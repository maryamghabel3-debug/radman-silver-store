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
        assert title_code["raw_code"] == "2079000.0000000002"
        assert title_code["category"] == "rings"
        assert title_code["excel_price_toman"] == 7_689_000
        assert title_code["weight_grams"] is None
        assert title_code["price_source"] == "EXCEL_ONLY"
        assert title_code["final_price_toman"] == 7_700_000
        assert title_code["regular_price_toman"] == 8_000_000
        assert title_code["sale_price_toman"] == 7_700_000

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
        assert persian_code["regular_price_toman"] == 1_200_000
        assert persian_code["sale_price_toman"] == 1_000_000

        large = by_id[3640]
        assert large["stone_class"] == "large_stone"
        assert large["rate_used"] == 590_000
        assert large["computed_price_toman"] == "5900000"
        assert large["price_source"] == "MAX_CALCULATED"
        assert large["final_price_toman"] == 5_900_000
        assert large["regular_price_toman"] == 5_900_000
        assert large["sale_price_toman"] is None

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
            return '<img src="/product-images/3643-main.jpg">'
        return "<html></html>"


def test_discovery_uses_direct_then_search_and_logs_strategy() -> None:
    fetcher = FakeDiscoveryFetcher()
    discovery = pipeline.LegacyImageDiscovery(fetcher=fetcher)
    url, images, strategy = discovery.discover(3643)
    assert strategy == "SITE_SEARCH"
    assert url == "https://noghrehmashhad.ir/product/3643/slug-fa/"
    assert images == [
        "https://noghrehmashhad.ir/product-images/3643-main.jpg"
    ]
    assert fetcher.calls[0] == "https://noghrehmashhad.ir/product/3643/"
    assert any(item["strategy"] == "SITE_SEARCH" and item["status"] == "FOUND" for item in discovery.log)
    print("PASS: image discovery tries direct ID patterns before site search and logs success")


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
    def __init__(self, existing_ids=None, sku_conflicts=None) -> None:
        self.existing_ids = dict(existing_ids or {})
        self.sku_conflicts = dict(sku_conflicts or {})
        self.created = []
        self.images = []

    def get_currency(self):
        return "IRT"

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
        "regular_price_toman": 8_000_000,
        "sale_price_toman": 7_700_000,
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
    assert "amount // 10" not in pipeline_source
    assert "public_html" in runner_source
    assert "LEGACY_API_ENV=/home/radmansi/.config/radman/api-keys/legacy-site.env" in runner_source
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
        assert "[API SLOT] /home/radmansi/.config/radman/api-keys/legacy-site.env" in result.stdout
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
        assert report_rows[0]["legacy_id"] == "3643"
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
        rejected = subprocess.run(
            ["bash", str(runner), "--import-drafts"],
            cwd=REPO_ROOT,
            env=unsafe,
            capture_output=True,
            text=True,
        )
        assert rejected.returncode != 0
    print("PASS: plan is offline/no-WP; Bash/POSIX, guards, API slot, and newest ordering")


def main() -> int:
    test_excel_parsing_sku_pricing_and_categories()
    test_sku_edge_cases_and_rounding()
    test_selection_descending_filters_and_cap()
    test_discovery_uses_direct_then_search_and_logs_strategy()
    test_gallery_extraction_is_original_ordered_and_image_only()
    test_image_missing_still_importable_and_conflicts_skip()
    test_runner_plan_and_static_safety()
    print("ALL EXCEL PRODUCT PIPELINE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
