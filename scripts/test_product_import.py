#!/usr/bin/env python3
"""Mocked dry-run/apply tests for scripts/import_products.py (no host/WP)."""

from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import import_products as ip


def write_fixture(root: Path) -> tuple[Path, Path, Path]:
    csv_path = root / "products.csv"
    images = root / "images"
    images.mkdir()
    (images / "ring-front.jpg").write_bytes(b"mock-image")
    rate = root / "daily_rate.txt"
    rate.write_text("85000\n", encoding="utf-8")

    rows = [
        {
            "sku": "RAD-RNG-M-1001",
            "title_fa": "انگشتر نقره ساده",
            "category": "rings",
            "weight_grams": "6.80",
            "silver_purity": "925",
            "stone_type": "",
            "stone_value_toman": "",
            "pricing_mode": "silver_weight_only",
            "stock": "",
            "legacy_price_toman": "",
            "manual_price_toman": "",
            "short_description": "نمونه تست وزن‌محور",
            "long_description": "توضیحات تست برای محصول وزن‌محور.",
            "image_filenames": "ring-front.jpg|ring-missing.jpg",
        },
        {
            "sku": "RAD-NEC-U-1002",
            "title_fa": "گردنبند نقره عقیق",
            "category": "necklaces",
            "weight_grams": "5",
            "silver_purity": "925",
            "stone_type": "عقیق",
            "stone_value_toman": "200000",
            "pricing_mode": "silver_weight_plus_stone",
            "stock": "1",
            "legacy_price_toman": "",
            "manual_price_toman": "",
            "short_description": "نمونه تست وزن و نگین",
            "long_description": "توضیحات تست برای محصول وزن و نگین.",
            "image_filenames": "",
        },
        {
            "sku": "RAD-BRC-U-1003",
            "title_fa": "دستبند نقره میراثی",
            "category": "bracelets",
            "weight_grams": "",
            "silver_purity": "925",
            "stone_type": "",
            "stone_value_toman": "",
            "pricing_mode": "legacy_mirror",
            "stock": "1",
            "legacy_price_toman": "1500000",
            "manual_price_toman": "",
            "short_description": "نمونه تست قیمت میراثی",
            "long_description": "توضیحات تست برای محصول با قیمت میراثی.",
            "image_filenames": "",
        },
        {
            "sku": "RAD-RNG-U-1004",
            "title_fa": "انگشتر دست‌ساز ویژه",
            "category": "rings",
            "weight_grams": "12",
            "silver_purity": "925",
            "stone_type": "فیروزه",
            "stone_value_toman": "",
            "pricing_mode": "manual_locked",
            "stock": "1",
            "legacy_price_toman": "",
            "manual_price_toman": "2500000",
            "short_description": "نمونه تست قیمت دستی",
            "long_description": "توضیحات تست برای محصول قفل‌شده دستی.",
            "image_filenames": "",
        },
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ip.CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path, images, rate


class FakeGateway:
    def __init__(self) -> None:
        self.existing = {"RAD-RNG-U-1004": 88}
        self.next_id = 200
        self.upserts = []
        self.imports = []
        self.image_sets = []

    def find_product_id(self, sku: str):
        return self.existing.get(sku)

    def resolve_category_id(self, slug: str) -> int:
        return {"rings": 17, "necklaces": 18, "bracelets": 19}[slug]

    def upsert_product(self, row: ip.ProductRow, category_id: int):
        existing_id = self.existing.get(row.sku)
        created = existing_id is None
        if created:
            product_id = self.next_id
            self.next_id += 1
            self.existing[row.sku] = product_id
        else:
            product_id = existing_id
        self.upserts.append((row.sku, category_id, row.computed_price_toman, created))
        return product_id, created

    def import_image(self, path: Path, title: str, product_id: int, sku: str) -> int:
        self.imports.append((path.name, title, product_id, sku))
        return 901

    def set_product_images(self, product_id: int, image_ids):
        self.image_sets.append((product_id, list(image_ids)))


def run_tests() -> None:
    with tempfile.TemporaryDirectory(prefix="radman-import-test-") as tmp:
        root = Path(tmp)
        csv_path, images, rate = write_fixture(root)
        rows, daily_rate = ip.load_product_rows(csv_path, images, rate)

        assert daily_rate == 85000
        assert len(rows) == 4
        assert [row.computed_price_toman for row in rows] == [580000, 625000, 1500000, 2500000]
        assert rows[0].stock == 1, "blank stock must default to exact stock=1"
        assert [path.name for path in rows[0].present_images] == ["ring-front.jpg"]
        assert rows[0].missing_images == ["ring-missing.jpg"]
        print("PASS: CSV parsing, defaults, image detection, and all 4 pricing modes")

        gateway = FakeGateway()
        ip.inspect_existing(rows, gateway)  # type: ignore[arg-type]
        preview = io.StringIO()
        ip.render_preview(rows, daily_rate, preview)
        text = preview.getvalue()
        assert "CREATE" in text
        assert "UPDATE#88" in text
        assert "status=draft" in text
        assert "PLAN ONLY" in text
        print("PASS: mocked read-only preview proves CREATE vs UPDATE logic")

        apply_output = io.StringIO()
        results = ip.apply_import(rows, gateway, apply_output)  # type: ignore[arg-type]
        assert len(results) == 4
        assert [created for _, _, _, created in gateway.upserts] == [True, True, True, False]
        assert [price for _, _, price, _ in gateway.upserts] == [580000, 625000, 1500000, 2500000]
        assert gateway.imports[0][0] == "ring-front.jpg"
        assert gateway.imports[0][3] == "RAD-RNG-M-1001"
        assert gateway.image_sets == [(200, [901])]
        assert "status=draft" in apply_output.getvalue()
        assert "status=preserved" in apply_output.getvalue()
        source = (Path(__file__).parent / "import_products.py").read_text(encoding="utf-8")
        assert "$p->set_status('draft')" in source
        forbidden_status_call = "$p->set_status('pub" + "lish')"
        assert forbidden_status_call not in source
        assert "--apply-production" not in source
        print("PASS: mocked apply keeps new products Draft and preserves existing status")

        # Exercise the owner-facing shell wrapper in plan mode and prove that
        # apply cannot start without the explicit confirmation guard.
        private = root / "private"
        (private / "import" / "images").mkdir(parents=True)
        (private / "state").mkdir(parents=True)
        shutil.copy2(csv_path, private / "import" / "products.csv")
        shutil.copy2(rate, private / "state" / "daily_rate.txt")
        shutil.copy2(images / "ring-front.jpg", private / "import" / "images" / "ring-front.jpg")
        env = dict(os.environ)
        env.update({"RADMAN_PRIVATE_DIR": str(private), "RADMAN_REPO_ROOT": str(ip.REPO_ROOT)})
        wrapper = ip.REPO_ROOT / "scripts" / "import_products.sh"
        planned = subprocess.run(
            ["bash", str(wrapper), "--plan"],
            cwd=ip.REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert planned.returncode == 0, planned.stderr
        assert "DRY-RUN PREVIEW" in planned.stdout
        assert "CHECK-AT-APPLY" in planned.stdout
        assert "No host/product/media mutation" in planned.stdout

        guarded_env = dict(env)
        guarded_env.update({
            "APP_ENV": "staging",
            "WP_URL": ip.EXPECTED_WP_URL,
            "WP_PATH": ip.EXPECTED_WP_PATH,
        })
        guarded = subprocess.run(
            ["bash", str(wrapper), "--apply-staging"],
            cwd=ip.REPO_ROOT,
            env=guarded_env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert guarded.returncode != 0
        assert "CONFIRM_STAGING_APPLY must equal YES" in guarded.stderr
        assert not (private / "backups").exists()
        print("PASS: owner shell plan is dry and apply confirmation guard blocks mutation")

        # Sample rows are deliberately non-importable until the owner replaces them.
        sample = root / "sample.csv"
        with sample.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=ip.CSV_COLUMNS)
            writer.writeheader()
            row = {name: "" for name in ip.CSV_COLUMNS}
            row.update({
                "sku": "SAMPLE-RAD-RNG-M-0001",
                "title_fa": "نمونه",
                "category": "rings",
                "silver_purity": "925",
                "pricing_mode": "manual_locked",
                "stock": "1",
                "manual_price_toman": "1",
                "short_description": "نمونه",
                "long_description": "نمونه",
            })
            writer.writerow(row)
        try:
            ip.load_product_rows(sample, images, rate)
            raise AssertionError("sample row should have been rejected")
        except ip.ImportValidationError as exc:
            assert "SAMPLE row detected" in str(exc)
        print("PASS: SAMPLE template cannot be imported accidentally")


if __name__ == "__main__":
    run_tests()
    print("ALL PRODUCT IMPORT TESTS PASSED")
