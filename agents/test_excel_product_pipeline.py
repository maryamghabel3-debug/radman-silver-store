#!/usr/bin/env python3
"""Offline fixture and safety tests for the PR-28 Excel import pipeline."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "excel-import" / "excel_products.json"
SPEC_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "legacy-specs" / "spec_blocks.json"
LIVE_HTML_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "legacy-specs" / "live_product_page.html"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

import agent_excel_product_pipeline as pipeline  # noqa: E402


def make_excel(path: Path) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = pipeline.SHEET_NAME
    sheet.append(fixture["headers"])
    for product in fixture["products"]:
        row = [None] * 29
        row[pipeline.COL_ID - 1] = product["id"]
        row[pipeline.COL_TITLE - 1] = product["title"]
        row[pipeline.COL_CATEGORY - 1] = product["category"]
        row[pipeline.COL_PRICE - 1] = product["price"]
        row[pipeline.COL_PRE_DISCOUNT_PRICE - 1] = product["pre_discount"]
        row[pipeline.COL_STOCK - 1] = product["stock"]
        row[pipeline.COL_AVAILABILITY - 1] = product["availability"]
        row[pipeline.COL_ACTIVE - 1] = product["active"]
        row[pipeline.COL_WEIGHT - 1] = product["weight"]
        row[pipeline.COL_RAW_CODE - 1] = product["raw_code"]
        row[pipeline.COL_SEO_TITLE - 1] = product["seo_title"]
        row[pipeline.COL_SEO_DESCRIPTION - 1] = product["seo_description"]
        sheet.append(row)
    workbook.create_sheet("خالی")
    workbook.save(path)
    workbook.close()


def test_real_spec_block_fixtures_and_html_section_parser() -> None:
    fixtures = json.loads(SPEC_FIXTURE.read_text(encoding="utf-8"))
    parsed = []
    for fixture in fixtures:
        specs = pipeline.parse_spec_block_text(fixture["text"])
        expected = fixture["expected"]
        assert specs.stone_type == expected["stone_type"]
        assert specs.stone_color == expected["stone_color"]
        assert specs.band_type == expected["band_type"]
        assert specs.engraving_type == expected["engraving_type"]
        assert specs.silver_purity == expected["silver_purity"]
        assert specs.size == expected["size"]
        assert specs.weight_grams == Decimal(expected["weight_grams"])
        parsed.append(specs)
    assert parsed[0].weight_display == "16 گرم"
    assert parsed[2].stone_type == "در نجف"

    html_page = LIVE_HTML_FIXTURE.read_text(encoding="utf-8")
    extracted = pipeline.extract_legacy_specs(html_page)
    assert extracted.technical_count == 8
    assert extracted.category == "انگشتر مردانه"
    assert extracted.weight_grams == Decimal("8.2")
    assert extracted.stone_type == "عقیق"
    assert extracted.stone_color == "سیاه"
    assert extracted.band_type == "دست ساز"
    assert extracted.silver_purity == "925"
    assert extracted.dimensions == "14 × 10 میلی متر"
    assert extracted.size == "60"
    assert extracted.model_code == "1057"
    serialized = json.dumps(extracted.to_dict(), ensure_ascii=False)
    for forbidden in (
        "0912", "۰۹۱۲", "نمایش کمتر", "پست پیشتاز رایگان",
        "ضمانت مادام", "پرداخت در محل", "آدرس", "بهترین انگشتر",
    ):
        assert forbidden not in serialized

    adjacent_blocks = """
    <section><h2>مشخصات</h2>
      <div>وزن تقریبی</div><div>۹.۵ گرم</div>
      <div><span>سنگ</span><span>فیروزه</span></div>
      <div><span>عیار</span><span>925</span></div>
    </section>
    """
    adjacent = pipeline.extract_legacy_specs(adjacent_blocks)
    assert adjacent.weight_grams == Decimal("9.5")
    assert adjacent.stone_type == "فیروزه"
    assert adjacent.silver_purity == "925"
    print("PASS: strict table/dl/div/visible HTML extraction yields 5+ safe technical fields")


def test_unique_descriptions_differ_and_omit_missing_fields() -> None:
    fixtures = json.loads(SPEC_FIXTURE.read_text(encoding="utf-8"))
    descriptions = []
    for index, fixture in enumerate(fixtures, start=1):
        specs = pipeline.parse_spec_block_text(fixture["text"])
        record = {
            "legacy_id": 300 + index,
            "sku": f"MODEL-{index}",
            "title": f"انگشتر نمونه {index}",
            "category_raw": "انگشتر مردانه",
            "category": "rings",
            "seo_fallback_description": "متن عمومی قدیمی",
        }
        description, source = pipeline.generate_unique_description(record, specs)
        assert source == "SPECS_TEMPLATE"
        assert "متن عمومی قدیمی" not in description
        assert "None" not in description
        assert f"کد مدل: MODEL-{index}" in description
        assert "موجودی محدود" not in description
        assert "اصل" not in description
        assert "ثبت سفارش" not in description
        descriptions.append(description)
    assert len(set(descriptions)) == 3
    assert "- نوع حکاکی: " not in descriptions[1]
    assert "- نوع رکاب: " not in descriptions[1]
    assert "- نوع سنگ: در نجف" in descriptions[2]
    size_missing = pipeline.parse_spec_block_text("نوع سنگ:فیروزه · عیار نقره:925")
    size_description, size_source = pipeline.generate_unique_description(
        {
            "legacy_id": 999,
            "sku": "MODEL-999",
            "title": "انگشتر فیروزه",
            "category_raw": "انگشتر",
            "category": "rings",
        },
        size_missing,
    )
    assert size_source == "MINIMAL_SAFE"
    assert "در حال تکمیل مشخصات فنی است" in size_description
    assert "امکان انتخاب سایز دلخواه هنگام ثبت سفارش" not in size_description
    assert "موجودی محدود" not in size_description
    assert "None" not in size_description
    print("PASS: factual descriptions use verified bullets or exact minimal-safe fallback")


def test_excel_parsing_sku_pricing_and_categories() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        excel = Path(temporary) / "products.xlsx"
        make_excel(excel)
        records, warnings = pipeline.load_excel_records(excel)
        assert len(records) == 8
        assert warnings == []
        by_id = {record["legacy_id"]: record for record in records}

        title_code = by_id[3643]
        assert title_code["sku"] == "1058"
        assert title_code["sku_source"] == "TITLE_CODE"
        assert title_code["title"] == "انگشتر نقره"
        assert title_code["legacy_original_title"] == "انگشتر نقره کد 1058"
        assert title_code["extracted_title_code"] == "1058"
        assert title_code["radman_legacy_code"] == "1058"
        assert title_code["legacy_identity_key"] == "3643:1058"
        assert title_code["legacy_title_cleanup_status"] == "CLEANED"
        assert title_code["raw_code"] == "2079000.0000000002"
        assert title_code["category"] == "rings"
        assert title_code["excel_price_toman"] == 7_689_000
        assert title_code["weight_grams"] is None
        assert title_code["price_source"] == "EXCEL_ONLY"
        assert title_code["final_price_toman"] == 7_700_000
        assert title_code["regular_price_toman"] == 7_700_000
        assert "sale_price_toman" not in title_code

        contaminated = by_id[3642]
        assert contaminated["sku"] == "NM-3642"
        assert contaminated["sku_source"] == "FALLBACK_LEGACY_ID"
        assert contaminated["computed_price_toman"] == "1300000"
        assert contaminated["price_source"] == "MAX_EXCEL"
        assert contaminated["final_price_toman"] == 2_100_000
        assert contaminated["category"] == "necklaces"
        assert contaminated["description"] == "عنوان 3642"

        persian_code = by_id[3641]
        assert persian_code["sku"] == "1059"
        assert persian_code["sku_source"] == "COL27_VALIDATED"
        assert persian_code["category"] == "bracelets"
        assert persian_code["weight_grams"] == "1.0"
        assert persian_code["price_source"] == "MAX_EXCEL"
        assert persian_code["regular_price_toman"] == 1_000_000
        assert "sale_price_toman" not in persian_code

        large = by_id[3640]
        assert large["stone_class"] == "large_stone"
        assert large["rate_used"] == 590_000
        assert large["computed_price_toman"] == "5900000"
        assert large["price_source"] == "MAX_CALCULATED"
        assert large["final_price_toman"] == 5_900_000
        assert large["regular_price_toman"] == 5_900_000
        assert "sale_price_toman" not in large

        missing_weight = by_id[3639]
        assert missing_weight["sku"] == "NM-3639"
        assert missing_weight["price_source"] == "EXCEL_ONLY"
        assert missing_weight["final_price_toman"] == 7_700_000

        unknown = by_id[3636]
        assert unknown["category"] == "rings"
        assert "UNKNOWN_CATEGORY_DEFAULTED_TO_RINGS" in unknown["review_flags"]
        assert unknown["stock"] == 5
        assert "STOCK_FRACTION_FLOORED" in unknown["review_flags"]
        assert unknown["price_source"] == "MAX_CALCULATED"
        assert unknown["final_price_toman"] == 1_300_000
    print("PASS: mixed digits, SKU priority, category mapping, stock, and Decimal pricing")


def test_weight_reconciliation_live_fill_and_excel_mismatch() -> None:
    fixtures = json.loads(SPEC_FIXTURE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temporary:
        excel = Path(temporary) / "products.xlsx"
        make_excel(excel)
        records, _ = pipeline.load_excel_records(excel)
        by_id = {record["legacy_id"]: record for record in records}

        live_specs = pipeline.parse_spec_block_text(fixtures[0]["text"])
        filled = pipeline.apply_specs_to_record(by_id[3643], live_specs)
        assert filled["excel_weight_grams"] is None
        assert filled["weight_source"] == "LIVE_PAGE"
        assert filled["weight_grams"] == "16"
        assert filled["computed_price_toman"] == "10400000"
        assert filled["final_price_toman"] == 10_400_000
        assert filled["price_source"] == "MAX_CALCULATED"
        assert filled["description_source"] == "SPECS_TEMPLATE"
        assert filled["description"].startswith("انگشتر نقره\n")
        assert "کد مدل: 1058" in filled["description"]
        assert "انگشتر نقره کد 1058\n" not in filled["description"]
        assert "PRICE_RECALCULATED_FROM_LIVE_WEIGHT" in filled["review_flags"]
        assert "SPEC_CATEGORY_MISMATCH" in filled["review_flags"]
        assert filled["category"] == "rings"
        report_row = pipeline._report_row(filled)
        assert report_row["stone_type"] == "حدید"
        assert report_row["stone_color"] == "طلایی"
        assert report_row["band_type"] == "نقره ماشینی"
        assert report_row["silver_purity"] == "925"
        assert report_row["spec_weight"] == "16"
        assert report_row["weight_source"] == "LIVE_PAGE"
        assert report_row["description_source"] == "SPECS_TEMPLATE"

        mismatch_specs = pipeline.parse_spec_block_text(fixtures[1]["text"])
        mismatch = pipeline.apply_specs_to_record(by_id[3641], mismatch_specs)
        assert mismatch["excel_weight_grams"] == "1.0"
        assert mismatch["weight_source"] == "EXCEL"
        assert mismatch["weight_grams"] == "1.0"
        assert mismatch["spec_weight_grams"] == "13"
        assert mismatch["final_price_toman"] == 1_000_000
        assert "WEIGHT_MISMATCH" in mismatch["review_flags"]
        assert mismatch["radman_requires_review"] == "YES"
    print("PASS: live weight fills Excel blanks; Excel weight stays authoritative with mismatch flag")


def test_sku_edge_cases_and_rounding() -> None:
    assert pipeline.derive_sku("انگشتر کد ۱۰۵۹", "9999", 50).sku == "1059"
    assert pipeline.derive_sku("بدون کد", "۹۹۹۹", 50).sku == "9999"
    fallback = pipeline.derive_sku("بدون کد", "2079000.0000000002", 3643)
    assert fallback.sku == "NM-3643"
    assert fallback.source == "FALLBACK_LEGACY_ID"
    assert pipeline.derive_sku("بدون کد", 1058.0, 51).sku == "NM-51"

    max_calculated = pipeline.calculate_pricing(
        title="انگشتر نقره",
        excel_price="۱٬۰۰۰٬۰۰۰",
        pre_discount_price=None,
        weight=Decimal("2.01"),
    )
    assert max_calculated.rate_used == 650_000
    assert max_calculated.computed_price_toman == Decimal("1306500.00")
    assert max_calculated.final_price_toman == 1_350_000
    assert max_calculated.price_source == "MAX_CALCULATED"

    missing = pipeline.calculate_pricing(
        title="انگشتر",
        excel_price=1_001_000,
        pre_discount_price=None,
        weight=None,
    )
    assert missing.price_source == "EXCEL_ONLY"
    assert missing.final_price_toman == 1_050_000

    large = pipeline.calculate_pricing(
        title="انگشتر با عقیق بزرگ",
        excel_price=5_000_000,
        pre_discount_price=None,
        weight=Decimal("10"),
    )
    assert large.stone_class == "large_stone"
    assert large.rate_used == 590_000
    assert large.final_price_toman == 5_900_000
    print("PASS: title/column/fallback SKUs and all owner-approved pricing branches")


def test_selection_descending_filters_and_cap() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        excel = Path(temporary) / "products.xlsx"
        make_excel(excel)
        records, _ = pipeline.load_excel_records(excel)
        selected, summary = pipeline.select_newest(records, 4)
        assert [record["legacy_id"] for record in selected] == [3643, 3642, 3641, 3640]
        assert summary == {
            "excel_rows": 8,
            "inactive_skipped": 1,
            "unavailable_skipped": 1,
            "eligible_rows": 6,
            "selected_rows": 4,
        }
        all_selected, _ = pipeline.select_newest(records, 1000)
        assert [record["legacy_id"] for record in all_selected] == [
            3643,
            3642,
            3641,
            3640,
            3639,
            3636,
        ]
        assert all(record["legacy_id"] not in {3638, 3637} for record in all_selected)
    assert pipeline.map_category("انگشتر های خطی")[0] == "rings"
    assert pipeline.map_category("مدال عقیق")[0] == "necklaces"
    assert pipeline.map_category("دستبند مردانه")[0] == "bracelets"
    print("PASS: ID-desc newest selection, eligibility filters, cap, and category rules")


class FakeDiscoveryFetcher:
    def __init__(self) -> None:
        self.loaded = False
        self.calls = []

    def load_robots(self):
        self.loaded = True

    def fetch_text(self, url):
        assert self.loaded
        self.calls.append(url)
        if "/search?q=3643" in url:
            return '<a href="/product/3643/slug-fa/">product</a>'
        if "/product/3643/slug-fa/" in url:
            return (
                '<h2>مشخصات</h2><p>وزن:16 گرم · نوع سنگ:حدید · عیار نقره:925</p>'
                '<img src="/product-images/3643-main.jpg">'
            )
        return "<html></html>"


def test_discovery_uses_direct_then_search_and_logs_strategy() -> None:
    fetcher = FakeDiscoveryFetcher()
    discovery = pipeline.LegacyImageDiscovery(fetcher=fetcher)
    page = discovery.discover(3643)
    assert page.strategy == "SITE_SEARCH"
    assert page.url == "https://noghrehmashhad.ir/product/3643/slug-fa/"
    assert page.image_urls == (
        "https://noghrehmashhad.ir/product-images/3643-main.jpg",
    )
    assert page.specs.stone_type == "حدید"
    assert page.specs.weight_grams == Decimal("16")
    assert fetcher.calls.count(page.url) == 1
    assert fetcher.calls[0] == "https://noghrehmashhad.ir/product/3643/"
    assert any(item["strategy"] == "SITE_SEARCH" and item["status"] == "FOUND" for item in discovery.log)
    print("PASS: one resolved-page response yields both gallery and specs with logged strategy")


class FakeSKUSearchFetcher:
    def __init__(self) -> None:
        self.loaded = False
        self.calls = []

    def load_robots(self):
        self.loaded = True

    def fetch_text(self, url):
        assert self.loaded
        self.calls.append(url)
        if url == "https://noghrehmashhad.ir/?s=1057":
            return """
              <a href="/product/3643/دستبند-قدیمی-کد-9999/">دستبند کد 9999</a>
              <a href="/product/9999/انگشتر-عقیق-کد-1057/">انگشتر عقیق سیاه کد 1057</a>
            """
        if "/product/9999/" in url:
            return LIVE_HTML_FIXTURE.read_text(encoding="utf-8")
        raise AssertionError(f"unexpected fetch: {url}")


def test_sku_search_selects_best_result_then_fetches_actual_product_page() -> None:
    fetcher = FakeSKUSearchFetcher()
    discovery = pipeline.LegacyImageDiscovery(fetcher=fetcher)
    page = discovery.discover_specs(3643, "1057", "انگشتر عقیق سیاه")
    assert fetcher.calls[0] == "https://noghrehmashhad.ir/?s=1057"
    assert page.url == "https://noghrehmashhad.ir/product/9999/انگشتر-عقیق-کد-1057/"
    assert page.strategy == "SKU_SEARCH"
    assert page.specs.technical_count >= 5
    assert page.specs.model_code == "1057"
    assert all("?s=1057" not in item.get("url", "") for item in discovery.log if item.get("status") == "FOUND")
    assert any(
        item.get("strategy") == "SKU_SEARCH_RESULTS"
        and item.get("candidate_count") == 2
        for item in discovery.log
    )
    print("PASS: SKU search scores title/URL, then extracts only from the actual product page")


def test_gallery_extraction_is_original_ordered_and_image_only() -> None:
    page = "https://noghrehmashhad.ir/product/3643/محصول/"
    source = """
