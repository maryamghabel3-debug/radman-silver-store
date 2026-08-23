#!/usr/bin/env python3
"""Offline PR-25 tests: pricing, mock-10 scrape, media QA, and draft safety."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

import agent_gemstone_classifier as classifier  # noqa: E402
import agent_legacy_catalog_pilot as catalog  # noqa: E402
import agent_original_image_processor as image_processor  # noqa: E402
import agent_original_product_pipeline as pipeline  # noqa: E402
from lib.legacy_identity import duplicate_codes, map_legacy_code_to_sku  # noqa: E402
from lib.legacy_pricing import calculate_safe_price, parse_toman  # noqa: E402


def test_decimal_pricing() -> None:
    large = calculate_safe_price(
        category="rings",
        stone_class="large_stone",
        stone_confidence="0.85",
        weight_grams="10",
        legacy_price_toman="5,000,000",
    )
    assert large.rate_toman_per_gram == 590_000
    assert large.calculated_price_toman == 5_900_000
    assert large.final_price_toman == 5_900_000
    assert large.selection_reason == "CALCULATED_FLOOR_HIGHER"

    low_confidence = calculate_safe_price(
        category="rings",
        stone_class="large_stone",
        stone_confidence="0.849",
        weight_grams="10",
        legacy_price_toman="5,000,000",
    )
    assert low_confidence.rate_toman_per_gram == 650_000
    assert low_confidence.effective_stone_class == "uncertain"
    assert low_confidence.requires_review

    necklace = calculate_safe_price(
        category="necklaces",
        stone_class="large_stone",
        stone_confidence="0.99",
        weight_grams="10",
        legacy_price_toman="7,001,000",
    )
    assert necklace.rate_toman_per_gram == 650_000
    assert necklace.selection_reason == "LEGACY_PRICE_HIGHER"
    assert necklace.final_price_toman == 7_001_000

    assert parse_toman("۱۲٬۳۴۵٬۶۷۸ تومان") == 12_345_678
    assert parse_toman("12345678") == 12_345_678
    mislabeled, mislabeled_source = catalog._price_from_jsonld(
        {"offers": {"price": "12345678", "priceCurrency": "IRR"}}
    )
    assert mislabeled == 12_345_678
    assert "amount_toman" in mislabeled_source
    print("PASS: exact Decimal Toman floors, conservative rate, and max selection")


def test_legacy_identity_mapping() -> None:
    exact = map_legacy_code_to_sku("AB-12.7")
    assert exact.sku == "AB-12.7"
    assert exact.legacy_code_raw == "AB-12.7"
    assert not exact.normalization_required

    localized = map_legacy_code_to_sku("۱۲۳۴")
    assert localized.legacy_code_raw == "۱۲۳۴"
    assert localized.sku == "1234"
    assert localized.normalization_required

    generated_a = map_legacy_code_to_sku("کد ویژه/الف")
    generated_b = map_legacy_code_to_sku("کد ویژه/الف")
    assert generated_a.sku == generated_b.sku
    assert generated_a.sku.startswith("LEGACY-")
    assert duplicate_codes([exact, exact]) == {"ab-12.7"}
    print("PASS: exact valid legacy codes and deterministic normalization/mapping")


def test_classifier_text_and_multi_image() -> None:
    no_stone = classifier.classify_product(
        category="rings", title="انگشتر مردانه بدون نگین"
    )
    assert no_stone.stone_class == "no_stone" and no_stone.confidence >= 0.9
    large = classifier.classify_product(
        category="rings", description="این انگشتر دارای نگین درشت عقیق است"
    )
    assert large.stone_class == "large_stone" and large.confidence >= 0.85
    generic = classifier.classify_product(category="rings", title="انگشتر عقیق")
    assert generic.stone_class == "uncertain" and generic.requires_review
    nonring = classifier.classify_product(category="bracelets", title="دستبند سنگی")
    assert nonring.stone_class == "uncertain" and not nonring.requires_review

    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for index in range(2):
            path = Path(tmp) / f"view-{index}.png"
            image = Image.new("RGB", (256, 256), "#dadada")
            ImageDraw.Draw(image).ellipse((110, 110, 146, 146), fill="#134fd1")
            image.save(path)
            paths.append(path)
        visual = classifier.classify_product(category="rings", image_paths=paths)
        assert visual.stone_class == "large_stone"
        assert visual.confidence >= 0.85
    print("PASS: text-first conservative classifier and deterministic multi-view evidence")


def _sample_image(path: Path, size=(2000, 1000)) -> None:
    image = Image.new("RGB", size, "#e8e4df")
    draw = ImageDraw.Draw(image)
    draw.rectangle((300, 200, 1700, 800), fill="#b8b8ba")
    draw.ellipse((850, 350, 1150, 650), fill="#1d56a8")
    draw.line((300, 200, 1700, 800), fill="#666666", width=8)
    image.save(path, quality=98)


def test_original_image_integrity_and_fallback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original = root / "original.jpg"
        output = root / "processed" / "01.webp"
        _sample_image(original)
        before = hashlib.sha256(original.read_bytes()).hexdigest()
        result = image_processor.process_one(original, output, sharpen=False)
        assert result.qa_status == "PASS", result.reasons
        assert result.processed_dimensions == (1600, 800)
        assert result.resize_scale == 0.8
        assert result.selected_import_path == str(output.resolve())
        assert hashlib.sha256(original.read_bytes()).hexdigest() == before
        with Image.open(output) as made:
            assert made.size == (1600, 800)
            assert made.format == "WEBP"

        old_limit = image_processor.MAX_MEAN_ABS_DRIFT
        image_processor.MAX_MEAN_ABS_DRIFT = -1.0
        try:
            failed = image_processor.process_one(
                original, root / "processed" / "forced-fail.webp", sharpen=False
            )
        finally:
            image_processor.MAX_MEAN_ABS_DRIFT = old_limit
        assert failed.qa_status == "FAIL"
        assert failed.fallback_to_original
        assert failed.selected_import_path == str(original.resolve())

        sheet = root / "qa" / "sheet.jpg"
        image_processor.make_qa_sheet((result, failed), sheet)
        assert sheet.is_file()
    print("PASS: no-crop resize, original checksum, color/detail gate, and original fallback")


class MockCatalogFetcher:
    def __init__(self) -> None:
        self.user_agent = catalog.USER_AGENT
        self.min_delay = catalog.MIN_REQUEST_DELAY_SECONDS
        self.loaded = False
        self.image_bytes = self._make_image_bytes()

    @staticmethod
    def _make_image_bytes() -> bytes:
        import io

        buffer = io.BytesIO()
        image = Image.new("RGB", (480, 360), "#efebe6")
        ImageDraw.Draw(image).ellipse((200, 130, 280, 210), fill="#2450a0")
        image.save(buffer, format="JPEG", quality=97)
        return buffer.getvalue()

    def load_robots(self) -> None:
        self.loaded = True

    def fetch_text(self, url: str, check_robots: bool = True) -> str:
        assert self.loaded
        if "/category/" in url:
            category_number = int(url.split("/category/")[1].split("/")[0])
            offset = {2: 0, 71: 4, 17: 8}.get(category_number, 0)
            links = []
            for index in range(1, 5):
                legacy_id = 2000 + offset + index
                links.append(
                    f'<a href="https://noghrehmashhad.ir/product/{legacy_id}/item-{legacy_id}/">item</a>'
                )
            return "<html>" + "".join(links) + "</html>"
        legacy_id = int(url.split("/product/")[1].split("/")[0])
        sequence = legacy_id - 2000
        # ID 2005 intentionally repeats A001. The scraper must skip it and continue.
        code = "A001" if sequence == 5 else f"A{sequence:03d}"
        if sequence <= 4:
            category_slug, category_fa, title = "2/ring", "انگشتر", "انگشتر نگین درشت"
        elif sequence <= 8:
            category_slug, category_fa, title = "71/necklace", "گردنبند", "گردنبند نقره"
        else:
            category_slug, category_fa, title = "17/bracelet", "دستبند", "دستبند نقره"
        return f"""
