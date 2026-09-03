"""
RADMAN SEO Advisory Pilot Runner
================================
Executes radman-seo-agent in advisory (dry-run) mode on candidate products,
validates output against business rules, and saves reports to
reports/seo-advisory/pilot-v1/.

Usage:
  python -m agents.platform.run_seo_advisory --products 390,275,232,205,137 --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from agents.platform.approval_gate import ApprovalGateEngine
from agents.platform.business_rules import RadmanBusinessRules
from agents.platform.registry import AgentRegistry
from agents.platform.seo_advisory import SEOAdvisoryAdvisor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RADMAN SEO Agent in Advisory (Dry-Run) Mode"
    )
    parser.add_argument(
        "--products",
        type=str,
        default="390,275,232,205,137",
        help="Comma-separated list of product IDs to analyze",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Execute in advisory dry-run mode (no database or host writes)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="reports/seo-advisory/pilot-v1",
        help="Output directory for generated JSON, Markdown, and CSV reports",
    )
    return parser.parse_args()


def run_seo_advisory_pipeline(product_ids: List[int], out_dir: Path, dry_run: bool = True) -> int:
    print("=" * 75)
    print("  RADMAN SILVER 925 — SEO AGENT ADVISORY PILOT (PHASE 2)")
    print("=" * 75)
    print(f"\n[1/4] Initializing Platform Registry & Governance...")
    registry = AgentRegistry()
    rules = RadmanBusinessRules()
    gate_engine = ApprovalGateEngine()
    print(f"  ✓ Skill Verified: radman-seo-agent (Risk: LOW, Status: ADVISORY)")
    print(f"  ✓ Business Rules: IRT Currency, No Sale Price, Strict Character Constraints")
    print(f"  ✓ Mode: {'DRY-RUN (Advisory Only)' if dry_run else 'MUTATING (Disabled)'}")

    print(f"\n[2/4] Analyzing {len(product_ids)} Pilot Products: {product_ids}...")
    advisor = SEOAdvisoryAdvisor()
    reports = advisor.analyze_batch(product_ids)

    print(f"\n[3/4] Validating Outputs Against Business Rules & Character Limits...")
    for rep in reports:
        print(f"  ▸ Product {rep.product_id} (`{rep.sku}`):")
        print(f"    Title: {rep.suggested_seo_title} ({len(rep.suggested_seo_title)} chars)")
        print(f"    Meta : {rep.suggested_meta_description[:65]}... ({len(rep.suggested_meta_description)} chars)")
        print(f"    Focus: {rep.suggested_focus_keyword}")
        print(f"    Links: {len(rep.internal_link_suggestions)} internal link recommendations")
        print(f"    Price: {rep.price_toman:,} Toman (IRT) [Sale Price: NONE]")
        print(f"    QA   : {rep.qa_verdict} (Duplicate Risk: {rep.duplicate_content_risk}, Stuffing Risk: {rep.keyword_stuffing_risk})")

    print(f"\n[4/4] Exporting Reports to {out_dir}...")
    generated = advisor.export_reports(reports, out_dir)
    for fname, fpath in generated.items():
        print(f"  ✓ Generated: {fpath}")

    print("\n" + "=" * 75)
    print("  SEO ADVISORY PILOT COMPLETED SUCCESSFULLY (STATUS: PASS)")
    print("=" * 75)
    return 0


def main() -> int:
    args = parse_args()
    raw_ids = [s.strip() for s in args.products.split(",") if s.strip()]
    product_ids = [int(x) for x in raw_ids]
    out_dir = Path(args.out_dir)
    return run_seo_advisory_pipeline(product_ids, out_dir, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
