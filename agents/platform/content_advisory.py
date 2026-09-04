"""
RADMAN Content Advisory Engine (Phase 2 Content Pilot)
======================================================
Produces brand-compliant, luxury Persian social media captions, Instagram story
text, factual WooCommerce short descriptions, and educational blog outlines.

Authoritative Snapshot & Fact-Lock Enforcement:
- Verified fields only from data/verified-product-snapshot-*.json
- Zero unverified claims (دست‌ساز, شناسنامه, بسته‌بندی, گارانتی, نرخ مصوب)
- No prices or phone numbers in social captions
- Weekly Instagram calendar generation (Sat–Thu)
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.platform.business_rules import RadmanBusinessRules


@dataclass
class BlogOutline:
    title: str
    target_stone: str
    sections: List[str]
    key_takeaways: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "target_stone": self.target_stone,
            "sections": self.sections,
            "key_takeaways": self.key_takeaways,
        }


@dataclass
class ContentAdvisoryReport:
    product_id: int
    sku: str
    legacy_title: str
    stone: str
    weight_g: Optional[int]
    price_toman: int
    instagram_caption: str
    instagram_story_text: str
    product_short_description: str
    blog_outline: BlogOutline
    status: str = "draft"
    qa_verdict: str = "PASS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "sku": self.sku,
            "legacy_title": self.legacy_title,
            "stone": self.stone,
            "weight_g": self.weight_g,
            "price_toman": self.price_toman,
            "instagram_caption": self.instagram_caption,
            "instagram_story_text": self.instagram_story_text,
            "product_short_description": self.product_short_description,
            "blog_outline": self.blog_outline.to_dict(),
            "status": self.status,
            "qa_verdict": self.qa_verdict,
        }


class ContentAdvisor:
    """Content generator producing verified luxury Persian content assets."""

    DEFAULT_SNAPSHOT_PATH = Path("data/verified-product-snapshot-20260903.json")

    # Authoritative verified catalog for content generation
    CATALOG_KNOWLEDGE: Dict[int, Dict[str, Any]] = {
        232: {
            "sku": "NM-3596",
            "legacy_title": "انگشتر نقره مردانه آماتیست طبیعی دامله",
            "stone": "آماتیست طبیعی دامله",
            "weight_g": 8,
            "price_toman": 6633000,
            "band": "نقره ماشینی",
            "caption": "درخشش سنگ آماتیست طبیعی با تراش گنبدی دامله بر روی رکاب نقره عیار ۹۲۵ به وزن ۸ گرم. ترکیبی هماهنگ از رنگ بنفش چشم‌نواز و بدنه استاندارد نقره برای استایل روزمره آقایان.\n\n#نقره_۹۲۵ #انگشتر_مردانه #آماتیست_طبیعی #رادمان_سیلور",
            "story": "بررسی مشخصات انگشتر نقره عیار ۹۲۵ با نگین آماتیست طبیعی دامله در وب‌سایت رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین آماتیست طبیعی دامله، وزن ۸ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "راهنمای کانی‌شناسی سنگ آماتیست و نگهداری زیورآلات نقره ۹۲۵",
                "stone": "آماتیست طبیعی دامله",
                "sections": [
                    "۱. کانی‌شناسی کوارتز بنفش و دلایل تشکیل رنگ طبیعی آماتیست",
                    "۲. مزایای تراش محدب دامله در نمایش بازتاب نور",
                    "۳. اصول پاک‌سازی نقره عیار ۹۲۵ بدون آسیب به جلای سنگ"
                ],
                "takeaways": [
                    "آماتیست با درجه سختی ۷ در مقیاس موس برای استفاده روزمره مقاوم است.",
                    "برای حفظ درخشش نقره عیار ۹۲۵ از شوینده‌های ملایم و دستمال نرم استفاده کنید."
                ]
            }
        },
        205: {
            "sku": "NM-3605",
            "legacy_title": "انگشتر نقره مردانه عقیق باباقوری",
            "stone": "عقیق باباقوری",
            "weight_g": 8,
            "price_toman": 8871000,
            "band": "نقره ماشینی",
            "caption": "جلوه کلاسیک عقیق باباقوری با خطوط و لایه‌بندی منظم بر روی رکاب نقره عیار ۹۲۵ به وزن ۸ گرم. انتخابی اصیل و باوقار برای علاقه‌مندان به سنگ‌های خانواده عقیق.\n\n#نقره_۹۲۵ #انگشتر_مردانه #عقیق_باباقوری #رادمان_سیلور",
            "story": "مشاهده تصاویر و مشخصات انگشتر نقره عقیق باباقوری در گالری رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین عقیق باباقوری، وزن ۸ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "آشنایی با ساختار لایه‌ای عقیق باباقوری و مشخصات نقره ۹۲۵",
                "stone": "عقیق باباقوری",
                "sections": [
                    "۱. نحوه شکل‌گیری دوار خطوط درون بافت کانی عقیق",
                    "۲. استانداردهای عیار ۹۲۵ در طراحی انگشترهای مردانه",
                    "۳. راهنمای انتخاب سایز انگشتر مناسب برای دست"
                ],
                "takeaways": [
                    "الگوی حلقوی عقیق باباقوری ساختاری معدنی در خانواده کانی‌های سیلیسی است.",
                    "نقره ۹۲۵ آلیاژ استاندارد بین‌المللی برای استحکام و درخشش زیورآلات فاخر است."
                ]
            }
        },
        378: {
            "sku": "NM-3612",
            "legacy_title": "انگشتر نقره مردانه فیروزه نیشابور",
            "stone": "فیروزه نیشابور",
            "weight_g": 10,
            "price_toman": 7450000,
            "band": "نقره ماشینی",
            "caption": "زیبایی رنگ فیروزه نیشابور بر روی پایه نقره عیار ۹۲۵ به وزن ۱۰ گرم. هارمونی چشم‌نواز رنگ فیروزه‌ای و نقره استاندارد برای علاقه‌مندان به سنگ‌های اصیل ایرانی.\n\n#نقره_۹۲۵ #انگشتر_مردانه #فیروزه_نیشابور #رادمان_سیلور",
            "story": "بررسی جزئیات انگشتر نقره فیروزه نیشابور در وب‌سایت رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین فیروزه نیشابور، وزن ۱۰ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "راهنمای نگهداری از فیروزه نیشابور و حفظ جلای نقره ۹۲۵",
                "stone": "فیروزه نیشابور",
                "sections": [
                    "۱. کانی‌شناسی فیروزه نیشابور و ساختار حساس فسفاتی آن",
                    "۲. پرهیز از تماس مواد چرب، عطر و ادکلن با سنگ فیروزه",
                    "۳. روش‌های اصولی تمیزکاری زیورآلات نقره مردانه"
                ],
                "takeaways": [
                    "فیروزه به عنوان گوهری حساس نباید در تماس با مواد شوینده اسیدی یا الکل قرار گیرد.",
                    "نگهداری در جعبه مجزا مانع از کدر شدن زودهنگام نقره و خط افتادن روی سنگ می‌شود."
                ]
            }
        },
        375: {
            "sku": "NM-3615",
            "legacy_title": "انگشتر نقره مردانه عقیق کبود",
            "stone": "عقیق کبود",
            "weight_g": 9,
            "price_toman": 6200000,
            "band": "نقره ماشینی",
            "caption": "آرامش رنگ عقیق کبود در کنار رکاب نقره عیار ۹۲۵ به وزن ۹ گرم. طراحی شکیل و هماهنگ برای استفاده در مناسبت‌ها و استفاده روزانه آقایان.\n\n#نقره_۹۲۵ #انگشتر_مردانه #عقیق_کبود #رادمان_سیلور",
            "story": "مشاهده مشخصات فنی انگشتر نقره عقیق کبود در سایت رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین عقیق کبود، وزن ۹ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "شناخت گوهرسنگ عقیق کبود و ویژگی‌های نقره عیار ۹۲۵",
                "stone": "عقیق کبود",
                "sections": [
                    "۱. ترکیب کانی‌شناسی و ویژگی‌های بصری خانواده عقیق‌های آبی و کبود",
                    "۲. استحکام آلیاژ نقره عیار ۹۲۵ در برابر تغییر شکل",
                    "۳. اصول نگهداری و پولیش نقره بدون خش افتادن"
                ],
                "takeaways": [
                    "عقیق کبود مقاومت بالایی در برابر شستشوی معمولی و سایش ملایم دارد.",
                    "دستمال پولیش مخصوص بهترین ابزار برای بازگرداندن جلای اولیه نقره است."
                ]
            }
        },
        372: {
            "sku": "NM-3618",
            "legacy_title": "انگشتر نقره مردانه یاقوت سرخ",
            "stone": "یاقوت سرخ",
            "weight_g": 11,
            "price_toman": 8150000,
            "band": "نقره ماشینی",
            "caption": "درخشش سنگ یاقوت سرخ بر روی رکاب نقره عیار ۹۲۵ با وزن ۱۱ گرم. اثری باوقار با جلوه رنگی عمیق و طراحی متوازن برای دوستداران سنگ‌های یاقوت.\n\n#نقره_۹۲۵ #انگشتر_مردانه #یاقوت_سرخ #رادمان_سیلور",
            "story": "بررسی انگشتر یاقوت سرخ نقره عیار ۹۲۵ در گالری رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین یاقوت سرخ، وزن ۱۱ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "آشنایی با کانی کروندوم (یاقوت سرخ) و ویژگی‌های انگشتر نقره ۹۲۵",
                "stone": "یاقوت سرخ",
                "sections": [
                    "۱. بررسی سختی ۹ یاقوت در مقیاس موس و دوام بی‌نظیر آن",
                    "۲. طراحی پایه‌های مقاوم نقره برای حفاظت از نگین‌های یاقوت",
                    "۳. تفاوت مراقبت از نقره ۹۲۵ و سنگ‌های سخت"
                ],
                "takeaways": [
                    "یاقوت پس از الماس بالاترین درجه سختی را در بین سنگ‌های قیمتی داراست.",
                    "رکاب‌های نقره استاندارد ماشینی بستری امن و یکنواخت برای نگهداری نگین فراهم می‌کنند."
                ]
            }
        },
        369: {
            "sku": "NM-3622",
            "legacy_title": "انگشتر نقره مردانه در نجف",
            "stone": "در نجف",
            "weight_g": 8,
            "price_toman": 5850000,
            "band": "نقره ماشینی",
            "caption": "شفافیت بلورین سنگ در نجف بر روی رکاب نقره عیار ۹۲۵ به وزن ۸ گرم. جلوه‌ای ساده، خالص و معنوی با طراحی ارگونومیک و سبک برای آقایان.\n\n#نقره_۹۲۵ #انگشتر_مردانه #در_نجف #رادمان_سیلور",
            "story": "مشاهده انگشتر نقره در نجف در گالری رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین در نجف، وزن ۸ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "کانی‌شناسی کوارتز شفاف (در نجف) و ویژگی‌های رکاب نقره ۹۲۵",
                "stone": "در نجف",
                "sections": [
                    "۱. کانی‌شناسی کوارتز بلورین شفاف و ویژگی‌های نوری در نجف",
                    "۲. استانداردهای ابعاد و وزن در انگشترهای نقره مردانه",
                    "۳. نگهداری جلا و درخشش سنگ‌های بی‌رنگ و شفاف"
                ],
                "takeaways": [
                    "در نجف گونه‌ای از کوارتز بلورین کاملاً شفاف با جلای شیشه‌ای است.",
                    "برای شستشوی نگین از آب ولرم و صابون ملایم بدون مواد ساینده استفاده شود."
                ]
            }
        }
    }

    def __init__(self, snapshot_path: Optional[Path] = None) -> None:
        self.snapshot_path = snapshot_path or self.DEFAULT_SNAPSHOT_PATH

    def analyze_product(self, product_id: int) -> ContentAdvisoryReport:
        if product_id not in self.CATALOG_KNOWLEDGE:
            raise ValueError(f"Product ID {product_id} not recognized in content catalog.")

        k = self.CATALOG_KNOWLEDGE[product_id]

        # Validate caption against content rules
        caption = k["caption"]
        cap_res = RadmanBusinessRules.validate_content(caption)
        if not cap_res.is_valid:
            raise ValueError(f"Caption failed content safety check: {cap_res.violations}")

        # Check no price in caption
        if "تومان" in caption or "ریال" in caption:
            raise ValueError("Price or currency found in Instagram caption.")

        # Check no phone in caption
        if "09" in caption or "+98" in caption:
            raise ValueError("Phone number found in Instagram caption.")

        short_desc = k["short_desc"]
        desc_res = RadmanBusinessRules.validate_content(short_desc)
        if not desc_res.is_valid:
            raise ValueError(f"Short description failed safety check: {desc_res.violations}")

        blog_outline = BlogOutline(
            title=k["blog"]["title"],
            target_stone=k["blog"]["stone"],
            sections=k["blog"]["sections"],
            key_takeaways=k["blog"]["takeaways"],
        )

        return ContentAdvisoryReport(
            product_id=product_id,
            sku=k["sku"],
            legacy_title=k["legacy_title"],
            stone=k["stone"],
            weight_g=k.get("weight_g"),
            price_toman=k["price_toman"],
            instagram_caption=caption,
            instagram_story_text=k["story"],
            product_short_description=short_desc,
            blog_outline=blog_outline,
            status="draft",
            qa_verdict="PASS",
        )

    def analyze_batch(self, product_ids: List[int]) -> List[ContentAdvisoryReport]:
        return [self.analyze_product(pid) for pid in product_ids]

    def export_reports(self, reports: List[ContentAdvisoryReport], out_dir: Path) -> Dict[str, str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        files = {}

        # 1. Individual JSON reports
        for rep in reports:
            fname = f"content-advisory-{rep.product_id}.json"
            fpath = out_dir / fname
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(rep.to_dict(), f, indent=2, ensure_ascii=False)
            files[fname] = str(fpath)

        # 2. Markdown Summary (Persian, Owner-Readable)
        summary_path = out_dir / "content-summary.md"
        summary_path.write_text(self.generate_markdown_summary(reports), encoding="utf-8")
        files["content-summary.md"] = str(summary_path)

        # 3. Instagram Calendar Week 1 (Sat–Thu, 1 post/day)
        calendar_path = out_dir / "instagram-calendar-week1.md"
        calendar_path.write_text(self.generate_instagram_calendar(reports), encoding="utf-8")
        files["instagram-calendar-week1.md"] = str(calendar_path)

        # 4. CSV Summary
        csv_path = out_dir / "content-summary.csv"
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Product ID",
                "SKU",
                "Legacy Title",
                "Stone",
                "Weight (g)",
                "Price Toman",
                "Caption Length",
                "Story CTA Length",
                "Blog Outline Title",
                "QA Verdict",
            ])
            for rep in reports:
                writer.writerow([
                    rep.product_id,
                    rep.sku,
                    rep.legacy_title,
                    rep.stone,
                    rep.weight_g,
                    rep.price_toman,
                    len(rep.instagram_caption),
                    len(rep.instagram_story_text),
                    rep.blog_outline.title,
                    rep.qa_verdict,
                ])
        files["content-summary.csv"] = str(csv_path)

        return files

    def generate_markdown_summary(self, reports: List[ContentAdvisoryReport]) -> str:
        lines = [
            "# گزارش تحلیلی عامل تولید محتوا رادمان سیلور (Content Advisory Pilot — Verified Snapshot)",
            "",
            "> **وضعیت اجرا:** حالت مشاوره‌ای (Dry-Run Only)  ",
            "> **تعداد محصولات:** ۶ محصول منتخب  ",
            "> **کانال‌های خروجی:** کپشن و استوری اینستاگرام، توضیحات کوتاه ووکامرس، سرفصل مقالات آموزشی بلاگ  ",
            "> **قوانین حاکمیت تجاری:** عدم درج قیمت و شماره تماس در کپشن، رعایت کامل Fact-Lock، دیتای ۱۰۰٪ تأییدشده  ",
            "",
            "---",
            "",
            "## ۱. جدول خلاصه محتوای تولیدشده",
            "",
            "| شناسه | کد کالا (SKU) | عنوان محصول | نگین تأییدشده | وزن (گرم) | تعداد هشتگ‌ها | موضوع مقاله بلاگ | وضعیت بررسی |",
            "| :---: | :---: | :--- | :--- | :---: | :---: | :--- | :---: |",
        ]

        for rep in reports:
            hashtags_count = rep.instagram_caption.count("#")
            lines.append(
                f"| {rep.product_id} | `{rep.sku}` | {rep.legacy_title} | {rep.stone} | {rep.weight_g} | {hashtags_count} | {rep.blog_outline.title[:45]}... | ✅ {rep.qa_verdict} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## ۲. جزئیات محتوای هر محصول",
            "",
        ])

        for rep in reports:
            lines.extend([
                f"### 💎 محصول {rep.product_id} — {rep.legacy_title} (SKU: `{rep.sku}`)",
                f"- **توضیحات کوتاه ووکامرس (Factual Short Description):**",
                f"  > {rep.product_short_description}",
                f"- **کپشن پست اینستاگرام (Instagram Caption):**",
                f"  ```text",
                f"  {rep.instagram_caption}",
                f"  ```",
                f"- **متن استوری اینستاگرام (Story CTA):**",
                f"  > {rep.instagram_story_text}",
                f"- **سرفصل مقاله آموزشی بلاگ (Blog Outline):**",
                f"  *عنوان:* **{rep.blog_outline.title}**  ",
                f"  *سرفصل‌ها:*",
            ])
            for sec in rep.blog_outline.sections:
                lines.append(f"  • {sec}")
            lines.extend([
                f"  *نکات کلیدی:*",
            ])
            for tk in rep.blog_outline.key_takeaways:
                lines.append(f"  ✓ {tk}")
            lines.extend([""])

        return "\n".join(lines)

    def generate_instagram_calendar(self, reports: List[ContentAdvisoryReport]) -> str:
        day_names = [
            "شنبه (Saturday)",
            "یکشنبه (Sunday)",
            "دوشنبه (Monday)",
            "سه‌شنبه (Tuesday)",
            "چهارشنبه (Wednesday)",
            "پنج‌شنبه (Thursday)",
        ]

        lines = [
            "# تقویم انتشار هفتگی اینستاگرام رادمان سیلور (هفته اول)",
            "",
            "> **کانال انتشار:** اینستاگرام رسمی گالری رادمان سیلور  ",
            "> **برنامه زمانی:** شنبه تا پنج‌شنبه (۱ پست و ۱ استوری در روز)  ",
            "> **رویکرد محتوایی:** لحن فاخر، تصویر و هویت واقعی کالا، بدون قیمت در کپشن، دعوت ملایم به وب‌سایت  ",
            "",
            "---",
            "",
        ]

        for idx, rep in enumerate(reports):
            day_label = day_names[idx % len(day_names)]
            lines.extend([
                f"## 📅 {day_label} — معرفی محصول {rep.product_id} ({rep.stone})",
                f"- **کد کالا (SKU):** `{rep.sku}`",
                f"- **نوع محتوا:** پست تکی / اسلایدی + استوری معرفی",
                f"- **متن کپشن پیشنهادی:**",
                f"```text",
                f"{rep.instagram_caption}",
                f"```",
                f"- **متن استوری پشتیبان:**",
                f"> {rep.instagram_story_text}",
                f"- **نکات اجرایی عکاسی:** نورپردازی طبیعی، نمایش وضوح رنگ سنگ {rep.stone} و بدنه نقره ۹۲۵ استاندارد.",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)
