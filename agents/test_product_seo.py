#!/usr/bin/env python3
"""Offline deterministic product SEO generation tests."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_product_seo import (  # noqa: E402
    BRAND,
    MATERIAL,
    ProductSEOError,
    generate_seo_package,
    optional_external_llm_suggestion,
    quality_humanization_pass,
)


def record(legacy_id, sku, title, category, **specs):
    return {
        "legacy_id": legacy_id,
        "sku": sku,
        "title": title,
        "category": category,
        "category_raw": title,
        "featured_image_id": 700 + legacy_id,
        "gallery_image_ids": [800 + legacy_id, 900 + legacy_id],
        **specs,
    }


def test_category_titles_and_complete_packages() -> None:
    cases = (
        (record(1, "1057", "انگشتر عقیق سرخ", "rings", spec_silver_purity="925", spec_stone_type="عقیق", spec_stone_color="سرخ", spec_weight_grams="8.2"), "انگشتر"),
        (record(2, "1058", "گردنبند در نجف", "necklaces", spec_silver_purity="925", spec_stone_type="در نجف", spec_weight_grams="12"), "گردنبند"),
        (record(3, "1059", "دستبند نقره مردانه", "bracelets", spec_silver_purity="925", spec_weight_grams="18.5"), "دستبند"),
    )
    for source, product_type in cases:
        package = generate_seo_package(source)
        assert package["seo_title"] == (
            f"{source['title']} | خرید {product_type} نقره ۹۲۵ اصل | رادمان سیلور"
        )
        assert package["meta_description"]
        assert 2 <= len([item for item in package["short_description"].split(".") if item.strip()]) <= 4
        assert package["image_alt_plan"][0]["role"] == "featured"
        assert len(package["image_alt_plan"]) == 3
        assert package["search_entities"]["brand"] == BRAND
        assert package["search_entities"]["material"] == MATERIAL
        assert package["search_entities"]["purity"] == "925"
        assert package["rank_math_meta"]["rank_math_title"] == package["seo_title"]
        assert package["external_llm"]["status"] == "DISABLED_BY_DEFAULT"
        assert "aggregateRating" not in str(package)
    print("PASS: ring/necklace/bracelet SEO titles and packages are complete")


def test_unique_factual_meta_and_internal_links() -> None:
    ring_a = generate_seo_package(
        record(11, "A-11", "انگشتر عقیق سرخ", "rings", spec_silver_purity="925", spec_stone_type="عقیق", spec_stone_color="سرخ", spec_weight_grams="8")
    )
    ring_b = generate_seo_package(
        record(12, "A-12", "انگشتر فیروزه آبی", "rings", spec_silver_purity="925", spec_stone_type="فیروزه", spec_stone_color="آبی", spec_weight_grams="9")
    )
    assert ring_a["meta_description"] != ring_b["meta_description"]
    assert "عقیق" in ring_a["meta_description"] and "سرخ" in ring_a["meta_description"]
    link_types = {item["type"] for item in ring_a["internal_links"]}
    assert {"category", "ring_size", "silver_authenticity", "silver_care", "gemstone_guide"}.issubset(link_types)
    assert quality_humanization_pass(
        ring_a["seo_title"], ring_a["meta_description"], ring_a["short_description"]
    ).passed
    print("PASS: differing verified specs produce unique factual meta and relevant links")


def test_unsafe_content_and_optional_llm_are_suggestion_only() -> None:
    result = quality_humanization_pass(
        "تماس 09123456789 برای ارسال رایگان و ضمانت مادام العمر"
    )
    assert not result.passed
    assert "PHONE_NUMBER" in result.reasons
    assert "UNSUPPORTED_PROMISE" in result.reasons

    package = generate_seo_package(
        record(20, "A-20", "دستبند نقره", "bracelets", spec_silver_purity="925")
    )
    disabled = optional_external_llm_suggestion(package, environ={})
    assert disabled["status"] == "DISABLED_BY_DEFAULT"

    def slop_adapter(_package, _secret):
        return {"meta_description": "بهترین انتخاب برای شما"}

    rejected = optional_external_llm_suggestion(
        package,
        adapter=slop_adapter,
        environ={
            "RADMAN_ENABLE_EXTERNAL_LLM": "1",
            "RADMAN_EXTERNAL_LLM_API_KEY": "private-test-placeholder",
        },
    )
    assert rejected["status"] == "SUGGESTION_REJECTED"
    assert rejected["suggestion_only"] is True
    print("PASS: phone/promises are rejected and optional LLM can only suggest Draft text")


def main() -> int:
    test_category_titles_and_complete_packages()
    test_unique_factual_meta_and_internal_links()
    test_unsafe_content_and_optional_llm_are_suggestion_only()
    print("ALL PRODUCT SEO TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
