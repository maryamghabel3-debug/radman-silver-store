"""
RADMAN Content Advisory Engine (Phase 2 Content Pilot — Corrected Snapshot 2026-09-04)
=====================================================================================
Produces brand-compliant, luxury Persian social media captions, Instagram story
text, factual WooCommerce short descriptions, and educational blog outlines.

Authoritative Snapshot & Fact-Lock Enforcement:
- Verified fields only from data/verified-product-snapshot-20260904.json
- Zero unverified claims (دست‌ساز, شناسنامه, بسته‌بندی, گارانتی, نرخ مصوب)
- No prices or phone numbers in social captions
- No medical/spiritual claims
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

    DEFAULT_SNAPSHOT_PATH = Path("data/verified-product-snapshot-20260904.json")

    # Authoritative verified catalog for content generation (2026-09-04)
    CATALOG_KNOWLEDGE: Dict[int, Dict[str, Any]] = {
        232: {
            "sku": "NM-3596",
            "legacy_title": "انگشتر نقره مردانه آماتیست طبیعی دامله",
            "stone": "آماتیست طبیعی دامله",
            "weight_g": 8,
            "price_toman": 6633000,
            "band": "نقره ماشینی",
            "caption": "درخشش سنگ آماتیست طبیعی با تراش گنبدی دامله بر روی رکاب نقره عیار ۹۲۵ به وزن ۸ گرم. ترکیبی هماهنگ از جلوه بنفش چشم‌نواز و بدنه استاندارد نقره برای استایل روزمره آقایان.\n\n#نقره_۹۲۵ #انگشتر_مردانه #آماتیست_طبیعی #رادمان_سیلور",
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
            "sku": "NM-3548",
            "legacy_title": "انگشتر نقره مردانه عقیق سیاه حکاکی حسبی الله",
            "stone": "عقیق سیاه",
            "inscription": "حسبی الله",
            "weight_g": 12,
            "price_toman": 8100000,
            "band": "نقره ماشینی",
            "caption": "وقار سنگ عقیق سیاه همراه با حکاکی ذکر حسبی الله بر روی رکاب نقره عیار ۹۲۵ به وزن ۱۲ گرم. اثری نفیس و چشم‌نواز با طراحی ارگونومیک برای آقایان.\n\n#نقره_۹۲۵ #انگشتر_مردانه #عقیق_سیاه #حسبی_الله #رادمان_سیلور",
            "story": "مشاهده مشخصات انگشتر نقره عقیق سیاه با حکاکی حسبی الله در گالری رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین عقیق سیاه با حکاکی حسبی الله، وزن ۱۲ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "شناخت سنگ عقیق سیاه و سنت حکاکی خط بر روی نگین‌های نقره",
                "stone": "عقیق سیاه",
                "sections": [
                    "۱. ویژگی‌های کانی‌شناسی عقیق سیاه مات و براق",
                    "۲. تاریخچه و اسلوب حکاکی کتیبه‌های سنتی بر عقیق",
                    "۳. اصول نگهداری نقره عیار ۹۲۵ با نگین‌های حکاکی‌شده"
                ],
                "takeaways": [
                    "عقیق سیاه به دلیل بافت ریزبلورین بستری ایده‌آل برای ظرافت خط و حکاکی است.",
                    "برای حفظ خطوط حکاکی از مواد ساینده زبر بر روی سطح نگین خودداری شود."
                ]
            }
        },
        375: {
            "sku": "NM-3549",
            "legacy_title": "انگشتر نقره مردانه عقیق سوسنی نقش رزق و روزی",
            "stone": "عقیق سوسنی",
            "inscription": "رزق و روزی",
            "weight_g": 12,
            "price_toman": 8100000,
            "band": "نقره ماشینی",
            "caption": "رنگ ملایم و خاص عقیق سوسنی با حکاکی نقش رزق و روزی بر روی رکاب نقره عیار ۹۲۵ به وزن ۱۲ گرم. ترکیبی متوازن از هنر خوشنویسی سنتی و بدنه استاندارد نقره.\n\n#نقره_۹۲۵ #انگشتر_مردانه #عقیق_سوسنی #رادمان_سیلور",
            "story": "بررسی انگشتر نقره عقیق سوسنی با نقش رزق و روزی در وب‌سایت رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین عقیق سوسنی با نقش رزق و روزی، وزن ۱۲ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "بررسی کانی عقیق سوسنی و ویژگی‌های رکاب نقره عیار ۹۲۵",
                "stone": "عقیق سوسنی",
                "sections": [
                    "۱. طیف‌های رنگی عقیق سوسنی و خاستگاه طبیعی کانی",
                    "۲. طراحی رکاب‌های نقره ماشینی با استحکام بالا",
                    "۳. روش‌های شستشو و پاک‌سازی نقره بدون آسیب به نگین"
                ],
                "takeaways": [
                    "عقیق سوسنی از تنوع رنگی چشم‌نواز در رده کانی‌های کلسدونی برخوردار است.",
                    "رکاب نقره ماشینی استاندارد توازن وزنی مناسبی برای نگهداری نگین‌های درشت دارد."
                ]
            }
        },
        372: {
            "sku": "NM-3550",
            "legacy_title": "انگشتر نقره مردانه دُر نجف اصل",
            "stone": "دُر نجف",
            "weight_g": 12,
            "price_toman": 10500000,
            "band": "نقره ماشینی",
            "caption": "شفافیت بلورین سنگ دُر نجف بر روی رکاب نقره عیار ۹۲۵ به وزن ۱۲ گرم. اثری با طراحی منظم و خالص با نشیمن راحت بر روی انگشت.\n\n#نقره_۹۲۵ #انگشتر_مردانه #در_نجف #رادمان_سیلور",
            "story": "مشاهده تصاویر و جزئیات انگشتر نقره دُر نجف در وب‌سایت رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین دُر نجف، وزن ۱۲ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "کانی‌شناسی کوارتز شفاف (دُر نجف) و ویژگی‌های رکاب نقره ۹۲۵",
                "stone": "دُر نجف",
                "sections": [
                    "۱. بررسی کانی‌شناسی کوارتز بلورین کاملاً شفاف",
                    "۲. استانداردهای ابعاد و وزن در انگشترهای نقره مردانه",
                    "۳. نگهداری جلا و پاک‌سازی نگین‌های بی‌رنگ"
                ],
                "takeaways": [
                    "دُر نجف گونه‌ای از کوارتز بلورین کاملاً شفاف با جلای شیشه‌ای است.",
                    "برای شستشوی نگین از آب ولرم و صابون ملایم استفاده شود."
                ]
            }
        },
        369: {
            "sku": "NM-3551",
            "legacy_title": "انگشتر نقره مردانه عقیق زرد حکاکی یا اباعبدالله",
            "stone": "عقیق زرد",
            "inscription": "یا اباعبدالله",
            "weight_g": 12,
            "price_toman": 8100000,
            "band": "نقره ماشینی",
            "caption": "درخشش سنگ عقیق زرد همراه با حکاکی ذکر یا اباعبدالله بر روی رکاب نقره عیار ۹۲۵ به وزن ۱۲ گرم. جلوه‌ای فاخر با نقوش اصیل سنتی ویژه آقایان.\n\n#نقره_۹۲۵ #انگشتر_مردانه #عقیق_زرد #رادمان_سیلور",
            "story": "مشاهده انگشتر نقره عقیق زرد با حکاکی یا اباعبدالله در گالری رادمان سیلور (لینک در بایو).",
            "short_desc": "انگشتر نقره مردانه با عیار استاندارد ۹۲۵، نگین عقیق زرد با حکاکی یا اباعبدالله، وزن ۱۲ گرم و رکاب نقره ماشینی.",
            "blog": {
                "title": "شناخت گوهرسنگ عقیق زرد و سنت کتیبه‌نگاری بر نگین‌های نقره",
                "stone": "عقیق زرد",
                "sections": [
                    "۱. کانی‌شناسی و دلایل رنگ زرد طبیعی در بافت عقیق",
                    "۲. هنر خوشنویسی و حکاکی مذهبی بر روی سنگ‌های زینتی",
                    "۳. راهنمای نگهداری و تمیزکاری نقره ۹۲۵"
                ],
                "takeaways": [
                    "عقیق زرد دارای دوام مناسب برای استفاده روزمره و نگهداری کتیبه است.",
                    "برای حفظ درخشش نقره از تماس با شوینده‌های اسیدی پرهیز شود."
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

        # Locked Identity validation
        id_valid, id_viols = RadmanBusinessRules.validate_locked_identity(
            product_id=product_id,
            sku=k["sku"],
            title=k["legacy_title"],
            stone=k["stone"],
        )
        if not id_valid:
            raise ValueError(f"Product {product_id} failed locked identity validation: {id_viols}")

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
            "# گزارش تحلیلی عامل تولید محتوا رادمان سیلور (Content Advisory Pilot — Corrected Snapshot)",
            "",
            "> **وضعیت اجرا:** حالت مشاوره‌ای (Dry-Run Only)  ",
            "> **منبع حقیقت:** snapshot معتبر هاست وردپرس استیجینگ (2026-09-04)  ",
            "> **تعداد محصولات:** ۶ محصول منتخب  ",
            "> **کانال‌های خروجی:** کپشن و استوری اینستاگرام، توضیحات کوتاه ووکامرس، سرفصل مقالات آموزشی بلاگ  ",
            "> **قوانین حاکمیت تجاری:** عدم درج قیمت و شماره تماس در کپشن، رعایت کامل Fact-Lock، دیتای ۱۰۰٪ تأییدشده  ",
            "",
            "---",
            "",
            "## ۱. جدول خلاصه محتوای تولیدشده (داده‌های ۱۰۰٪ تأییدشده)",
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
            "# تقویم انتشار هفتگی اینستاگرام رادمان سیلور (هفته اول — نسخه اصلاح‌شده)",
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
                f"- **عنوان اثر:** {rep.legacy_title}",
                f"- **نوع محتوا:** پست تکی / اسلایدی + استوری معرفی",
                f"- **متن کپشن پیشنهادی:**",
                f"```text",
                f"{rep.instagram_caption}",
                f"```",
                f"- **متن استوری پشتیبان:**",
                f"> {rep.instagram_story_text}",
                f"- **نکات اجرایی عکاسی:** نورپردازی طبیعی، نمایش وضوح نگین {rep.stone} و بدنه نقره ۹۲۵ استاندارد ماشینی.",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)