<html><head><meta property="og:image" content="/product-images/3643-main-300x300.jpg"></head>
<body>
<img src="/assets/logo.png">
<img data-large_image="/product-images/3643-main.jpg" src="/product-images/3643-main-150x150.jpg">
<img srcset="/product-images/3643-side-300x300.jpg 300w, /product-images/3643-side.jpg 1600w">
<a href="/product-images/3643-detail.jpg"><img src="/product-images/3643-detail-300x300.jpg"></a>
</body></html>
"""
    images = pipeline.extract_gallery_urls(page, source)
    assert images == [
        "https://noghrehmashhad.ir/product-images/3643-main.jpg",
        "https://noghrehmashhad.ir/product-images/3643-side.jpg",
        "https://noghrehmashhad.ir/product-images/3643-detail.jpg",
    ]
    assert all("logo" not in value and "300x300" not in value for value in images)
    print("PASS: gallery parser keeps ordered original-quality same-host image URLs")


class FakeGateway:
    def __init__(self, existing_ids=None, sku_conflicts=None, existing_rows=None) -> None:
        self.existing_ids = dict(existing_ids or {})
        self.sku_conflicts = dict(sku_conflicts or {})
        self.existing_rows = list(existing_rows or [])
        self.created = []
        self.images = []
        self.enrich_calls = []

    def get_currency(self):
        return "IRT"

    def list_draft_legacy_products(self, limit):
        return [dict(row) for row in self.existing_rows[:limit]]

    def find_by_legacy_id(self, legacy_id):
        return self.existing_ids.get(str(legacy_id))

    def find_product_id(self, sku):
        return self.sku_conflicts.get(sku)

    def resolve_category_id(self, category):
        return {"rings": 17, "necklaces": 18, "bracelets": 19}[category]

    def create_excel_draft(self, record, category_id):
        product_id = 9000 + len(self.created)
        self.created.append((record["legacy_id"], record["sku"], category_id))
        self.existing_ids[str(record["legacy_id"])] = product_id
        return product_id

    def import_image(self, path, title, product_id, sku):
        self.images.append((str(path), title, product_id, sku))
        return 7000 + len(self.images)

    def set_product_images(self, product_id, image_ids):
        raise AssertionError("missing-image test must not attach media")

    def enrich_existing_draft(self, record, product_id, *, update_price):
        self.enrich_calls.append(
            {
                "product_id": product_id,
                "public_title": record["title"],
                "sku": record["sku"],
                "legacy_original_title": record.get("legacy_original_title"),
                "legacy_identity_key": record.get("legacy_identity_key"),
                "description": record["description"],
                "short_description": record.get("short_description", ""),
                "spec_dimensions": record.get("spec_dimensions", ""),
                "specs_found_count": record.get("specs_found_count", 0),
                "legacy_specs": json.dumps(
                    record.get("legacy_specs", {}), ensure_ascii=False, sort_keys=True
                ),
                "update_price": update_price,
            }
        )
        return {
            "id": product_id,
            "status": "draft",
            "price_updated": update_price,
            "sale_meta_after_cleanup": "",
        }


def test_existing_draft_title_cleanup_preserves_sku_and_traceability() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        excel = Path(temporary) / "products.xlsx"
        make_excel(excel)
        records, _ = pipeline.load_excel_records(excel)
    gateway = FakeGateway(
        existing_rows=[
            {
                "product_id": 65,
                "legacy_id": "3643",
                "public_title": "انگشتر نقره کد 1058",
                "sku": "9999",
                "legacy_raw_code": "2079000.0000000002",
                "legacy_url": "https://noghrehmashhad.ir/product/3643/slug/",
                "legacy_original_title": "",
                "legacy_identity_key": "",
                "title_cleanup_status": "",
                "title_cleanup_timestamp": "",
                "review_flags": "",
                "price": "7700000",
                "regular_price": "7700000",
            }
        ]
    )
    matched, missing = pipeline.prepare_existing_enrichment(records, gateway, 20)
    assert missing == []
    assert len(matched) == 1
    record = matched[0]
    assert record["wordpress_product_id"] == 65
    assert record["old_public_title"] == "انگشتر نقره کد 1058"
    assert record["new_public_title"] == "انگشتر نقره"
    assert record["title"] == "انگشتر نقره"
    assert record["sku"] == "9999"
    assert record["current_sku"] == "9999"
    assert record["extracted_title_code"] == "1058"
    assert record["sku_title_match"] == "NO"
    assert "SKU_TITLE_MISMATCH" in record["review_flags"]
    assert record["legacy_original_title"] == "انگشتر نقره کد 1058"
    assert record["raw_code"] == "2079000.0000000002"
    assert record["legacy_url"].endswith("/product/3643/slug/")
    assert record["legacy_identity_key"] == "3643:9999"
    assert record["legacy_title_cleanup_status"] == "REVIEW"
    assert gateway.created == []
    print("PASS: existing Draft title cleans in place; mismatched SKU stays unchanged and flagged")


def test_exact_twenty_existing_drafts_update_without_recreation() -> None:
    specs = pipeline.extract_legacy_specs(
        LIVE_HTML_FIXTURE.read_text(encoding="utf-8")
    )
    records = []
    for index in range(20):
        sku = str(1057 + index)
        source = {
            "wordpress_product_id": 500 + index,
            "legacy_id": 3643 - index,
            "sku": sku,
            "title": f"انگشتر نقره نمونه {index + 1}",
            "category": "rings",
            "category_raw": "انگشتر مردانه",
            "excel_weight_grams": None,
            "excel_price_toman": 4_000_000,
            "pre_discount_price_toman": None,
            "final_price_toman": 4_000_000,
            "regular_price_toman": 4_000_000,
            "wordpress_current_price": 7_700_000,
            "review_flags": [],
        }
        records.append(pipeline.apply_specs_to_record(source, specs))
    gateway = FakeGateway()
    actions = pipeline.enrich_existing_records(records, gateway)
    assert len(actions) == len(gateway.enrich_calls) == 20
    assert gateway.created == []
    assert all(action["action"] == "ENRICHED_DRAFT" for action in actions)
    assert all(action["sale_meta_after_cleanup"] == "" for action in actions)
    assert all(call["update_price"] is False for call in gateway.enrich_calls)
    assert all(call["specs_found_count"] >= 5 for call in gateway.enrich_calls)
    for call in gateway.enrich_calls:
        assert call["short_description"]
        assert "0912" not in call["description"]
        assert "نمایش کمتر" not in call["description"]
        assert "پست پیشتاز" not in call["description"]
        assert "موجودی محدود" not in call["description"]
    print("PASS: exact 20 existing Drafts update in place with zero product recreation")


def test_enrich_existing_is_idempotent_and_price_update_is_targeted() -> None:
    fixture = json.loads(SPEC_FIXTURE.read_text(encoding="utf-8"))[0]
    specs = pipeline.parse_spec_block_text(fixture["text"])
    with tempfile.TemporaryDirectory() as temporary:
        excel = Path(temporary) / "products.xlsx"
        make_excel(excel)
        records, _ = pipeline.load_excel_records(excel)
        base = next(record for record in records if record["legacy_id"] == 3643)
    enriched = pipeline.apply_specs_to_record(base, specs)
    enriched["wordpress_product_id"] = 77
    enriched["wordpress_current_price"] = 7_700_000
    gateway = FakeGateway()
    first = pipeline.enrich_existing_records([dict(enriched)], gateway)
    assert first[0]["price_updated"] is True

    rerun_record = dict(enriched)
    rerun_record["wordpress_current_price"] = enriched["final_price_toman"]
    second = pipeline.enrich_existing_records([rerun_record], gateway)
    assert second[0]["price_updated"] is False
    assert gateway.enrich_calls[0]["description"] == gateway.enrich_calls[1]["description"]
    assert gateway.enrich_calls[0]["legacy_specs"] == gateway.enrich_calls[1]["legacy_specs"]
    assert gateway.enrich_calls[0]["public_title"] == gateway.enrich_calls[1]["public_title"]
    assert gateway.enrich_calls[0]["sku"] == gateway.enrich_calls[1]["sku"] == "1058"
    assert gateway.enrich_calls[0]["legacy_original_title"] == "انگشتر نقره کد 1058"
    assert gateway.enrich_calls[0]["legacy_identity_key"] == "3643:1058"
    assert gateway.enrich_calls[0]["update_price"] is True
    assert gateway.enrich_calls[1]["update_price"] is False
    assert first[0]["sale_meta_after_cleanup"] == second[0]["sale_meta_after_cleanup"] == ""

    lower = dict(enriched)
    lower["wordpress_current_price"] = 20_000_000
    lower_actions = pipeline.enrich_existing_records([lower], gateway)
    assert lower_actions[0]["price_updated"] is False
    assert lower["regular_price_toman"] == 20_000_000
    assert "PRICE_REDUCTION_BLOCKED" in lower["review_flags"]

    excel_only_higher = dict(enriched)
    excel_only_higher["wordpress_current_price"] = 9_000_000
    excel_only_higher["live_weight_floor_toman"] = 8_000_000
    excel_only_higher["final_price_toman"] = 12_000_000
    excel_only_higher["regular_price_toman"] = 12_000_000
    no_floor_raise = pipeline.enrich_existing_records([excel_only_higher], gateway)
    assert no_floor_raise[0]["price_updated"] is False
    print("PASS: price rises only when live-weight floor beats current; sale price stays empty")


def test_image_missing_still_importable_and_conflicts_skip() -> None:
    record = {
        "excel_row": 2,
        "legacy_id": 3643,
        "sku": "1058",
        "title": "انگشتر کد 1058",
        "description": "توضیح",
        "category": "rings",
        "category_raw": "انگشتر",
        "raw_code": "2079000.0000000002",
        "weight_grams": None,
        "price_source": "EXCEL_ONLY",
        "rate_used": 650000,
        "computed_price_toman": None,
        "final_price_toman": 7_700_000,
        "excel_price_toman": 7_689_000,
        "pre_discount_price_toman": 8_000_000,
        "regular_price_toman": 7_700_000,
        "stone_class": "uncertain",
        "stock": 2,
        "image_status": "MISSING",
        "image_discovery_strategy": "NOT_FOUND",
        "selected_import_paths": [],
        "review_flags": ["IMAGES_MISSING"],
        "action": "READY_DRAFT",
        "legacy_url": "",
    }
    gateway = FakeGateway()
    actions = pipeline.import_records([record], gateway)
    assert actions[0]["action"] == "CREATED_DRAFT"
    assert gateway.created == [(3643, "1058", 17)]
    assert gateway.images == []
    assert record["image_status"] == "MISSING"

    conflict = dict(record)
    conflict["legacy_id"] = 3642
    conflict["action"] = "READY_DRAFT"
    conflict_gateway = FakeGateway(sku_conflicts={"1058": 44})
    conflict_actions = pipeline.import_records([conflict], conflict_gateway)
    assert conflict_actions[0]["action"] == "SKIP_SKU_CONFLICT"
    assert conflict_gateway.created == []

    existing = dict(record)
    existing["action"] = "READY_DRAFT"
    existing_gateway = FakeGateway(existing_ids={"3643": 77})
    existing_actions = pipeline.import_records([existing], existing_gateway)
    assert existing_actions[0]["action"] == "SKIP_EXISTING_LEGACY_ID"
    assert existing_gateway.created == []
    print("PASS: no-image Draft imports; SKU/legacy conflicts skip without overwrite")


def test_read_only_identity_report_columns() -> None:
    rows = [
        {
            "product_id": 65,
            "public_title": "انگشتر نقره",
            "sku": "1058",
            "legacy_id": "3642",
            "legacy_raw_code": "1058",
            "legacy_url": "https://noghrehmashhad.ir/product/3642/slug/",
            "legacy_identity_key": "3642:1058",
            "title_cleanup_status": "CLEANED",
            "review_flags": "",
        }
    ]
    with tempfile.TemporaryDirectory() as temporary:
        csv_path, txt_path = pipeline.write_identity_report(rows, Path(temporary))
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            report = list(csv.DictReader(handle))
        assert report == [
            {
                "wp_id": "65",
                "public_title": "انگشتر نقره",
                "sku": "1058",
                "legacy_product_id": "3642",
                "legacy_raw_code": "1058",
                "legacy_url": "https://noghrehmashhad.ir/product/3642/slug/",
                "identity_key": "3642:1058",
                "title_cleanup_status": "CLEANED",
                "review_flags": "",
            }
        ]
        assert "3642:1058" in txt_path.read_text(encoding="utf-8")
    print("PASS: identity-report emits complete read-only SKU/legacy reconciliation fields")


def test_runner_plan_and_static_safety() -> None:
    runner = REPO_ROOT / "scripts" / "run_excel_import.sh"
    pipeline_source = (HERE / "agent_excel_product_pipeline.py").read_text(
        encoding="utf-8"
    )
    runner_source = runner.read_text(encoding="utf-8")
    subprocess.run(["bash", "-n", str(runner)], check=True)
    subprocess.run(["bash", "--posix", "-n", str(runner)], check=True)
    assert "set_status('draft')" in pipeline_source
    assert "set_status('publish')" not in pipeline_source
    assert "set_sale_price" not in pipeline_source
    assert "delete_post_meta($id, '_sale_price')" in pipeline_source
    assert "update_post_meta($id, '_price', $luxury_regular)" in pipeline_source
    enrichment_source = pipeline_source.split("def enrich_existing_draft", 1)[1].split(
        "def create_excel_draft", 1
    )[0]
    assert "$p->set_description($d['description']);" in enrichment_source
    assert "$p->set_short_description($d['short_description']);" in enrichment_source
    for forbidden_setter in (
        "set_name(",
        "set_sku(",
        "set_status(",
        "set_stock_quantity(",
        "set_category_ids(",
        "set_image_id(",
        "set_gallery_image_ids(",
    ):
        assert forbidden_setter not in enrichment_source
    assert "wp_delete_post" not in pipeline_source
    for protected_meta_write in (
        '"legacy_product_id":',
        '"legacy_raw_code":',
        '"legacy_original_title":',
        '"legacy_identity_key":',
        '"legacy_title_cleanup_status":',
    ):
        assert protected_meta_write not in enrichment_source
    for meta_key in (
        "radman_legacy_specs",
        "radman_spec_stone_type",
        "radman_spec_stone_color",
        "radman_spec_band_type",
        "radman_spec_engraving_type",
        "radman_spec_silver_purity",
        "radman_spec_dimensions",
        "radman_spec_size",
        "radman_spec_model_code",
        "radman_spec_status",
        "radman_spec_count",
        "radman_spec_weight_grams",
        "radman_spec_weight_display",
        "radman_requires_review",
        "radman_legacy_code",
        "legacy_original_title",
        "legacy_identity_key",
        "legacy_title_cleanup_status",
        "legacy_title_cleanup_timestamp",
    ):
        assert meta_key in pipeline_source
    assert "amount // 10" not in pipeline_source
    assert "public_html" in runner_source
    assert "--api-probe" not in runner_source
    assert "API] DEFERRED" in runner_source
    assert "--enrich-existing" in runner_source
    assert "--identity-report" in runner_source
    for prohibited in ("remove" + "bg", "BR" + "IA", "BiRef" + "Net"):
        assert prohibited.casefold() not in pipeline_source.casefold()

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        excel = root / "products.xlsx"
        private = root / "private"
        make_excel(excel)
        environment = os.environ.copy()
        environment["MAX_PRODUCTS"] = "5"
        environment["EXCEL_FILE"] = str(excel)
        environment["RADMAN_PRIVATE_DIR"] = str(private)
        result = subprocess.run(
            ["bash", str(runner), "--plan"],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "[API] DEFERRED" in result.stdout
        assert "HTML product pages are the primary spec source" in result.stdout
        assert "SELECTION + PRICING PREVIEW" in result.stdout
        assert "PLAN PREVIEW ONLY" in result.stdout
        manifests = list(
            (private / "legacy-cache" / "runs").glob(
                "excel-import-*/prepared-products.json"
            )
        )
        assert len(manifests) == 1
        payload = json.loads(manifests[0].read_text(encoding="utf-8"))
        assert payload["sort"] == "legacy_id DESC"
        assert payload["spec_source"] == "HTML_PRODUCT_PAGE_PRIMARY_API_DEFERRED"
        assert [row["legacy_id"] for row in payload["products"]] == [
            3643,
            3642,
            3641,
            3640,
            3639,
        ]
        assert all(row["image_status"] == "NOT_FETCHED" for row in payload["products"])
        csv_reports = list(manifests[0].parent.glob("excel-import-*.csv"))
        assert len(csv_reports) == 1
        with csv_reports[0].open("r", encoding="utf-8-sig", newline="") as handle:
            report_rows = list(csv.DictReader(handle))
        assert len(report_rows) == 5
        assert {
            "stone_type",
            "stone_color",
            "band_type",
            "silver_purity",
            "spec_weight",
            "weight_source",
            "description_source",
            "unknown_spec_labels_seen",
            "wp_id",
            "old_public_title",
            "new_public_title",
            "title_cleanup_applied",
            "extracted_title_code",
            "current_sku",
            "sku_title_match",
            "legacy_product_id",
            "legacy_raw_code",
            "identity_key",
            "title_cleanup_status",
            "description_updated",
            "specs_found_count",
            "price_changed",
        }.issubset(report_rows[0])
        assert report_rows[0]["legacy_id"] == "3643"
        assert report_rows[0]["new_public_title"] == "انگشتر نقره"
        assert report_rows[0]["extracted_title_code"] == "1058"
        assert report_rows[0]["identity_key"] == "3643:1058"
        assert report_rows[0]["sku_source"] == "TITLE_CODE"
        assert report_rows[1]["sku"] == "NM-3642"
        assert report_rows[3]["stone_class"] == "large_stone"
        assert report_rows[3]["final_price_toman"] == "5900000"
        try:
            pipeline.read_manifest(manifests[0], private)
            raise AssertionError("plan-only manifest must not be importable")
        except pipeline.ExcelPipelineError as exc:
            assert "--fetch-images" in str(exc)

        unsafe = environment.copy()
        for key in ("APP_ENV", "WP_URL", "WP_PATH", "CONFIRM_STAGING_APPLY"):
            unsafe.pop(key, None)
        for unsafe_mode in (
            "--import-drafts",
            "--enrich-existing",
            "--identity-report",
        ):
            rejected = subprocess.run(
                ["bash", str(runner), unsafe_mode],
                cwd=REPO_ROOT,
                env=unsafe,
                capture_output=True,
                text=True,
            )
            assert rejected.returncode != 0
    print("PASS: plan is offline/no-WP; guards declare API deferred and HTML primary")


def main() -> int:
    test_real_spec_block_fixtures_and_html_section_parser()
    test_unique_descriptions_differ_and_omit_missing_fields()
    test_excel_parsing_sku_pricing_and_categories()
    test_weight_reconciliation_live_fill_and_excel_mismatch()
    test_sku_edge_cases_and_rounding()
    test_selection_descending_filters_and_cap()
    test_discovery_uses_direct_then_search_and_logs_strategy()
    test_sku_search_selects_best_result_then_fetches_actual_product_page()
    test_gallery_extraction_is_original_ordered_and_image_only()
    test_existing_draft_title_cleanup_preserves_sku_and_traceability()
    test_exact_twenty_existing_drafts_update_without_recreation()
    test_enrich_existing_is_idempotent_and_price_update_is_targeted()
    test_image_missing_still_importable_and_conflicts_skip()
    test_read_only_identity_report_columns()
    test_runner_plan_and_static_safety()
    print("ALL EXCEL PRODUCT PIPELINE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
