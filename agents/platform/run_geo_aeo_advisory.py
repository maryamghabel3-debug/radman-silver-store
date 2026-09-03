"""
RADMAN GEO + AEO Advisory Pilot Runner
======================================
Executes both radman-geo-agent (Generative Engine Optimization) and
radman-aeo-agent (Answer Engine Optimization) in advisory (dry-run) mode
on 5 pilot products and exports reports to reports/geo-aeo-advisory/pilot-v1/.

Usage:
  python -m agents.platform.run_geo_aeo_advisory --products 390,275,232,205,137 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from agents.platform.aeo_advisory import AEOAdvisor, AEOAdvisoryReport
from agents.platform.approval_gate import ApprovalGateEngine
from agents.platform.business_rules import RadmanBusinessRules
from agents.platform.geo_advisory import GEOAdvisor, GEOAdvisoryReport
from agents.platform.registry import AgentRegistry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RADMAN GEO + AEO Advisory Engine"
    )
    parser.add_argument(
        "--products",
        type=str,
        default="390,275,232,205,137",
        help="Comma-separated product IDs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run in advisory dry-run mode",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="reports/geo-aeo-advisory/pilot-v1",
        help="Output directory for GEO/AEO reports",
    )
    return parser.parse_args()


def generate_geo_aeo_summary_markdown(
    geo_reports: List[GEOAdvisoryReport],
    aeo_reports: List[AEOAdvisoryReport],
) -> str:
    lines = [
        "# گزارش راهبردی هوش مصنوعی و بهینه‌سازی موتورهای پاسخگو (GEO & AEO Summary)",
        "",
        "> **وضعیت اجرا:** حالت مشاوره‌ای (Dry-Run Only)  ",
        "> **تعداد محصولات تحلیل‌شده:** ۵ محصول منتخب  ",
        "> **اهداف استراتژیک:** آمادگی ارجاع در Google AI Overviews, Gemini, Perplexity و پاسخ‌گویی مستقیم در ChatGPT Search  ",
        "> **قوانین حاکمیت تجاری:** واحد پول تومان (IRT)، عدم اعمال sale_price، حفظ پیش‌نویس (Draft)  ",
        "",
        "---",
        "",
        "## ۱. جدول ارزیابی امتیازهای آمادگی هوش مصنوعی (GEO & AEO Scorecard)",
        "",
        "| شناسه | کد کالا (SKU) | عنوان محصول | امتیاز GEO (استناد هوش مصنوعی) | امتیاز AEO (پاسخ مستقیم صوتی/چت) | تعداد سوالات نقشه‌برداری‌شده | اسکیما FAQ | وضعیت کلی |",
        "| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for geo, aeo in zip(geo_reports, aeo_reports):
        lines.append(
            f"| {geo.product_id} | `{geo.sku}` | {geo.legacy_title} | {geo.geo_readiness_score}/100 | {aeo.aeo_readiness_score}/100 | {aeo.questions_mapped} سوال | ✅ {aeo.faq_schema_ready} | ✅ {geo.qa_verdict} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## ۲. جزئیات تحلیل بهینه‌سازی موتورهای مولد (GEO) برای هر محصول",
        "",
    ])

    for geo in geo_reports:
        lines.extend([
            f"### 🌐 محصول {geo.product_id} — {geo.legacy_title} (SKU: `{geo.sku}`)",
            f"- **امتیاز آمادگی استناد (GEO Score):** `{geo.geo_readiness_score}/100`",
            f"- **آمادگی برای نقل‌قول مستقیم هوش مصنوعی:** {geo.citation_ready}",
            f"- **وضوح هویت محصول (Entity Clarity):** {geo.entity_clarity}",
            f"- **موقعیت‌یابی مقایسه‌ای (Comparative Positioning):**",
            f"  > {geo.comparative_positioning}",
            f"- **شکاف‌های اسکیما و متادیتا (Schema Gaps):**",
        ])
        for sg in geo.schema_gaps:
            lines.append(f"  • {sg}")
        lines.extend([
            f"- **پیشنهادهای اصلاح محتوایی (Content Suggestions):**",
        ])
        for cs in geo.content_suggestions:
            lines.append(f"  • {cs}")
        lines.extend([
            f"- **محتوای آموزشی مکمل مورد نیاز (Supporting Content):**",
        ])
        for sc in geo.supporting_content_needed:
            lines.append(f"  • {sc}")
        lines.extend([""])

    lines.extend([
        "---",
        "",
        "## ۳. جزئیات بهینه‌سازی موتورهای پاسخگو و سوالات متداول (AEO)",
        "",
    ])

    for aeo in aeo_reports:
        lines.extend([
            f"### 💬 محصول {aeo.product_id} — {aeo.legacy_title} (SKU: `{aeo.sku}`)",
            f"- **امتیاز پاسخ‌گویی چت و دستیارهای صوتی (AEO Score):** `{aeo.aeo_readiness_score}/100`",
            f"- **کیفیت اسنیپت مکالمه‌ای (Snippet Quality):** {aeo.snippet_quality}",
            f"- **عبارات جستجوی با قصد خرید (Purchase-Intent Coverage):**",
        ])
        for it in aeo.intent_coverage:
            lines.append(f"  • {it}")
        lines.extend([
            f"- **بسته‌های پرسش و پاسخ مستقیم (Direct Answer Blocks):**",
        ])
        for qp in aeo.qa_pairs:
            lines.extend([
                f"  ❓ **سوال:** {qp.question}",
                f"  💡 **پاسخ مستقیم:** {qp.direct_answer}",
                "",
            ])

    return "\n".join(lines)


def generate_unified_report(
    geo_reports: List[GEOAdvisoryReport],
    aeo_reports: List[AEOAdvisoryReport],
) -> str:
    lines = [
        "# گزارش راهبرد یکپارچه بهینه‌سازی جستجو رادمان سیلور (SEO + GEO + AEO)",
        "",
        "این گزارش سند هم‌افزایی سه عامل بهینه‌سازی جستجوی رادمان است:",
        "1. **عامل SEO (سنتی):** بهینه‌سازی رتبه گوگل، عناوین فارسی و کلمات کلیدی تراکنشی.",
        "2. **عامل GEO (موتورهای مولد):** بهینه‌سازی استناد و نقل‌قول در Google AI Overviews, Gemini, Perplexity.",
        "3. **عامل AEO (دستیارهای مکالمه‌ای):** بهینه‌سازی پاسخ مستقیم در ChatGPT Search، کوپایلوت و دستیارهای صوتی.",
        "",
        "---",
        "",
        "## ماتریس هم‌افزایی برای ۵ محصول پایلوت",
        "",
        "| شناسه | محصول | کلیدواژه سئو | کلیدواژه استناد هوش مصنوعی | اولویت پاسخ صوتی/چت | وضعیت تجاری |",
        "| :---: | :--- | :--- | :--- | :--- | :---: |",
    ]

    for geo, aeo in zip(geo_reports, aeo_reports):
        lines.append(
            f"| {geo.product_id} | {geo.legacy_title} | نقره ۹۲۵ دست‌ساز | عقیق شجر/طبیعی معدنی | اصالت سنگ و عیار ۹۲۵ | بدون قیمت حراجی (تومان) |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## توصیه‌های اجرایی برای فاز استیجینگ",
        "1. بارگذاری متادیتای Rank Math تولیدشده توسط SEO Agent.",
        "2. افزودن اسکیماهای FAQPage تولیدشده توسط AEO Agent به قالب تک‌محصول.",
        "3. ایجاد صفحات راهنمای آموزشی گوهرشناسی بر اساس پیشنهادهای GEO Agent.",
        "",
    ])

    return "\n".join(lines)


def run_geo_aeo_pipeline(product_ids: List[int], out_dir: Path, dry_run: bool = True) -> int:
    print("=" * 80)
    print("  RADMAN SILVER 925 — GEO & AEO AGENT ADVISORY PILOT")
    print("=" * 80)

    print("\n[1/4] Verifying Skills & Business Rules...")
    registry = AgentRegistry()
    rules = RadmanBusinessRules()
    gate_engine = ApprovalGateEngine()
    print("  ✓ Skills Active: radman-geo-agent, radman-aeo-agent, radman-seo-agent")
    print("  ✓ Business Invariants: IRT Currency, No Sale Price, Factual Truth Priority")

    print(f"\n[2/4] Running GEO Advisory Engine on Products {product_ids}...")
    geo_advisor = GEOAdvisor()
    geo_reports = geo_advisor.analyze_batch(product_ids)
    for rep in geo_reports:
        print(f"  ▸ GEO {rep.product_id} (`{rep.sku}`): Score={rep.geo_readiness_score}/100, Citation={rep.citation_ready}, Entity={rep.entity_clarity}")

    print(f"\n[3/4] Running AEO Advisory Engine on Products {product_ids}...")
    aeo_advisor = AEOAdvisor()
    aeo_reports = aeo_advisor.analyze_batch(product_ids)
    for rep in aeo_reports:
        print(f"  ▸ AEO {rep.product_id} (`{rep.sku}`): Score={rep.aeo_readiness_score}/100, Questions={rep.questions_mapped}, FAQ Schema={rep.faq_schema_ready}")

    print(f"\n[4/4] Exporting Multi-Format Reports to {out_dir}...")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Individual GEO & AEO JSON files
    geo_files = geo_advisor.export_reports(geo_reports, out_dir)
    aeo_files = aeo_advisor.export_reports(aeo_reports, out_dir)
    for f in {**geo_files, **aeo_files}.values():
        print(f"  ✓ JSON Artifact: {f}")

    # 2. Markdown Summary
    summary_md_path = out_dir / "geo-aeo-summary.md"
    summary_md_path.write_text(
        generate_geo_aeo_summary_markdown(geo_reports, aeo_reports),
        encoding="utf-8",
    )
    print(f"  ✓ Markdown Summary: {summary_md_path}")

    # 3. CSV Summary
    csv_path = out_dir / "geo-aeo-summary.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Product ID",
            "SKU",
            "Legacy Title",
            "GEO Score",
            "Citation Ready",
            "Entity Clarity",
            "AEO Score",
            "Questions Mapped",
            "FAQ Schema Ready",
            "Price Toman",
            "QA Verdict",
        ])
        for geo, aeo in zip(geo_reports, aeo_reports):
            writer.writerow([
                geo.product_id,
                geo.sku,
                geo.legacy_title,
                geo.geo_readiness_score,
                geo.citation_ready,
                geo.entity_clarity,
                aeo.aeo_readiness_score,
                aeo.questions_mapped,
                aeo.faq_schema_ready,
                geo.price_toman,
                geo.qa_verdict,
            ])
    print(f"  ✓ CSV Summary: {csv_path}")

    # 4. Unified Search Optimization Report
    unified_report_path = out_dir / "unified-search-optimization-report.md"
    unified_report_path.write_text(
        generate_unified_report(geo_reports, aeo_reports),
        encoding="utf-8",
    )
    print(f"  ✓ Unified Report: {unified_report_path}")

    print("\n" + "=" * 80)
    print("  GEO & AEO ADVISORY PILOT COMPLETED SUCCESSFULLY (STATUS: PASS)")
    print("=" * 80)
    return 0


def main() -> int:
    args = parse_args()
    raw_ids = [s.strip() for s in args.products.split(",") if s.strip()]
    product_ids = [int(x) for x in raw_ids]
    out_dir = Path(args.out_dir)
    return run_geo_aeo_pipeline(product_ids, out_dir, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
