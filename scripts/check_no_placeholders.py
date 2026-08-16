#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Placeholder gate for rendered static pages.

Scans rendered HTML fragments (produced by render_static_pages.py) for the
"[…]"/radman-placeholder markers that indicate an unresolved owner-fill-later
token. Exits non-zero if any are found so the staging runner can refuse to
apply until content is complete.

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

MARKERS = ("[…]", "radman-placeholder")  # literal owner placeholder and the CSS class


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
        # The renderer leaves either the literal "…" placeholder span or the
        # radman-placeholder CSS class on unresolved tokens.
        if "…" in text or "radman-placeholder" in text:
            offenders.append(html.name)

    if offenders:
        print("[FAIL] Placeholder markers found in rendered HTML:", file=sys.stderr)
        for name in offenders:
            print(f"  - {name}", file=sys.stderr)
        return 2

    print(f"[OK] No placeholder markers in {build_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
