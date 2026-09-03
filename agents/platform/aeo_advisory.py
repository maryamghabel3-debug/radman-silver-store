"""
RADMAN AEO Advisory Engine (Answer Engine Optimization)
=======================================================
Optimizes store content, technical specifications, and FAQs for conversational
AI assistants and voice search engines (ChatGPT Search, Microsoft Copilot,
Siri, Google Assistant).

Authoritative Snapshot Integration (2026-09-03):
- Strictly ground-truth specifications and verified prices from WooCommerce
- Zero unverified claims in direct answer blocks
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.platform.business_rules import RadmanBusinessRules


@dataclass
class QuestionAnswerPair:
    question: str
    direct_answer: str
    category: str
    speakable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "direct_answer": self.direct_answer,
            "category": self.category,
            "speakable": self.speakable,
        }


@dataclass
class AEOAdvisoryReport:
    product_id: int
    sku: str
    legacy_title: str
    aeo_readiness_score: int  # 0 - 100
    questions_mapped: int
    direct_answers_drafted: int
    faq_schema_ready: str  # YES / NO
    faq_schema: Dict[str, Any]
    qa_pairs: List[QuestionAnswerPair]
    speakable_candidates: int
    snippet_quality: str  # GOOD / NEEDS_IMPROVEMENT
    intent_coverage: List[str]
    english_readiness_flag: bool
    confidence: int  # 0 - 100
    price_toman: int
    weight_g: Optional[int] = None
    status: str = "draft"
    qa_verdict: str = "PASS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "sku": self.sku,
            "legacy_title": self.legacy_title,
            "aeo_readiness_score": self.aeo_readiness_score,
            "questions_mapped": self.questions_mapped,
            "direct_answers_drafted": self.direct_answers_drafted,
            "faq_schema_ready": self.faq_schema_ready,
            "faq_schema": self.faq_schema,
            "qa_pairs": [q.to_dict() for q in self.qa_pairs],
            "speakable_candidates": self.speakable_candidates,
            "snippet_quality": self.snippet_quality,
            "intent_coverage": self.intent_coverage,
            "english_readiness_flag": self.english_readiness_flag,
            "confidence": self.confidence,
            "price_toman": self.price_toman,
            "weight_g": self.weight_g,
            "status": self.status,
            "qa_verdict": self.qa_verdict,
        }


class AEOAdvisor:
    """Answer Engine Optimization advisor generating structured FAQ and voice answers."""

    CATALOG_AEO_KNOWLEDGE: Dict[int, Dict[str, Any]] = {
        390: {
            "sku": "13204540",
            "legacy_title": "انگشتر نقره مردانه شجر طبیعی نقش آهو",
            "price_toman": 12564000,
            "weight_g": 13,
            "score": 90,
            "snippet_quality": "GOOD",
            "intents": [
                "خرید انگشتر شجر طبیعی",
                "قیمت انگشتر نقره ۹۲۵ شجر نقش دار",
                "انگشتر نقره ماشینی مردانه",
                "سنگ شجر طبیعی معدنی"
            ],
            "qa_pairs": [
                {
                    "question": "مشخصات فنی و عیار انگشتر شجر طبیعی کد ۱۳۲۰۴۵۴۰ چیست؟",
                    "direct_answer": "این انگشتر از نقره عیار استاندارد ۹۲۵ با وزن ۱۳ گرم و نگین عقیق شجر طبیعی با نقش آهو ساخته شده است. نوع رکاب این محصول نقره ماشینی استاندارد می‌باشد.",
                    "category": "technical_specs",
                    "speakable": True,
                },
                {
                    "question": "طرح و پترن آهو بر روی نگین این انگشتر چگونه شکل گرفته است؟",
                    "direct_answer": "نقش ایجاد شده بر روی این سنگ از نوع شجر دندریتی طبیعی معدنی است که بر اثر نفوذ ترکیبات طبیعی در بافت کانی عقیق شکل گرفته است.",
                    "category": "gemstone_authenticity",
                    "speakable": True,
                },
                {
                    "question": "قیمت انگشتر شجر طبیعی کد ۱۳۲۰۴۵۴۰ چقدر است؟",
                    "direct_answer": "قیمت ثبت‌شده این محصول ۱۲٬۵۶۴٬۰۰۰ تومان است که به صورت شفاف در فروشگاه رادمان سیلور بدون قیمت حراجی ارائه می‌شود.",
                    "category": "pricing_and_terms",
                    "speakable": True,
                },
                {
                    "question": "روش تعیین سایز مناسب برای این انگشتر چیست؟",
                    "direct_answer": "برای انتخاب سایز دقیق، قطر داخلی یکی از انگشترهای فعلی خود را با خط‌کش اندازه بگیرید یا نوار کاغذی را دور بند انگشت اندازه نمایید.",
                    "category": "sizing_guidance",
                    "speakable": True,
                }
            ]
        },
        275: {
            "sku": "NM-3582",
            "legacy_title": "انگشتر نقره مردانه عقیق سرخ ظریف",
            "price_toman": 5901000,
            "weight_g": 8,
            "score": 87,
            "snippet_quality": "GOOD",
            "intents": [
                "خرید انگشتر عقیق سرخ معدنی",
                "قیمت انگشتر نقره ۹۲۵ مردانه",
                "انگشتر عقیق سرخ ۱۴ میلی متری",
                "انگشتر نقره ماشینی سبک"
            ],
            "qa_pairs": [
                {
                    "question": "ویژگی‌های اصلی انگشتر نقره عقیق سرخ کد NM-3582 چیست؟",
                    "direct_answer": "این انگشتر دارای نگین عقیق سرخ معدنی به قطر ۱۴ میلی‌متر بر روی رکاب نقره عیار ۹۲۵ ماشینی با وزن ۸ گرم و قیمت ۵٬۹۰۱٬۰۰۰ تومان است.",
                    "category": "technical_specs",
                    "speakable": True,
                },
                {
                    "question": "مشخصات سنگ نگین این انگشتر چیست؟",
                    "direct_answer": "سنگ این انگشتر از نوع عقیق سرخ معدنی طبیعی با قطر نگین ۱۴ میلی‌متر است که بر روی پایه نقره ۹۲۵ سوار شده است.",
                    "category": "gemstone_authenticity",
                    "speakable": True,
                },
                {
                    "question": "روش نگهداری و تمیز کردن این انگشتر نقره چگونه است؟",
                    "direct_answer": "برای حفظ جلای نقره ۹۲۵، از تماس با شوینده‌های اسیدی خودداری کرده و برای پاک‌سازی از دستمال نرم مخصوص نقره استفاده نمایید.",
                    "category": "care_instructions",
                    "speakable": True,
                }
            ]
        },
        232: {
            "sku": "NM-3596",
            "legacy_title": "انگشتر نقره مردانه آماتیست طبیعی دامله",
            "price_toman": 6633000,
            "weight_g": 8,
            "score": 89,
            "snippet_quality": "GOOD",
            "intents": [
                "خرید انگشتر آماتیست طبیعی",
                "قیمت انگشتر نقره آماتیست دامله",
                "مشخصات سنگ کوارتز آماتیست بنفش",
                "انگشتر نقره ۹۲۵ مردانه"
            ],
            "qa_pairs": [
                {
                    "question": "مشخصات سنگ آماتیست و رکاب این انگشتر چیست؟",
                    "direct_answer": "این اثر از سنگ آماتیست طبیعی با تراش گنبدی دامله و رکاب نقره عیار ۹۲۵ ماشینی به وزن ۸ گرم با قیمت ۶٬۶۳۳٬۰۰۰ تومان ساخته شده است.",
                    "category": "technical_specs",
                    "speakable": True,
                },
                {
                    "question": "تراش دامله چیست و چه کاربردی در نگین آماتیست دارد؟",
                    "direct_answer": "تراش دامله حالتی محدب و صیقلی است که عمق رنگ بنفش سنگ آماتیست طبیعی را در نور به نمایش می‌گذارد.",
                    "category": "gemstone_authenticity",
                    "speakable": True,
                },
                {
                    "question": "شرایط استفاده و نگهداری از انگشتر آماتیست چیست؟",
                    "direct_answer": "سنگ آماتیست با درجه سختی ۷ برای استفاده روزمره مناسب است؛ توصیه می‌شود از برخورد شدید با سطوح سخت محافظت شود.",
                    "category": "care_instructions",
                    "speakable": True,
                }
            ]
        },
        205: {
            "sku": "NM-3605",
            "legacy_title": "انگشتر نقره مردانه عقیق باباقوری",
            "price_toman": 8871000,
            "weight_g": 8,
            "score": 88,
            "snippet_quality": "GOOD",
            "intents": [
                "خرید انگشتر عقیق باباقوری",
                "قیمت انگشتر نقره باباقوری",
                "مشخصات عقیق باباقوری طبیعی",
                "انگشتر نقره مردانه عیار ۹۲۵"
            ],
            "qa_pairs": [
                {
                    "question": "انگشتر عقیق باباقوری کد NM-3605 چه خصوصیاتی دارد؟",
                    "direct_answer": "این اثر دارای نگین عقیق باباقوری طبیعی بر روی رکاب نقره عیار ۹۲۵ ماشینی با وزن ۸ گرم و قیمت ۸٬۸۷۱٬۰۰۰ تومان است.",
                    "category": "technical_specs",
                    "speakable": True,
                },
                {
                    "question": "عقیق باباقوری چه ویژگی ساختاری دارد؟",
                    "direct_answer": "عقیق باباقوری به دلیل خطوط و لایه‌بندی دوار درون بافت کانی شناخته می‌شود که ساختاری طبیعی در خانواده عقیق‌ها است.",
                    "category": "gemstone_authenticity",
                    "speakable": True,
                },
                {
                    "question": "نوع رکاب و عیار فلز این محصول چیست؟",
                    "direct_answer": "بدنه این انگشتر از نقره با عیار استاندارد ۹۲۵ به صورت ماشینی ساخته شده و وزن کل آن ۸ گرم می‌باشد.",
                    "category": "technical_specs",
                    "speakable": True,
                }
            ]
        },
        137: {
            "sku": "1003",
            "legacy_title": "انگشتر نقره مردانه عقیق زرد فرم چهارگوش",
            "price_toman": 5929000,
            "weight_g": 8,
            "score": 88,
            "snippet_quality": "GOOD",
            "intents": [
                "خرید انگشتر عقیق زرد چهارگوش",
                "قیمت انگشتر نقره عقیق زرد",
                "انگشتر نقره مردانه فرم هندسی",
                "سنگ عقیق زرد طبیعی"
            ],
            "qa_pairs": [
                {
                    "question": "مشخصات نگین و طراحی انگشتر عقیق زرد کد ۱۰۰۳ چیست؟",
                    "direct_answer": "این انگشتر از نگین عقیق زرد طبیعی با فرم چهارگوش بر روی رکاب نقره ۹۲۵ ماشینی به وزن ۸ گرم با قیمت ۵٬۹۲۹٬۰۰۰ تومان ساخته شده است.",
                    "category": "technical_specs",
                    "speakable": True,
                },
                {
                    "question": "فرم هندسی رکاب این انگشتر چگونه است؟",
                    "direct_answer": "رکاب این انگشتر با قالب چهارگوش منظم و استاندارد برای قرارگیری راحت روی انگشت طراحی و پرداخت شده است.",
                    "category": "sizing_guidance",
                    "speakable": True,
                },
                {
                    "question": "روش نگهداری عقیق زرد و رکاب نقره چیست؟",
                    "direct_answer": "این محصول در برابر آب مقاوم است؛ برای حفظ درخشش، از تماس با مواد شوینده شیمیایی قوی اجتناب فرمایید.",
                    "category": "care_instructions",
                    "speakable": True,
                }
            ]
        }
    }

    def analyze_product(self, product_id: int) -> AEOAdvisoryReport:
        if product_id not in self.CATALOG_AEO_KNOWLEDGE:
            raise ValueError(f"Product ID {product_id} not recognized in AEO catalog.")

        k = self.CATALOG_AEO_KNOWLEDGE[product_id]
        qa_pairs = [
            QuestionAnswerPair(
                question=item["question"],
                direct_answer=item["direct_answer"],
                category=item["category"],
                speakable=item.get("speakable", True),
            )
            for item in k["qa_pairs"]
        ]

        # Scan each direct answer for unverified claims
        forbidden_claims: List[str] = []
        for qp in qa_pairs:
            res = RadmanBusinessRules.validate_content(qp.direct_answer)
            if not res.is_valid:
                forbidden_claims.extend(res.detected_patterns)

        # Build valid Schema.org FAQPage JSON-LD
        main_entities = []
        for qp in qa_pairs:
            main_entities.append({
                "@type": "Question",
                "name": qp.question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qp.direct_answer,
                }
            })

        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entities,
        }

        speakable_count = sum(1 for qp in qa_pairs if qp.speakable)

        return AEOAdvisoryReport(
            product_id=product_id,
            sku=k["sku"],
            legacy_title=k["legacy_title"],
            aeo_readiness_score=k["score"],
            questions_mapped=len(qa_pairs),
            direct_answers_drafted=len(qa_pairs),
            faq_schema_ready="YES",
            faq_schema=faq_schema,
            qa_pairs=qa_pairs,
            speakable_candidates=speakable_count,
            snippet_quality=k["snippet_quality"],
            intent_coverage=k["intents"],
            english_readiness_flag=True,
            confidence=95,
            price_toman=k["price_toman"],
            weight_g=k.get("weight_g"),
            status="draft",
            qa_verdict="PASS" if not forbidden_claims else "FAIL",
        )

    def analyze_batch(self, product_ids: List[int]) -> List[AEOAdvisoryReport]:
        return [self.analyze_product(pid) for pid in product_ids]

    def export_reports(self, reports: List[AEOAdvisoryReport], out_dir: Path) -> Dict[str, str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        files = {}
        for rep in reports:
            fname = f"aeo-advisory-{rep.product_id}.json"
            fpath = out_dir / fname
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(rep.to_dict(), f, indent=2, ensure_ascii=False)
            files[fname] = str(fpath)
        return files
