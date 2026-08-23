#!/usr/bin/env python3
"""Offline publication-blocking SEO QA tests."""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_product_seo import generate_seo_package  # noqa: E402
from agents.agent_product_seo_qa import (  # noqa: E402
    SEO_BLOCKED,
    SEO_PASS,
    detect_duplicate_content,
    evaluate_products,
    write_qa_reports,
)


def valid_record(legacy_id: int, sku: str, title: str, category: str, description: str):
    source = {
        "product_id": 100 + legacy_id,
        "legacy_id": str(legacy_id),
        "sku": sku,
        "title": title,
        "public_title": title,
        "status": "draft",
        "category": category,
        "category_ids": [17],
        "featured_image_id": 700 + legacy_id,
        "gallery_image_ids": [800 + legacy_id],
        "description": description,
        "price": "7689000",
        "regular_price": "7689000",
        "sale_price_readonly": "",
        "currency": "IRT",
        "stock_quantity": 1,
        "stock_status": "instock",
        "spec_purity": "925",
        "spec_stone_type": "عقیق" if category == "rings" else "در نجف",
        "spec_stone_color": "سرخ" if category == "rings" else "سفید",
        "spec_weight": "8.2" if category == "rings" else "12",
    }
    source["seo_package"] = generate_seo_package(source)
    source["short_description"] = source["seo_package"]["short_description"]
    source["rank_math_title"] = source["seo_package"]["seo_title"]
    source["rank_math_description"] = source["seo_package"]["meta_description"]
    return source


def test_valid_drafts_pass_schema_and_publication_gate() -> None:
    records = [
        valid_record(1, "1057", "انگشتر عقیق سرخ", "rings", "انگشتر عقیق سرخ با وزن ثبت شده 8.2 گرم و عیار 925."),
        valid_record(2, "1058", "گردنبند در نجف", "necklaces", "گردنبند در نجف با وزن ثبت شده 12 گرم و عیار نقره 925."),
    ]
    payload = evaluate_products(records)
    assert payload["summary"][SEO_PASS] == 2
    assert payload["summary"][SEO_BLOCKED] == 0
    assert all(row["consistent"] for row in payload["schema"])
    assert not payload["duplicates"]
    print("PASS: complete Drafts pass SEO and visible schema consistency gates")


def test_missing_critical_unsafe_schema_and_fake_rating_block() -> None:
    broken = valid_record(3, "1059", "دستبند نقره", "bracelets", "برای ارسال رایگان با 09123456789 تماس بگیرید.")
    broken.update(
        {
            "status": "publish",
            "featured_image_id": 0,
            "regular_price": "7000000",
            "sale_price_readonly": "6500000",
            "schema_price": "6000000",
            "schema_currency": "IRR",
            "aggregate_rating": {"ratingValue": 5},
            "short_description": "",
            "rank_math_title": "",
            "rank_math_description": "",
            "seo_package": {},
        }
    )
    payload = evaluate_products([broken])
    result = payload["results"][0]
    assert result["seo_status"] == SEO_BLOCKED
    assert result["publication_blocked"] is True
    for blocker in (
        "STATUS_NOT_DRAFT", "FEATURED_IMAGE_MISSING", "SALE_PRICE_NOT_EMPTY",
        "PHONE_NUMBER_IN_PUBLIC_CONTENT", "UNSUPPORTED_PROMISE",
        "UNSUPPORTED_REVIEW_OR_RATING", "SCHEMA_VISIBLE_DATA_MISMATCH",
    ):
        assert blocker in result["blockers"]
    print("PASS: missing fields, unsafe content, fake rating and schema mismatch block publication")


def test_duplicate_detection_and_required_reports() -> None:
    left = valid_record(4, "1060", "انگشتر عقیق", "rings", "توضیح فنی یکسان برای آزمایش محتوای تکراری.")
    right = valid_record(5, "1061", "انگشتر عقیق دیگر", "rings", "توضیح فنی یکسان برای آزمایش محتوای تکراری.")
    right["seo_package"] = dict(left["seo_package"])
    right["rank_math_description"] = left["rank_math_description"]
    duplicates = detect_duplicate_content([left, right])
    assert duplicates and float(duplicates[0]["similarity"]) >= 0.90
    payload = evaluate_products([left, right])
    assert payload["summary"][SEO_BLOCKED] == 2
    with tempfile.TemporaryDirectory() as temporary:
        paths = write_qa_reports(payload, Path(temporary))
        assert {path.name for path in paths.values()} == {
            "product-seo-report.csv",
            "product-seo-report-fa.txt",
            "duplicate-content-report.csv",
            "schema-consistency-report.csv",
            "publication-blockers.csv",
        }
        with paths["blockers"].open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 2
        assert all("DUPLICATE_CONTENT" in row["blockers"] for row in rows)
    print("PASS: duplicate content blocks publication and all five QA reports are written")


def main() -> int:
    test_valid_drafts_pass_schema_and_publication_gate()
    test_missing_critical_unsafe_schema_and_fake_rating_block()
    test_duplicate_detection_and_required_reports()
    print("ALL PRODUCT SEO QA TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
