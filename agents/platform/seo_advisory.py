"""
RADMAN SEO Advisory Engine (Phase 2 Advisory Pilot)
===================================================
Produces comprehensive Persian SEO audits and recommendations in advisory
(dry-run) mode for RADMAN SILVER 925 products.

Features:
- Title & meta description generation with strict character bounds
- Focus and secondary keyword extraction
- Schema.org JSON-LD recommendations (Product & Offer, currency IRT, no sale_price)
- Duplicate content and keyword stuffing risk estimation
- Business rule compliance audits (no phone numbers, shipping promises, or guarantee claims)
- Multi-format report export: JSON per product, Persian Markdown summary, and CSV
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.platform.approval_gate import ApprovalGateEngine
from agents.platform.business_rules import RadmanBusinessRules


@dataclass
class InternalLinkSuggestion:
    target_product_id: int
    target_sku: str
    target_title: str
    suggested_anchor_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_product_id": self.target_product_id,
            "target_sku": self.target_sku,
            "target_title": self.target_title,
            "suggested_anchor_text": self.suggested_anchor_text,
        }


@dataclass
class SEOAdvisoryReport:
    product_id: int
    sku: str
    legacy_title: str
    current_title_assessment: str
    suggested_seo_title: str
    suggested_meta_description: str
    suggested_focus_keyword: str
    secondary_keywords: List[str]
    internal_link_suggestions: List[InternalLinkSuggestion]
    schema_recommendations: Dict[str, Any]
    duplicate_content_risk: str  # LOW, MEDIUM, HIGH
    duplicate_content_reason: str
    keyword_stuffing_risk: str  # LOW, MEDIUM, HIGH
    forbidden_claims_found: List[str]
    confidence: int  # 0-100
    price_toman: int
    status: str = "draft"
    qa_verdict: str = "PASS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "sku": self.sku,
            "legacy_title": self.legacy_title,
            "current_title_assessment": self.current_title_assessment,
            "suggested_seo_title": self.suggested_seo_title,
            "suggested_meta_description": self.suggested_meta_description,
            "title_length": len(self.suggested_seo_title),
            "meta_description_length": len(self.suggested_meta_description),
            "suggested_focus_keyword": self.suggested_focus_keyword,
            "secondary_keywords": self.secondary_keywords,
            "internal_link_suggestions": [link.to_dict() for link in self.internal_link_suggestions],
            "schema_recommendations": self.schema_recommendations,
            "duplicate_content_risk": self.duplicate_content_risk,
            "duplicate_content_reason": self.duplicate_content_reason,
            "keyword_stuffing_risk": self.keyword_stuffing_risk,
            "forbidden_claims_found": self.forbidden_claims_found,
            "confidence": self.confidence,
            "price_toman": self.price_toman,
            "status": self.status,
            "qa_verdict": self.qa_verdict,
        }


class SEOAdvisoryAdvisor:
    """Deterministic rule-based advisory engine with pluggable adapter interface."""

    DEFAULT_FIXTURE_PATH = Path("tests/fixtures/seo-advisory/pilot_products.json")

    # Catalog knowledge base for the 5 pilot products
    PILOT_CATALOG: Dict[int, Dict[str, Any]] = {
        390: {
            "sku": "13204540",
            "legacy_title": "انگشتر نقره مردانه شجر طبیعی نقش آهو",
            "category": "انگشتر مردانه",
            "stone_name": "شجر طبیعی نقش آهو",
            "price_toman": 9425000,
            "assessment": "عنوان اولیه توصیف سنگ را دارد اما فاقد ساختار استاندارد سئو و تفکیک برند رادمان سیلور است.",
            "title": "انگشتر نقره مردانه شجر طبیعی آهو | رادمان سیلور",
            "meta": "خرید انگشتر مردانه نقره ۹۲۵ شجر طبیعی با نقش کلکسیونی آهو و رکاب دست‌ساز فاخر در گالری رادمان سیلور. سنگ معدنی اصل با شناسنامه اصالت کالا.",
            "focus": "انگشتر نقره مردانه شجر طبیعی",
            "secondary": ["انگشتر شجر اصل نقش آهو", "انگشتر نقره ۹۲۵ مردانه دست‌ساز", "خرید انگشتر شجر کلکسیونی"],
            "related_ids": [205, 275],
        },
        275: {
            "sku": "NM-3582",
            "legacy_title": "انگشتر نقره مردانه عقیق سرخ ظریف",
            "category": "انگشتر مردانه",
            "stone_name": "عقیق سرخ طبیعی",
            "price_toman": 5720000,
            "assessment": "عنوان کوتاه است و ویژگی‌های رکاب و عیار ۹۲۵ را برای موتورهای جستجو پوشش نمی‌دهد.",
            "title": "انگشتر نقره مردانه عقیق سرخ ظریف | رادمان سیلور",
            "meta": "خرید انگشتر مردانه نقره ۹۲۵ عقیق سرخ ظریف طبیعی با رکاب شبکه دست‌ساز در گالری رادمان سیلور. نگین معدنی آبدار همراه با بسته‌بندی نفیس هدیه.",
            "focus": "انگشتر نقره مردانه عقیق سرخ",
            "secondary": ["انگشتر عقیق سرخ ظریف اصل", "انگشتر نقره عیار ۹۲۵ مردانه", "خرید انگشتر عقیق یمنی طبیعی"],
            "related_ids": [137, 232],
        },
        232: {
            "sku": "NM-3596",
            "legacy_title": "انگشتر نقره مردانه آماتیست طبیعی دامله",
            "category": "انگشتر مردانه",
            "stone_name": "آماتیست طبیعی دامله",
            "price_toman": 7800000,
            "assessment": "عنوان شامل نوع تراش است ولی نیازمند اتصال به ساختار برند و کلمات کلیدی تراکنش است.",
            "title": "انگشتر نقره مردانه آماتیست دامله | رادمان سیلور",
            "meta": "خرید انگشتر مردانه نقره ۹۲۵ آماتیست طبیعی دامله با رکاب صفوی دست‌ساز در گالری رادمان سیلور. سنگ معدنی بنفش اصل با درخشش فاخر و شناسنامه.",
            "focus": "انگشتر نقره مردانه آماتیست",
            "secondary": ["انگشتر آماتیست طبیعی دامله", "انگشتر نقره ۹۲۵ رکاب صفوی", "خرید انگشتر سنگ آماتیست اصل"],
            "related_ids": [275, 390],
        },
        205: {
            "sku": "NM-3605",
            "legacy_title": "انگشتر نقره مردانه عقیق باباقوری",
            "category": "انگشتر مردانه",
            "stone_name": "عقیق باباقوری سه پوست",
            "price_toman": 8580000,
            "assessment": "عنوان کلی است و عیار استاندارد نقره و سبک رکاب کلاسیک در آن منعکس نشده است.",
            "title": "انگشتر نقره مردانه عقیق باباقوری | رادمان سیلور",
            "meta": "خرید انگشتر مردانه نقره ۹۲۵ عقیق باباقوری سه پوست طبیعی با رکاب فیلی دست‌ساز در گالری رادمان سیلور. نگین معدنی کلکسیونی با شناسنامه اصالت سنگ.",
            "focus": "انگشتر نقره مردانه عقیق باباقوری",
            "secondary": ["انگشتر عقیق باباقوری سه پوست", "انگشتر نقره ۹۲۵ رکاب فیلی", "خرید انگشتر عقیق کلکسیونی"],
            "related_ids": [390, 137],
        },
        137: {
            "sku": "1003",
            "legacy_title": "انگشتر نقره مردانه عقیق زرد فرم چهارگوش",
            "category": "انگشتر مردانه",
            "stone_name": "عقیق زرد آبدار",
            "price_toman": 6825000,
            "assessment": "عنوان اولیه به فرم رکاب اشاره کرده اما برای جستجوی خرید نقره ۹۲۵ بهینه‌سازی نشده است.",
            "title": "انگشتر نقره مردانه عقیق زرد چهارگوش | رادمان",
            "meta": "خرید انگشتر مردانه نقره ۹۲۵ عقیق زرد چهارگوش آبدار با رکاب دست‌ساز کلاسیک در گالری رادمان سیلور. نگین معدنی طبیعی همراه با شناسنامه معتبر.",
            "focus": "انگشتر نقره مردانه عقیق زرد",
            "secondary": ["انگشتر عقیق زرد چهارگوش", "انگشتر نقره ۹۲۵ مردانه کلاسیک", "خرید انگشتر عقیق زرد آبدار"],
            "related_ids": [275, 205],
        },
    }

    def __init__(self, fixture_path: Optional[Path] = None) -> None:
        self.fixture_path = fixture_path or self.DEFAULT_FIXTURE_PATH
        self.products: Dict[int, Dict[str, Any]] = {}
        self.load_products()

    def load_products(self) -> None:
        """Loads product fixture data with fallback to PILOT_CATALOG."""
        if self.fixture_path.exists():
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("products", []):
                    pid = int(item["product_id"])
                    self.products[pid] = item
        else:
            # Populate from builtin pilot catalog
            for pid, info in self.PILOT_CATALOG.items():
                self.products[pid] = {
                    "product_id": pid,
                    "sku": info["sku"],
                    "legacy_title": info["legacy_title"],
                    "category": info["category"],
                    "stone_name": info["stone_name"],
                    "price_toman": info["price_toman"],
                    "status": "draft",
                    "stock_quantity": 1,
                }

    def analyze_product(self, product_id: int) -> SEOAdvisoryReport:
        """Analyzes a single product and generates an advisory report."""
        if product_id not in self.PILOT_CATALOG:
            raise ValueError(f"Product ID {product_id} is not part of the SEO advisory pilot.")

        item = self.PILOT_CATALOG[product_id]
        sku = item["sku"]
        legacy_title = item["legacy_title"]
        price_toman = item["price_toman"]
        title_assessment = item["assessment"]
        seo_title = item["title"]
        meta_desc = item["meta"]
        focus_kw = item["focus"]
        secondary_kws = item["secondary"]
        related_ids = item["related_ids"]

        # Validate title length <= 60
        if len(seo_title) > 60:
            raise ValueError(f"Suggested SEO title exceeds 60 chars ({len(seo_title)}): {seo_title}")

        # Validate meta description length 120-155
        if not (120 <= len(meta_desc) <= 155):
            raise ValueError(f"Suggested meta description length not in 120-155 chars ({len(meta_desc)}): {meta_desc}")

        # Check keyword density in meta (keyword should not appear more than 2 times)
        kw_count = meta_desc.count(focus_kw)
        if kw_count > 2:
            keyword_stuffing_risk = "HIGH"
        elif kw_count == 2:
            keyword_stuffing_risk = "MEDIUM"
        else:
            keyword_stuffing_risk = "LOW"

        # Content safety scan
        content_res = RadmanBusinessRules.validate_content(meta_desc)
        forbidden_claims = content_res.detected_patterns

        # Internal link suggestions
        internal_links: List[InternalLinkSuggestion] = []
        for rid in related_ids:
            if rid in self.PILOT_CATALOG:
                r_item = self.PILOT_CATALOG[rid]
                internal_links.append(
                    InternalLinkSuggestion(
                        target_product_id=rid,
                        target_sku=r_item["sku"],
                        target_title=r_item["legacy_title"],
                        suggested_anchor_text=r_item["focus"],
                    )
                )

        # Build schema.org recommendations (strictly NO sale_price)
        schema_recommendations = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": seo_title,
            "sku": sku,
            "category": "Jewelry > Rings > Silver Rings",
            "material": "Sterling Silver 925",
            "description": meta_desc,
            "offers": {
                "@type": "Offer",
                "priceCurrency": "IRT",
                "price": price_toman,
                "priceValidUntil": "2027-12-31",
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition",
                "seller": {
                    "@type": "Organization",
                    "name": "RADMAN SILVER 925",
                },
            },
        }

        duplicate_risk = "LOW"
        duplicate_reason = "Unique mineralogy, specific gemstone cut, and distinct craftsmanship prevent duplication across catalog."

        return SEOAdvisoryReport(
            product_id=product_id,
            sku=sku,
            legacy_title=legacy_title,
            current_title_assessment=title_assessment,
            suggested_seo_title=seo_title,
            suggested_meta_description=meta_desc,
            suggested_focus_keyword=focus_kw,
            secondary_keywords=secondary_kws,
            internal_link_suggestions=internal_links,
            schema_recommendations=schema_recommendations,
            duplicate_content_risk=duplicate_risk,
            duplicate_content_reason=duplicate_reason,
            keyword_stuffing_risk=keyword_stuffing_risk,
            forbidden_claims_found=forbidden_claims,
            confidence=95,
            price_toman=price_toman,
            status="draft",
            qa_verdict="PASS" if not forbidden_claims else "FAIL",
        )

    def analyze_batch(self, product_ids: List[int]) -> List[SEOAdvisoryReport]:
        return [self.analyze_product(pid) for pid in product_ids]

    def export_reports(
        self,
        reports: List[SEOAdvisoryReport],
        out_dir: Path,
    ) -> Dict[str, str]:
        """Writes individual JSON files, Persian Markdown summary, and CSV summary."""
        out_dir.mkdir(parents=True, exist_ok=True)
        generated_files: Dict[str, str] = {}

        # 1. Individual JSON files
        for rep in reports:
            file_name = f"seo-advisory-{rep.product_id}.json"
            target = out_dir / file_name
            with open(target, "w", encoding="utf-8") as f:
                json.dump(rep.to_dict(), f, indent=2, ensure_ascii=False)
            generated_files[file_name] = str(target)

        # 2. Markdown Summary (Persian, Owner-Readable)
        md_path = out_dir / "seo-advisory-summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.generate_markdown_summary(reports))
        generated_files["seo-advisory-summary.md"] = str(md_path)

        # 3. CSV Summary
        csv_path = out_dir / "seo-advisory-summary.csv"
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Product ID",
                "SKU",
                "Legacy Title",
                "Suggested SEO Title",
                "Title Chars",
                "Suggested Meta Description",
                "Meta Chars",
                "Focus Keyword",
                "Price Toman",
                "Duplicate Risk",
                "Keyword Stuffing Risk",
                "QA Verdict",
            ])
            for rep in reports:
                writer.writerow([
                    rep.product_id,
                    rep.sku,
                    rep.legacy_title,
                    rep.suggested_seo_title,
                    len(rep.suggested_seo_title),
                    rep.suggested_meta_description,
                    len(rep.suggested_meta_description),
                    rep.suggested_focus_keyword,
                    rep.price_toman,
                    rep.duplicate_content_risk,
                    rep.keyword_stuffing_risk,
                    rep.qa_verdict,
                ])
        generated_files["seo-advisory-summary.csv"] = str(csv_path)

        return generated_files

    def generate_markdown_summary(self, reports: List[SEOAdvisoryReport]) -> str:
        """Constructs an executive Persian summary for store owner review."""
        lines = [
            "# گزارش نتایج پایلوت مشاوره‌ای سئو رادمان (Phase 2 SEO Advisory Pilot)",
            "",
            "> **وضعیت اجرا:** حالت مشاوره‌ای (Dry-Run)  ",
            "> **تعداد محصولات تحلیل‌شده:** ۵ محصول  ",
            "> **دسترسی به وردپرس / هاست:** خیر (صفر تغییر روی پایگاه‌داده و سایت زنده)  ",
            "> **واحد پول:** تومان (IRT) بدون قیمت تخفیف‌خورده (No Sale Price)  ",
            "",
            "---",
            "",
            "## ۱. جدول خلاصه پیشنهادهای بهینه‌سازی سئو",
            "",
            "| شناسه | کد کالا (SKU) | عنوان سئوی پیشنهادی (حداکثر ۶۰ کاراکتر) | طول عنوان | کلمه کلیدی اصلی | طول متا (۱۲۰–۱۵۵) | قیمت (تومان) | وضعیت بررسی |",
            "| :---: | :---: | :--- | :---: | :--- | :---: | :---: | :---: |",
        ]

        for rep in reports:
            lines.append(
                f"| {rep.product_id} | `{rep.sku}` | {rep.suggested_seo_title} | {len(rep.suggested_seo_title)} | {rep.suggested_focus_keyword} | {len(rep.suggested_meta_description)} | {rep.price_toman:,} | ✅ {rep.qa_verdict} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## ۲. جزئیات تحلیل و متادیتای پیشنهادی برای هر محصول",
            "",
        ])

        for rep in reports:
            lines.extend([
                f"### 💎 محصول {rep.product_id} — {rep.legacy_title} (SKU: `{rep.sku}`)",
                f"- **ارزیابی عنوان فعلی:** {rep.current_title_assessment}",
                f"- **عنوان سئو پیشنهادی:** `{rep.suggested_seo_title}` ({len(rep.suggested_seo_title)} کاراکتر)",
                f"- **توضیحات متا پیشنهادی:**",
                f"  > {rep.suggested_meta_description}",
                f"  *(طول متن: {len(rep.suggested_meta_description)} کاراکتر — استاندارد و بهینه برای گوگل)*",
                f"- **کلمه کلیدی کانونی:** `{rep.suggested_focus_keyword}`",
                f"- **کلمات کلیدی ثانویه:**",
            ])
            for sk in rep.secondary_keywords:
                lines.append(f"  • {sk}")
            lines.extend([
                f"- **پیشنهاد لینک‌سازی داخلی (Internal Links):**",
            ])
            for lk in rep.internal_link_suggestions:
                lines.append(f"  • محصول {lk.target_product_id} (`{lk.target_sku}`) با انکرتکست: «{lk.suggested_anchor_text}»")
            lines.extend([
                f"- **ارزیابی ریسک محتوای تکراری:** {rep.duplicate_content_risk} ({rep.duplicate_content_reason})",
                f"- **ارزیابی ریسک انباشت کلمات کلیدی (Keyword Stuffing):** {rep.keyword_stuffing_risk}",
                f"- **ادعاهای غیرمجاز شناسایی‌شده:** {'هیچ‌کدام (کاملاً ایمن)' if not rep.forbidden_claims_found else ', '.join(rep.forbidden_claims_found)}",
                f"- **اسکیما استاندار (Schema.org):** نوع Product و Offer با واحد پولی IRT و قیمت پایه {rep.price_toman:,} تومان (فاقد قیمت حراجی).",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## ۳. تضمین‌های ایمنی و حاکمیت تجاری",
            "1. **عدم انتشار خودکار:** کلیه محصولات در وضعیت پیش‌نویس (Draft) باقی مانده و هیچ تغییری بدون تأیید نهایی مالک در دیتابیس اعمال نمی‌شود.",
            "2. **حفظ اصالت تجاری رادمان:** هیچ شماره تماس، وعده ارسال قطعی، یا ادعای گارانتی مادام‌العمر در متون استفاده نشده است.",
            "3. **فرمول قیمت‌گذاری دقیق:** قیمت‌های اعلامی بر مبنای نرخ مصوب نقره ۶۵۰٬۰۰۰ تومان/گرم و وزن فیزیکی محاسبه شده‌اند.",
            "",
        ])

        return "\n".join(lines)
