#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Placeholder gate for rendered static pages.

Scans rendered HTML fragments (produced by render_static_pages.py) for
unresolved owner-fill-later markers and exits non-zero if any are found so
the staging runner can refuse to apply until content is complete.

A placeholder FAILS the gate if any of the following are present:
  * The literal bracketed-ellipsis sentinel "[...]" (open-bracket, U+2026
    HORIZONTAL ELLIPSIS, close-bracket) anywhere in the HTML.
  * The CSS class "radman-placeholder" which the renderer wraps around any
    unresolved [owner-fill] token.

A normal/standalone ellipsis character "..." (U+2026) used in Persian prose
OUTSIDE brackets is perfectly valid content and DOES PASS the gate.

Usage:
    python3 scripts/check_no_placeholders.py <build-dir>

Exit codes:
    0  clean — no placeholder markers
    2  one or more placeholders found
    3  usage / bad path
"""
from __future__ import annotations

import pathlib
import sys

# Fail patterns. Order matters: we look for the bracketed sentinel "[...]"
# explicitly, NOT for a bare ellipsis character. The CSS class
# "radman-placeholder" is emitted by the renderer for every unresolved
# [owner-fill] token including the literal "[...]" sentinel.
FAIL_MARKERS = (
    "[\u2026]",        # "[...]" — bracketed-ellipsis owner-fill-later sentinel
    "radman-placeholder",  # CSS class on placeholder spans
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_no_placeholders.py <build-dir>", file=sys.stderr)
        return 3
    build_dir = pathlib.Path(argv[1]).resolve()
    if not build_dir.is_dir():
        print(f"[FATAL] build dir not found: {build_dir}", file=sys.stderr)
        return 3

    offenders: list[str] = []
    for html in sorted(build_dir.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        for marker in FAIL_MARKERS:
            if marker in text:
                offenders.append(f"{html.name} (matched: {marker!r})")
                break

    if offenders:
        print("[FAIL] Placeholder markers found in rendered HTML:", file=sys.stderr)
        for name in offenders:
            print(f"  - {name}", file=sys.stderr)
        print(
            "\n[HINT] Normal ellipsis '\\u2026' in Persian prose is fine; "
            "only bracketed '[...]' tokens and radman-placeholder spans fail.",
            file=sys.stderr,
        )
        return 2

    print(f"[OK] No placeholder markers in {build_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
