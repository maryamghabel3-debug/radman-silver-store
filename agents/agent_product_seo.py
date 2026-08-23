#!/usr/bin/env python3
"""Deterministic WooCommerce product SEO packages; external AI is suggestion-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

BRAND = "RADMAN SILVER 925"
MATERIAL = "Sterling Silver"
EXTERNAL_LLM_ENABLE_ENV = "RADMAN_ENABLE_EXTERNAL_LLM"
EXTERNAL_LLM_SECRET_ENV = "RADMAN_EXTERNAL_LLM_API_KEY"

CATEGORY_TYPES = {
    "rings": "انگشتر",
    "necklaces": "گردنبند",
    "bracelets": "دستبند",
}
CATEGORY_LINKS = {
    "rings": "/product-category/rings/",
    "necklaces": "/product-category/necklaces/",
    "bracelets": "/product-category/bracelets/",
}
GENERIC_AI_PHRASES = (
    "بهترین انتخاب برای شما",
    "تجربه ای بی نظیر",
    "تجربه‌ای بی‌نظیر",
    "ترکیبی از زیبایی و اصالت",
    "شاهکاری بی نظیر",
    "شاهکاری بی‌نظیر",
    "انتخابی ایده آل",
    "انتخابی ایده‌آل",
    "با افتخار تقدیم",
    "سطح استایل خود را ارتقا دهید",
)
UNSUPPORTED_PROMISES = (
    "ارسال رایگان", "ارسال فوری", "پرداخت در محل", "ضمانت مادام",
    "گارانتی", "مرجوعی", "بازگشت بدون قید", "پشتیبانی 24 ساعته",
    "موجودی محدود", "shipping", "warranty", "refund", "return policy",
)
INTERNAL_DISCLAIMER_PARTS = (
    "اطلاعات فوق فقط از مشخصات فنی",
    "صفحه همان محصول استخراج شده است",
)
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_PHONE_RE = re.compile(
    r"(?<![0-9])(?:(?:\+?98)|(?:0098)|0)?[\s()\-]*9(?:[\s()\-]*[0-9]){9}(?![0-9])"
)
_LANDLINE_RE = re.compile(
    r"(?<![0-9])0[\s(\-]*[0-9]{2,3}[\s)\-]*(?:[0-9][\s\-]*){7,8}(?![0-9])"
)


class ProductSEOError(RuntimeError):
    pass


@dataclass(frozen=True)
class HumanizationResult:
    passed: bool
    reasons: Tuple[str, ...]


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("ي", "ی").replace("ك", "ک")).strip()


def contains_phone(value: Any) -> bool:
    text = normalize_text(value).translate(_DIGITS)
    return bool(_PHONE_RE.search(text) or _LANDLINE_RE.search(text))


def contains_unsupported_promise(value: Any) -> bool:
    text = normalize_text(value).casefold()
    return any(term.casefold() in text for term in UNSUPPORTED_PROMISES)


def contains_internal_disclaimer(value: Any) -> bool:
    text = normalize_text(value)
    return any(part in text for part in INTERNAL_DISCLAIMER_PARTS)


def quality_humanization_pass(*values: Any) -> HumanizationResult:
    reasons: List[str] = []
    texts = [normalize_text(value) for value in values if normalize_text(value)]
    combined = " ".join(texts)
    if contains_phone(combined):
        reasons.append("PHONE_NUMBER")
    if contains_unsupported_promise(combined):
        reasons.append("UNSUPPORTED_PROMISE")
    if contains_internal_disclaimer(combined):
        reasons.append("INTERNAL_SYSTEM_DISCLAIMER")
    for phrase in GENERIC_AI_PHRASES:
        if phrase.casefold() in combined.casefold():
            reasons.append("GENERIC_AI_PHRASE")
            break
    for text in texts:
        sentences = [normalize_text(item) for item in re.split(r"[.!؟]+", text) if normalize_text(item)]
        if len(sentences) != len(set(sentences)):
            reasons.append("REPEATED_SENTENCE")
            break
    return HumanizationResult(not reasons, tuple(dict.fromkeys(reasons)))


def _spec(record: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = normalize_text(record.get(key))
        if value:
            return value
    return ""


def _category(record: Mapping[str, Any]) -> Tuple[str, str]:
    category = normalize_text(record.get("category"))
    if category in CATEGORY_TYPES:
        return category, CATEGORY_TYPES[category]
    raw = normalize_text(record.get("category_raw"))
    if "دستبند" in raw:
        return "bracelets", "دستبند"
    if "گردنبند" in raw or "مدال" in raw:
        return "necklaces", "گردنبند"
    return "rings", "انگشتر"


def _audience(record: Mapping[str, Any]) -> str:
    text = normalize_text(
        f"{record.get('title', '')} {record.get('category_raw', '')} {record.get('audience', '')}"
    )
    if "مردانه" in text:
        return "Men"
    if "زنانه" in text:
        return "Women"
    if "بچگانه" in text or "کودک" in text:
        return "Children"
    return ""


def _facts(record: Mapping[str, Any]) -> Dict[str, str]:
    return {
        "purity": _spec(record, "spec_silver_purity", "silver_purity", "purity"),
        "stone_type": _spec(record, "spec_stone_type", "stone_type", "gemstone"),
        "stone_color": _spec(record, "spec_stone_color", "stone_color", "color"),
        "weight": _spec(record, "spec_weight_grams", "weight_grams", "weight"),
        "setting_type": _spec(record, "spec_band_type", "setting_type"),
        "dimensions": _spec(record, "spec_dimensions", "dimensions"),
    }


def _fact_phrases(facts: Mapping[str, str]) -> List[str]:
    phrases: List[str] = []
    if facts.get("purity"):
        phrases.append(f"عیار نقره {facts['purity']}")
    if facts.get("stone_type"):
        stone = f"سنگ {facts['stone_type']}"
        if facts.get("stone_color"):
            stone += f" با رنگ {facts['stone_color']}"
        phrases.append(stone)
    elif facts.get("stone_color"):
        phrases.append(f"رنگ نگین {facts['stone_color']}")
    if facts.get("weight"):
        weight = facts["weight"]
        if "گرم" not in weight:
            weight += " گرم"
        phrases.append(f"وزن {weight}")
    if facts.get("setting_type"):
        phrases.append(f"رکاب {facts['setting_type']}")
    if facts.get("dimensions"):
        phrases.append(f"ابعاد {facts['dimensions']}")
    return phrases


def _stable_variant(identity: str, count: int) -> int:
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % count


def generate_seo_package(record: Mapping[str, Any]) -> Dict[str, Any]:
    title = normalize_text(record.get("title") or record.get("public_title"))
    sku = normalize_text(record.get("sku"))
    legacy_id = normalize_text(record.get("legacy_id"))
    if not title or not sku or not legacy_id:
        raise ProductSEOError("title, SKU and legacy identity are required")
    category, product_type = _category(record)
    facts = _facts(record)
    phrases = _fact_phrases(facts)
    identity = f"{legacy_id}:{sku}:{title}"
    variant = _stable_variant(identity, 3)

    seo_title = f"{title} | خرید {product_type} نقره ۹۲۵ اصل | رادمان سیلور"
    detail = "، ".join(phrases[:4])
    meta_templates = (
        f"{title} با کد مدل {sku}" + (f" و مشخصات {detail}" if detail else "") + "؛ جزئیات فنی و قیمت این مدل را در رادمان سیلور ببینید.",
        f"برای بررسی {title} با کد مدل {sku}" + (f"، شامل {detail}" if detail else "") + "، مشخصات ثبت‌شده محصول را در رادمان سیلور مشاهده کنید.",
        f"مشخصات {title}، کد مدل {sku}" + (f"، شامل {detail}" if detail else "") + " است؛ اطلاعات فنی و قیمت محصول در رادمان سیلور درج شده است.",
    )
    meta_description = meta_templates[variant]

    short_sentences = [f"{title} یک {product_type} نقره از مجموعه رادمان سیلور است."]
    if phrases:
        short_sentences.append("مشخصات ثبت‌شده این مدل شامل " + "، ".join(phrases[:4]) + " است.")
    short_sentences.append(f"کد مدل این محصول {sku} است.")
    short_description = " ".join(short_sentences[:4])

    visible_attribute = facts.get("stone_type") or facts.get("stone_color") or facts.get("setting_type")
    alt_base = title + (f" با {visible_attribute}" if visible_attribute else "")
    featured_id = int(record.get("featured_image_id") or 0)
    gallery_ids = [int(value) for value in record.get("gallery_image_ids", []) if int(value) > 0]
    alt_plan = []
    if featured_id:
        alt_plan.append({"attachment_id": featured_id, "role": "featured", "alt": f"تصویر اصلی {alt_base}"})
    for index, attachment_id in enumerate(gallery_ids, 1):
        alt_plan.append({"attachment_id": attachment_id, "role": "gallery", "alt": f"تصویر {index + 1} {alt_base}"})

    internal_links = [
        {"type": "category", "target": CATEGORY_LINKS[category]},
        {"type": "silver_authenticity", "target": "/راهنمای-تشخیص-نقره-اصل/"},
        {"type": "silver_care", "target": "/راهنمای-نگهداری-نقره/"},
    ]
    if category == "rings":
        internal_links.append({"type": "ring_size", "target": "/راهنمای-سایز-انگشتر/"})
    if facts.get("stone_type"):
        internal_links.append({"type": "gemstone_guide", "target": "/راهنمای-سنگ-های-قیمتی/"})

    entities = {
        "brand": BRAND,
        "material": MATERIAL,
        "purity": "925" if "925" in facts.get("purity", "") else facts.get("purity", ""),
        "color": facts.get("stone_color", ""),
        "gemstone": facts.get("stone_type", ""),
        "weight": facts.get("weight", ""),
        "audience": _audience(record),
    }
    woo_attributes = {
        "وزن": facts.get("weight", ""),
        "عیار نقره": entities["purity"],
        "نوع سنگ": entities["gemstone"],
        "رنگ نگین": entities["color"],
        "نوع رکاب": facts.get("setting_type", ""),
        "مخاطب": entities["audience"],
        "کد مدل": sku,
    }
    woo_attributes = {key: value for key, value in woo_attributes.items() if value}

    quality = quality_humanization_pass(seo_title, meta_description, short_description)
    if not quality.passed:
        raise ProductSEOError("deterministic SEO package failed quality gate: " + ",".join(quality.reasons))

    return {
        "legacy_id": legacy_id,
        "sku": sku,
        "title": title,
        "category": category,
        "seo_title": seo_title,
        "meta_description": meta_description,
        "short_description": short_description,
        "image_alt_plan": alt_plan,
        "internal_links": internal_links,
        "search_entities": entities,
        "woo_attributes": woo_attributes,
        "rank_math_meta": {
            "rank_math_title": seo_title,
            "rank_math_description": meta_description,
            "rank_math_focus_keyword": f"خرید {title}",
        },
        "quality_status": "HUMANIZATION_PASS",
        "external_llm": {"enabled": False, "suggestion_only": True, "status": "DISABLED_BY_DEFAULT"},
    }


def optional_external_llm_suggestion(
    package: Mapping[str, Any],
    adapter: Optional[Callable[[Mapping[str, Any], str], Mapping[str, Any]]] = None,
    *,
    environ: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    env = dict(os.environ if environ is None else environ)
    if env.get(EXTERNAL_LLM_ENABLE_ENV) != "1":
        return {"enabled": False, "suggestion_only": True, "status": "DISABLED_BY_DEFAULT"}
    if adapter is None:
        return {"enabled": True, "suggestion_only": True, "status": "ADAPTER_NOT_CONFIGURED"}
    secret = env.get(EXTERNAL_LLM_SECRET_ENV, "")
    if not secret:
        return {"enabled": True, "suggestion_only": True, "status": "PRIVATE_SECRET_MISSING"}
    suggestion = dict(adapter(dict(package), secret))
    quality = quality_humanization_pass(*suggestion.values())
    if not quality.passed:
        return {
            "enabled": True,
            "suggestion_only": True,
            "status": "SUGGESTION_REJECTED",
            "reasons": list(quality.reasons),
        }
    return {
        "enabled": True,
        "suggestion_only": True,
        "status": "DRAFT_SUGGESTION_READY",
        "suggestion": suggestion,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    records = payload if isinstance(payload, list) else payload.get("products", [])
    packages = [generate_seo_package(record) for record in records]
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(packages, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
