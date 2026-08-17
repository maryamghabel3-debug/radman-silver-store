#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Static Pages Renderer
==========================================
Reads approved Persian Markdown sources under ``content/static-pages/`` and
renders the public-only page body into safe HTML fragments.

* Python standard library only (no pip dependencies).
* Extracts content strictly between the ``## Content`` heading and the first
  internal section heading (``## Trust Notes``, ``## Owner Fill Later``,
  ``## Internal Link Suggestions``, ``## SEO``, ``## Page Purpose``).
* Converts a safe, reviewed subset of Markdown into HTML:
    - ATX headings (h2, h3, h4)
    - paragraphs
    - unordered and ordered lists (single level; nested lists flattened)
    - bold / strong emphasis (``**text**``)
    - inline links (``[text](url)`` — URL must be http(s) or path-absolute)
* Refuses to emit owner checklists, SEO planning notes, or unresolved
  bracketed placeholders (``[owner-fill]`` or the literal ``[...]`` sentinel),
  which are replaced with a neutral ``<span class="radman-placeholder">``
  marker so reviewers can spot them. A normal Persian ellipsis "…" in prose
  is NOT treated as a placeholder and is rendered as-is.
* Writes rendered HTML fragments into a private build directory.
* Fails loudly if any source file or ``## Content`` section is missing.

This script intentionally does NOT touch WordPress. It is consumed by
``scripts/radman_branding_and_content_import.sh`` / ``scripts/radman_stage_apply.sh``
which perform idempotent ``wp post update`` / ``wp post create`` operations
under staging guards.

Usage (plan / render only):
    python3 scripts/render_static_pages.py \
        --repo-root . \
        --build-dir /tmp/radman-render-<timestamp>

Exit codes:
    0  all 11 pages rendered successfully
    2  user/configuration error (missing source, missing Content section, ...)
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple


# -----------------------------------------------------------------------------
# Official slug registry (must stay in sync with docs/STATIC-PAGES-REGISTRY.md)
# -----------------------------------------------------------------------------
OFFICIAL_PAGES: Tuple[Tuple[str, str, str], ...] = (
    # (slug,              persian_title,                 source_markdown)
    ("about-us",              "درباره رادمان",            "about-us.md"),
    ("contact-us",            "تماس با ما",               "contact-us.md"),
    ("faq",                   "سؤالات متداول",            "faq.md"),
    ("shipping",              "روش‌های ارسال",            "shipping-policy.md"),
    ("returns",               "شرایط بازگشت کالا",        "returns-policy.md"),
    ("privacy-policy-radman", "حریم خصوصی",              "privacy-policy.md"),
    ("terms",                 "قوانین و مقررات",          "terms-of-purchase.md"),
    ("ring-size-guide",       "راهنمای سایز انگشتر",      "ring-size-guide.md"),
    ("silver-care",           "راهنمای نگهداری نقره",     "silver-care-guide.md"),
    ("silver-925-authenticity", "اصالت نقره ۹۲۵",         "silver-925-authenticity.md"),
    ("gemstones",             "راهنمای سنگ‌های زینتی",    "gemstones-guide.md"),
)

INTERNAL_SECTION_HEADINGS: Tuple[str, ...] = (
    "trust notes",
    "owner fill later",
    "internal link suggestions",
    "seo",
    "page purpose",
)

# Placeholder pattern: bracketed owner-fill tokens like [شماره تماس] or the
# literal bracketed ellipsis "[...]" (U+2026 HORIZONTAL ELLIPSIS between brackets).
# We EXCLUDE markdown links ("](" immediately after the closing bracket) so that
# in-page links like [راهنمای سایز](/ring-size-guide) are never mistaken for
# placeholders. A normal/standalone ellipsis "..." in Persian prose is NOT a
# placeholder and is intentionally left untouched.
PLACEHOLDER_PATTERN = re.compile(r"\[([^\]\n]{1,80})\](?!\()")
HEADING_PATTERN = re.compile(r"^(#{2,4})\s+(.+?)\s*#*\s*$")
UL_BULLET_PATTERN = re.compile(r"^\s*[-*+]\s+(.*)$")
OL_BULLET_PATTERN = re.compile(r"^\s*\d+[.)]\s+(.*)$")

BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")
# Link text may contain Persian (non-ASCII); allow any non-] character.
LINK_PATTERN = re.compile(r"\[([^\]]{1,200})\]\(([^)\s<>\"']{1,500})\)", re.UNICODE)


class RenderError(Exception):
    """Raised when rendering cannot proceed safely."""


@dataclass(frozen=True)
class RenderResult:
    slug: str
    title: str
    source_path: Path
    output_path: Path
    char_count: int
    has_placeholders: bool


# -----------------------------------------------------------------------------
# Markdown extraction
# -----------------------------------------------------------------------------
def extract_public_body(markdown_text: str, source_label: str) -> str:
    """Return only the text inside the public ``## Content`` section."""
    lines = markdown_text.splitlines()
    content_start: int | None = None
    content_end: int | None = None

    for i, raw_line in enumerate(lines):
        line = raw_line.strip().lower()
        # Match "## Content" heading (allow trailing colons / comments)
        if line.startswith("## ") and "content" in line and not line.startswith("###"):
            if content_start is not None:
                raise RenderError(
                    f"{source_label}: duplicate '## Content' heading found; aborting."
                )
            content_start = i + 1
            continue
        if content_start is not None and line.startswith("## "):
            heading_name = line[3:].strip().rstrip(":").lower()
            if any(h in heading_name for h in INTERNAL_SECTION_HEADINGS):
                content_end = i
                break

    if content_start is None:
        raise RenderError(
            f"{source_label}: required '## Content' section not found. "
            "Every static page must contain a ## Content block."
        )

    if content_end is None:
        content_end = len(lines)

    body_lines = lines[content_start:content_end]
    # strip leading/trailing blank lines
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    if not body_lines:
        raise RenderError(f"{source_label}: '## Content' section is empty.")

    return "\n".join(body_lines)


# -----------------------------------------------------------------------------
# Inline formatting (XSS-safe)
# -----------------------------------------------------------------------------
def render_inline(text: str) -> str:
    """Render inline bold and links; escape everything else.

    Processing order matters here:
      1. Stash Markdown links [text](url) FIRST so their bracket syntax is
         never examined by the placeholder regex (defense-in-depth beyond
         the negative lookahead for a following open-paren in PLACEHOLDER_PATTERN).
      2. Stash bold **text** next.
      3. HTML-escape the remaining plain text.
      4. Replace any unresolved [owner-fill] or literal "[...]" sentinel in
         the escaped plain text with a neutral <span class="radman-placeholder">
         marker. A normal/standalone ellipsis "..." (U+2026) used in Persian
         prose is left alone and passes through as-is; it is NOT a placeholder.
      5. Restore the stashed links/bold tokens.
    """
    tokens: List[str] = []

    def _stash(s: str) -> str:
        tokens.append(s)
        return f"\x00TOK{len(tokens)-1}\x00"

    def _link_sub(m: re.Match[str]) -> str:
        label, url = m.group(1), m.group(2)
        safe_url = html.escape(url, quote=True)
        # Only allow safe URL schemes.
        if not (safe_url.startswith("/") or safe_url.startswith("http://") or safe_url.startswith("https://") or safe_url.startswith("mailto:")):
            safe_url = "#blocked"
        return _stash(f'<a href="{safe_url}">{html.escape(label)}</a>')

    def _bold_sub(m: re.Match[str]) -> str:
        return _stash(f"<strong>{html.escape(m.group(1))}</strong>")

    out = text
    out = LINK_PATTERN.sub(_link_sub, out)
    out = BOLD_PATTERN.sub(_bold_sub, out)
    out = html.escape(out, quote=False)

    # Replace unresolved [owner-fill] / "[...]" sentinels in the remaining
    # plain (escaped) text with a neutral placeholder span.
    def _placeholder_sub(match: re.Match[str]) -> str:
        ph = html.escape(match.group(0))
        return f'<span class="radman-placeholder" data-placeholder="{ph}">[…]</span>'

    out = PLACEHOLDER_PATTERN.sub(_placeholder_sub, out)

    for i, tok in enumerate(tokens):
        out = out.replace(f"\x00TOK{i}\x00", tok)
    return out


# -----------------------------------------------------------------------------
# Block rendering (lists, paragraphs, headings)
# -----------------------------------------------------------------------------
def _flush_paragraph(buf: List[str]) -> str:
    if not buf:
        return ""
    text = " ".join(s.strip() for s in buf if s.strip())
    buf.clear()
    if not text:
        return ""
    return f"<p>{render_inline(text)}</p>"


def _list_item(line: str, ordered: bool) -> str:
    if ordered:
        m = OL_BULLET_PATTERN.match(line)
    else:
        m = UL_BULLET_PATTERN.match(line)
    if not m:
        return ""
    return f"<li>{render_inline(m.group(1).strip())}</li>"


def render_markdown_to_html(public_body: str, source_label: str) -> Tuple[str, bool]:
    """Render extracted body Markdown into a safe HTML fragment.

    Returns a tuple of (html_string, has_placeholders_flag).
    """
    out: List[str] = []
    para: List[str] = []
    list_type: str | None = None  # 'ul' | 'ol' | None
    list_items: List[str] = []
    has_placeholders = False

    def _close_list() -> None:
        nonlocal list_type, list_items
        if list_type is None:
            return
        tag = list_type
        out.append(f"<{tag}>")
        out.extend(list_items)
        out.append(f"</{tag}>")
        list_type = None
        list_items = []

    for raw_line in public_body.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        # Detect horizontal rules: "---"
        if stripped in {"---", "***", "___"}:
            _close_list()
            out.append(_flush_paragraph(para))
            out.append("<hr />")
            continue

        # Headings
        hm = HEADING_PATTERN.match(stripped)
        if hm:
            _close_list()
            out.append(_flush_paragraph(para))
            level = len(hm.group(1))  # 2..4
            if level > 4:
                level = 4
            out.append(f"<h{level}>{render_inline(hm.group(2))}</h{level}>")
            continue

        # Unordered list line?
        ul_m = UL_BULLET_PATTERN.match(line)
        ol_m = OL_BULLET_PATTERN.match(line)
        if ul_m or ol_m:
            out.append(_flush_paragraph(para))
            ordered = bool(ol_m)
            wanted = "ol" if ordered else "ul"
            if list_type != wanted:
                _close_list()
                list_type = wanted
            item = _list_item(line, ordered)
            if item:
                list_items.append(item)
                if "radman-placeholder" in item:
                    has_placeholders = True
            continue

        # Table line — skip pipe tables (not allowed in static content).
        if stripped.startswith("|") and stripped.endswith("|"):
            # Render as pre/mono to avoid broken markup; reviewers will replace.
            _close_list()
            out.append(_flush_paragraph(para))
            out.append(f"<pre><code>{html.escape(stripped)}</code></pre>")
            continue

        # Blank line closes paragraph / list
        if not stripped:
            _close_list()
            out.append(_flush_paragraph(para))
            continue

        # Continuation line for current paragraph (or start a new one)
        if list_type is not None:
            # Treat continuation text inside a list as appended to the last li.
            if list_items:
                last = list_items[-1]
                # close li, append continuation
                last = last[:len("</li>") * -1] if last.endswith("</li>") else last
                last += " " + render_inline(stripped) + "</li>"
                list_items[-1] = last
            continue

        para.append(stripped)

    _close_list()
    out.append(_flush_paragraph(para))

    html_out = "\n".join(x for x in out if x).strip()
    # A page contains placeholders ONLY if the renderer emitted a
    # radman-placeholder span (unresolved [owner-fill-later] token).
    # Normal/standalone ellipsis "..." in Persian prose is NOT a placeholder.
    if "radman-placeholder" in html_out:
        has_placeholders = True
    return html_out, has_placeholders


# -----------------------------------------------------------------------------
# Orchestration
# -----------------------------------------------------------------------------
def render_one(
    slug: str,
    title: str,
    source_file: Path,
    output_dir: Path,
) -> RenderResult:
    if not source_file.is_file():
        raise RenderError(f"Missing source file for slug '{slug}': {source_file}")
    md_text = source_file.read_text(encoding="utf-8")
    public_body = extract_public_body(md_text, source_file.name)
    html_body, has_placeholder = render_markdown_to_html(public_body, source_file.name)
    if not html_body:
        raise RenderError(f"Rendered body is empty for slug '{slug}'.")

    output_dir.mkdir(parents=True, exist_ok=True)
    # Rendered files are keyed by the official WordPress slug (not source filename).
    out_path = output_dir / f"{slug}.html"
    # Wrap in a semantic article block so the deployer can push into the page.
    wrapped = textwrap.dedent(
        f"""\
        <!-- AUTO-RENDERED from {source_file.name} — DO NOT EDIT IN WORDPRESS DIRECTLY -->
        <article id="radman-page-{html.escape(slug)}" class="radman-static-content">
        {html_body}
        </article>
        """
    )
    out_path.write_text(wrapped, encoding="utf-8")
    return RenderResult(
        slug=slug,
        title=title,
        source_path=source_file,
        output_path=out_path,
        char_count=len(wrapped),
        has_placeholders=has_placeholder,
    )


def render_all(repo_root: Path, build_dir: Path) -> List[RenderResult]:
    content_dir = repo_root / "content" / "static-pages"
    if not content_dir.is_dir():
        raise RenderError(f"content/static-pages/ not found under {repo_root}")

    results: List[RenderResult] = []
    for slug, title, md_name in OFFICIAL_PAGES:
        src = content_dir / md_name
        results.append(render_one(slug, title, src, build_dir))
    return results


def format_plan_table(results: Iterable[RenderResult]) -> str:
    headers = ("slug", "title", "source", "output bytes", "placeholders")
    rows = [
        (
            r.slug,
            r.title,
            str(r.source_path.relative_to(r.source_path.parents[2])),
            str(r.output_path.stat().st_size),
            "YES" if r.has_placeholders else "no",
        )
        for r in results
    ]
    widths = [max(len(str(row[i])) for row in (headers, *rows)) for i in range(len(headers))]
    line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * w for w in widths)
    body = "\n".join(
        " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)) for row in rows
    )
    return f"{line}\n{sep}\n{body}"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render RADMAN static-page Markdown into safe HTML fragments.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root (default: cwd)")
    parser.add_argument(
        "--build-dir",
        default=None,
        help="Directory to write rendered HTML fragments. Default: /tmp/radman-render-<ts>",
    )
    parser.add_argument(
        "--strict-no-placeholders",
        action="store_true",
        help="Fail if any [placeholder] tokens remain in the rendered output.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if args.build_dir:
        build_dir = Path(args.build_dir)
    else:
        build_dir = Path("/tmp") / f"radman-render-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    build_dir = build_dir.resolve()
    build_dir.mkdir(parents=True, exist_ok=True)

    try:
        results = render_all(repo_root, build_dir)
    except RenderError as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        return 2

    print(f"[OK] Rendered {len(results)} static pages to {build_dir}")
    print(format_plan_table(results))

    any_placeholder = any(r.has_placeholders for r in results)
    if any_placeholder:
        print(
            "\n[NOTE] Pages marked 'YES' in placeholders column still contain "
            "owner-fill-later tokens ([...] / bracketed text) rendered as "
            "<span class=\"radman-placeholder\">. The deploy runner refuses to "
            "apply when --strict-no-placeholders is set; plan mode allows them "
            "for review. A normal/standalone ellipsis '…' in Persian prose is "
            "NOT a placeholder and does not block rendering.",
            file=sys.stderr,
        )
        if args.strict_no_placeholders:
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