<html><head><meta name="description" content="توضیح کوتاه {code}"></head><body>
<a href="https://noghrehmashhad.ir/category/{category_slug}/">{category_fa}</a>
<h1>{title} کد {code}</h1>
<div class="price">{2_000_000 + sequence * 100_000:,} تومان</div>
<div>وزن: {5 + sequence / 10:.1f} گرم</div>
<div class="product-description">توضیح کامل محصول با کد {code}</div>
<img src="https://noghrehmashhad.ir/product-images/{legacy_id}-1.jpg">
<img src="https://noghrehmashhad.ir/product-images/{legacy_id}-2.jpg">
</body></html>
"""

    def fetch_bytes(self, url: str, *, max_bytes: int, check_robots: bool = True, timeout: int = 45):
        assert self.loaded and len(self.image_bytes) <= max_bytes
        return self.image_bytes, {"content-type": "image/jpeg"}


def test_mock_ten_product_scrape_and_reports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        private = Path(tmp) / "private"
        manifest = catalog.scrape_original_products(
            private, limit=10, fetcher=MockCatalogFetcher()
        )
        assert manifest["scraped_count"] == 10
        assert len(manifest["products"]) == 10
        assert any(item["reason"] == "DUPLICATE_LEGACY_CODE" for item in manifest["skipped"])
        assert len({item["legacy_code"] for item in manifest["products"]}) == 10
        for product in manifest["products"]:
            assert product["price_source"] == "visible_price_toman"
            assert product["visible_legacy_price_toman"] > 0
            assert product["legacy_code_raw"] == product["sku"]
            assert len(product["original_image_paths"]) == 2
            image_dir = private / "legacy-cache" / "original-images" / product["legacy_id"]
            assert image_dir.is_dir()
            for downloaded in product["downloaded_images"]:
                path = Path(downloaded["local_path"])
                assert path.parent == image_dir
                assert hashlib.sha256(path.read_bytes()).hexdigest() == downloaded["sha256"]

        source_path = Path(manifest["manifest_path"])
        run_dir = private / "legacy-cache" / "runs" / "mock-prepare"
        records = pipeline.prepare_products(
            pipeline.load_products(source_path),
            private_dir=private,
            run_dir=run_dir,
            run_image_qa=True,
        )
        assert len(records) == 10
        for record in records:
            pricing = record["pricing"]
            candidates = [
                value for value in (
                    pricing.get("legacy_price_toman"),
                    pricing.get("calculated_price_toman"),
                ) if value is not None
            ]
            assert pricing["final_price_toman"] == max(candidates)
            assert record["image_qa_status"] in {"PASS", "FAIL"}
            assert len(record["selected_import_paths"]) == 2
            assert record["import_action"] == "CREATE_DRAFT"
        mock_gateway = FakeGateway()
        actions = pipeline.import_drafts(records, gateway=mock_gateway)
        assert len(actions) == 10
        assert all(action["action"] == "CREATED_DRAFT" for action in actions)
        assert len(mock_gateway.created) == 10
        csv_path, summary_path = pipeline.write_reports(
            records, run_dir, manifest["skipped"]
        )
        csv_text = csv_path.read_text(encoding="utf-8-sig")
        assert csv_text.count("\n") == 12
        assert "DUPLICATE_LEGACY_CODE" in csv_text
        summary = summary_path.read_text(encoding="utf-8")
        assert "تومان" in summary and "هیچ تبدیل ریال/تومان" in summary
    print("PASS: mocked ten-product acquisition, per-ID originals, QA, pricing, and reports")


class FakeGateway:
    def __init__(self, *, currency="IRT", existing_legacy=None, sku_conflicts=None) -> None:
        self.currency = currency
        self.existing_legacy = dict(existing_legacy or {})
        self.sku_conflicts = dict(sku_conflicts or {})
        self.created = []
        self.imported = []
        self.image_sets = []

    def get_currency(self):
        return self.currency

    def find_product_id_by_legacy_id(self, legacy_id):
        return self.existing_legacy.get(str(legacy_id))

    def find_product_id(self, sku):
        return self.sku_conflicts.get(sku)

    def resolve_category_id(self, category):
        return {"rings": 17, "necklaces": 18, "bracelets": 19}[category]

    def create_legacy_draft(self, record, category_id):
        self.created.append((record["legacy_id"], record["sku"], category_id))
        product_id = 5000 + len(self.created)
        self.existing_legacy[str(record["legacy_id"])] = product_id
        return product_id

    def import_image(self, path, title, product_id, sku):
        attachment_id = 7000 + len(self.imported)
        self.imported.append((str(path), product_id, sku))
        return attachment_id

    def set_product_images(self, product_id, image_ids):
        self.image_sets.append((product_id, list(image_ids)))


def _import_record(tmp: Path, legacy_id: str, sku: str):
    first = tmp / f"{legacy_id}-01.jpg"
    second = tmp / f"{legacy_id}-02.jpg"
    _sample_image(first, (100, 100))
    _sample_image(second, (100, 100))
    return {
        "legacy_id": legacy_id,
        "legacy_code": sku,
        "legacy_code_raw": sku,
        "sku": sku,
        "category": "rings",
        "title": "محصول",
        "short_description": "کوتاه",
        "description": "کامل",
        "product_url": f"https://noghrehmashhad.ir/product/{legacy_id}/x/",
        "classification": {"stone_class": "uncertain", "confidence": 0.3, "source": "test"},
        "pricing": {
            "weight_grams": "10",
            "legacy_price_toman": 6_000_000,
            "rate_toman_per_gram": 650_000,
            "calculated_price_toman": 6_500_000,
            "final_price_toman": 6_500_000,
            "selection_reason": "CALCULATED_FLOOR_HIGHER",
        },
        "image_qa": {"qa_sheet": "sheet.jpg"},
        "image_qa_status": "PASS",
        "selected_import_paths": [str(first), str(second)],
        "image_integrity_action": "OPTIMIZED_OUTPUT_APPROVED",
        "review_reasons": ["test review"],
        "requires_review": True,
        "import_action": "CREATE_DRAFT",
        "image_urls": [],
    }


def test_create_only_import_idempotency_and_conflict_stop() -> None:
    with tempfile.TemporaryDirectory() as tmp_raw:
        tmp = Path(tmp_raw)
        first = _import_record(tmp, "301", "OLD-301")
        second = _import_record(tmp, "302", "OLD-302")
        gateway = FakeGateway(existing_legacy={"302": 9302})
        actions = pipeline.import_drafts((first, second), gateway=gateway)
        assert [item["action"] for item in actions] == ["CREATED_DRAFT", "SKIP_EXISTING_LEGACY_ID"]
        assert gateway.created == [("301", "OLD-301", 17)]
        assert [Path(call[0]).name for call in gateway.imported] == ["301-01.jpg", "301-02.jpg"]
        assert gateway.image_sets[0][1] == [7000, 7001]

        first["import_action"] = "CREATE_DRAFT"
        rerun = pipeline.import_drafts((first,), gateway=gateway)
        assert rerun[0]["action"] == "SKIP_EXISTING_LEGACY_ID"
        assert len(gateway.created) == 1

        conflict_record = _import_record(tmp, "303", "OLD-303")
        conflict_gateway = FakeGateway(sku_conflicts={"OLD-303": 9999})
        try:
            pipeline.import_drafts((conflict_record,), gateway=conflict_gateway)
            raise AssertionError("SKU conflict should stop the batch")
        except pipeline.PipelineError as exc:
            assert "stopped all mutation" in str(exc)
        assert conflict_gateway.created == []
    print("PASS: create-only drafts skip legacy IDs, preserve media order, and stop on SKU conflicts")


def test_staging_and_backup_guards() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backup = Path(tmp) / "pre-import.sql"
        backup.write_text("-- staging backup", encoding="utf-8")
        keys = {
            "APP_ENV": "staging",
            "WP_URL": "https://staging.radmansilver.ir",
            "CONFIRM_STAGING_APPLY": "YES",
            "RADMAN_DB_BACKUP_PATH": str(backup),
        }
        previous = {key: os.environ.get(key) for key in keys}
        os.environ.update(keys)
        try:
            assert pipeline.require_original_import_environment(
                "/home/radmansi/staging.radmansilver.ir"
            ) == backup
            os.environ["WP_URL"] = "https://radmansilver.ir"
            rejected = False
            try:
                pipeline.require_original_import_environment(
                    "/home/radmansi/staging.radmansilver.ir"
                )
            except Exception:
                rejected = True
            assert rejected, "production URL must be rejected"
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    print("PASS: exact staging confirmation and fresh database backup guards")


def test_safety_source_and_shell() -> None:
    source = (HERE / "agent_original_product_pipeline.py").read_text(encoding="utf-8")
    scraper_source = (HERE / "agent_legacy_catalog_pilot.py").read_text(encoding="utf-8")
    image_source = (HERE / "agent_original_image_processor.py").read_text(encoding="utf-8")
    assert "set_status('draft')" in source
    assert "set_backorders('no')" in source
    assert "_legacy_store_id" in source
    assert '"radman_legacy_id"' in source
    assert '"radman_original_image_sha256"' in source
    assert "set_status('publish')" not in source
    assert "set_status(\"publish\")" not in source
    assert "amount // 10" not in source
    assert "amount // 10" not in scraper_source
    assert "* 10" not in source
    for prohibited in ("remove" + "bg", "BR" + "IA", "BiRef" + "Net"):
        assert prohibited.lower() not in image_source.lower()
    runner = REPO_ROOT / "scripts" / "run_original_product_import.sh"
    subprocess.run(["sh", "-n", str(runner)], check=True)
    plan = subprocess.run(
        [str(runner), "--plan"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    assert "mutation in this command: NONE" in plan.stdout
    assert "public_html" in runner.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        unsafe_env = os.environ.copy()
        for key in ("APP_ENV", "WP_URL", "WP_PATH", "CONFIRM_STAGING_APPLY"):
            unsafe_env.pop(key, None)
        rejected = subprocess.run(
            [str(runner), "--import-drafts", "--private-dir", tmp],
            cwd=REPO_ROOT,
            env=unsafe_env,
            capture_output=True,
            text=True,
        )
        assert rejected.returncode != 0
        assert not (Path(tmp) / "locks").exists()
    print("PASS: draft-only, no currency conversion, approved media path, and POSIX plan safety")


def main() -> int:
    test_decimal_pricing()
    test_legacy_identity_mapping()
    test_classifier_text_and_multi_image()
    test_original_image_integrity_and_fallback()
    test_mock_ten_product_scrape_and_reports()
    test_create_only_import_idempotency_and_conflict_stop()
    test_staging_and_backup_guards()
    test_safety_source_and_shell()
    print("ALL PR-25 OFFLINE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
