#!/usr/bin/env python3
"""RADMAN SILVER 925 — validated CSV -> WooCommerce draft importer.

The public entry point is scripts/import_products.sh. This helper is stdlib-only
and talks to WordPress exclusively through wp-cli subprocesses (`wp eval`,
`wp media import`, and `wp post meta update`). It never calls WooCommerce REST,
never publishes a product, and never downloads remote media.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, TextIO, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.lib import radman_common as rc  # noqa: E402

EXPECTED_APP_ENV = "staging"
EXPECTED_WP_URL = "https://staging.radmansilver.ir"
EXPECTED_WP_PATH = "/home/radmansi/staging.radmansilver.ir"
MAX_ROWS = 500

CSV_COLUMNS = (
    "sku",
    "title_fa",
    "category",
    "weight_grams",
    "silver_purity",
    "stone_type",
    "stone_value_toman",
    "pricing_mode",
    "stock",
    "legacy_price_toman",
    "manual_price_toman",
    "short_description",
    "long_description",
    "image_filenames",
)

CATEGORY_CODE = {"rings": "RNG", "necklaces": "NEC", "bracelets": "BRC"}
EXPECTED_CATEGORY_IDS = {"rings": 17, "necklaces": 18, "bracelets": 19}
PRICING_MODES = {
    rc.MODE_WEIGHT_ONLY,
    rc.MODE_WEIGHT_PLUS_STONE,
    rc.MODE_LEGACY_MIRROR,
    rc.MODE_MANUAL_LOCKED,
}
SKU_RE = re.compile(r"^RAD-(RNG|NEC|BRC)-(W|M|U)-[0-9]{4,}$")
IMAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.(?:jpe?g|png|webp)$", re.IGNORECASE)

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


class ImportValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


class WPCliError(RuntimeError):
    pass


@dataclass
class ProductRow:
    row_number: int
    sku: str
    title_fa: str
    category: str
    weight_grams: Optional[Decimal]
    silver_purity: int
    stone_type: str
    stone_value_toman: Optional[int]
    pricing_mode: str
    stock: int
    legacy_price_toman: Optional[int]
    manual_price_toman: Optional[int]
    short_description: str
    long_description: str
    image_filenames: List[str]
    computed_price_toman: int = 0
    existing_id: Optional[int] = None
    inspection_complete: bool = False
    present_images: List[Path] = field(default_factory=list)
    missing_images: List[str] = field(default_factory=list)

    @property
    def action(self) -> str:
        return "UPDATE" if self.existing_id else "CREATE"

    @property
    def target_status(self) -> str:
        return "preserve" if self.existing_id else "draft"


@dataclass
class ApplyResult:
    product_id: int
    created: bool
    image_ids: List[int]


def _clean_number(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .translate(_DIGITS)
        .replace("٬", "")
        .replace(",", "")
        .replace(" ", "")
        .replace("٫", ".")
    )


def parse_int(value: str, field_name: str, *, allow_blank: bool = False) -> Optional[int]:
    cleaned = _clean_number(value)
    if not cleaned:
        if allow_blank:
            return None
        raise ValueError(f"{field_name} is required")
    if not re.fullmatch(r"[0-9]+", cleaned):
        raise ValueError(f"{field_name} must be a non-negative integer")
    return int(cleaned)


def parse_decimal(value: str, field_name: str, *, allow_blank: bool = False) -> Optional[Decimal]:
    cleaned = _clean_number(value)
    if not cleaned:
        if allow_blank:
            return None
        raise ValueError(f"{field_name} is required")
    try:
        parsed = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal number") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field_name} must be a non-negative decimal")
    return parsed


def read_daily_rate(path: Path) -> int:
    if not path.is_file():
        raise ImportValidationError([f"daily rate file is missing: {path}"])
    cleaned = _clean_number(path.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[0-9]+", cleaned or "") or int(cleaned) <= 0:
        raise ImportValidationError([f"daily rate must contain one positive integer (Toman/gram): {path}"])
    return int(cleaned)


def calculate_price(row: ProductRow, daily_rate: Optional[int]) -> int:
    if row.pricing_mode == rc.MODE_WEIGHT_ONLY:
        if daily_rate is None or row.weight_grams is None:
            raise ValueError("daily rate and weight are required")
        return rc.round_to_step(row.weight_grams * Decimal(daily_rate))

    if row.pricing_mode == rc.MODE_WEIGHT_PLUS_STONE:
        if daily_rate is None or row.weight_grams is None or row.stone_value_toman is None:
            raise ValueError("daily rate, weight, and stone value are required")
        total = row.weight_grams * Decimal(daily_rate) + Decimal(row.stone_value_toman)
        return int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    if row.pricing_mode == rc.MODE_LEGACY_MIRROR:
        if not row.legacy_price_toman:
            raise ValueError("legacy_price_toman must be a positive integer")
        return row.legacy_price_toman

    if row.pricing_mode == rc.MODE_MANUAL_LOCKED:
        if not row.manual_price_toman:
            raise ValueError("manual_price_toman must be a positive integer")
        return row.manual_price_toman

    raise ValueError(f"unsupported pricing mode: {row.pricing_mode}")


def _parse_images(raw: str) -> List[str]:
    names = [part.strip() for part in str(raw or "").split("|") if part.strip()]
    seen: set[str] = set()
    result: List[str] = []
    for name in names:
        if Path(name).name != name or not IMAGE_RE.fullmatch(name):
            raise ValueError(
                "image_filenames accepts basename-only JPG/JPEG/PNG/WebP names separated by |"
            )
        if name in seen:
            raise ValueError(f"duplicate image filename: {name}")
        seen.add(name)
        result.append(name)
    return result


def load_product_rows(csv_path: Path, images_dir: Path, daily_rate_path: Path) -> Tuple[List[ProductRow], Optional[int]]:
    if not csv_path.is_file():
        raise ImportValidationError([f"product CSV is missing: {csv_path}"])

    errors: List[str] = []
    rows: List[ProductRow] = []
    seen_skus: set[str] = set()
    seen_image_names: set[str] = set()

    try:
        handle = csv_path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ImportValidationError([f"cannot read CSV {csv_path}: {exc}"]) from exc

    with handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing_headers = [name for name in CSV_COLUMNS if name not in headers]
        if missing_headers:
            raise ImportValidationError([
                "CSV is missing required column(s): " + ", ".join(missing_headers)
            ])

        for row_number, raw in enumerate(reader, start=2):
            if row_number > MAX_ROWS + 1:
                errors.append(f"CSV exceeds safety limit of {MAX_ROWS} product rows")
                break
            prefix = f"row {row_number}"
            try:
                sku = str(raw.get("sku", "")).strip().upper()
                if sku.startswith("SAMPLE-") or "SAMPLE" in sku:
                    raise ValueError("SAMPLE row detected; replace sample SKU/content before import")
                match = SKU_RE.fullmatch(sku)
                if not match:
                    raise ValueError("sku must match RAD-(RNG|NEC|BRC)-(W|M|U)-NNNN")
                if sku in seen_skus:
                    raise ValueError(f"duplicate SKU in CSV: {sku}")

                title = str(raw.get("title_fa", "")).strip()
                short_description = str(raw.get("short_description", "")).strip()
                long_description = str(raw.get("long_description", "")).strip()
                if not title:
                    raise ValueError("title_fa is required")
                if not short_description:
                    raise ValueError("short_description is required")
                if not long_description:
                    raise ValueError("long_description is required")

                category = str(raw.get("category", "")).strip().lower()
                if category not in CATEGORY_CODE:
                    raise ValueError("category must be rings, necklaces, or bracelets")
                if match.group(1) != CATEGORY_CODE[category]:
                    raise ValueError("SKU category code does not match category column")

                purity = parse_int(str(raw.get("silver_purity", "")), "silver_purity")
                if purity != 925:
                    raise ValueError("silver_purity must equal 925")

                pricing_mode = str(raw.get("pricing_mode", "")).strip()
                if pricing_mode not in PRICING_MODES:
                    raise ValueError("pricing_mode is not one of the four official modes")

                weight = parse_decimal(str(raw.get("weight_grams", "")), "weight_grams", allow_blank=True)
                stone_value = parse_int(
                    str(raw.get("stone_value_toman", "")), "stone_value_toman", allow_blank=True
                )
                legacy_price = parse_int(
                    str(raw.get("legacy_price_toman", "")), "legacy_price_toman", allow_blank=True
                )
                manual_price = parse_int(
                    str(raw.get("manual_price_toman", "")), "manual_price_toman", allow_blank=True
                )
                stock = parse_int(str(raw.get("stock", "")), "stock", allow_blank=True)
                if stock is None:
                    stock = 1

                stone_type = str(raw.get("stone_type", "")).strip()
                if pricing_mode in (rc.MODE_WEIGHT_ONLY, rc.MODE_WEIGHT_PLUS_STONE):
                    if weight is None or weight <= 0:
                        raise ValueError("weight_grams must be positive for weight pricing modes")
                if pricing_mode == rc.MODE_WEIGHT_PLUS_STONE:
                    if not stone_type:
                        raise ValueError("stone_type is required for silver_weight_plus_stone")
                    if stone_value is None or stone_value <= 0:
                        raise ValueError("stone_value_toman must be positive for silver_weight_plus_stone")
                if pricing_mode == rc.MODE_LEGACY_MIRROR and (legacy_price is None or legacy_price <= 0):
                    raise ValueError("legacy_price_toman must be positive for legacy_mirror")
                if pricing_mode == rc.MODE_MANUAL_LOCKED and (manual_price is None or manual_price <= 0):
                    raise ValueError("manual_price_toman must be positive for manual_locked")

                images = _parse_images(str(raw.get("image_filenames", "")))
                repeated_images = [name for name in images if name in seen_image_names]
                if repeated_images:
                    raise ValueError(
                        "image filename(s) reused by another CSV row: " + ", ".join(repeated_images)
                    )
                product = ProductRow(
                    row_number=row_number,
                    sku=sku,
                    title_fa=title,
                    category=category,
                    weight_grams=weight,
                    silver_purity=purity,
                    stone_type=stone_type,
                    stone_value_toman=stone_value,
                    pricing_mode=pricing_mode,
                    stock=stock,
                    legacy_price_toman=legacy_price,
                    manual_price_toman=manual_price,
                    short_description=short_description,
                    long_description=long_description,
                    image_filenames=images,
                )
                seen_skus.add(sku)
                seen_image_names.update(images)
                rows.append(product)
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")

    if not rows and not errors:
        errors.append("CSV contains no product rows")
    if errors:
        raise ImportValidationError(errors)

    needs_rate = any(
        row.pricing_mode in (rc.MODE_WEIGHT_ONLY, rc.MODE_WEIGHT_PLUS_STONE) for row in rows
    )
    daily_rate = read_daily_rate(daily_rate_path) if needs_rate else None

    for row in rows:
        try:
            row.computed_price_toman = calculate_price(row, daily_rate)
        except ValueError as exc:
            errors.append(f"row {row.row_number}: {exc}")
        for filename in row.image_filenames:
            image_path = images_dir / filename
            if image_path.is_file():
                row.present_images.append(image_path)
            else:
                row.missing_images.append(filename)

    if errors:
        raise ImportValidationError(errors)
    return rows, daily_rate


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class WPGateway:
    """Small wp-cli adapter. No REST and no shell=True."""

    def __init__(self, wp_path: str) -> None:
        self.wp_path = wp_path
        self._category_cache: Dict[str, int] = {}

    def run(self, args: Sequence[str], timeout: int = 180) -> str:
        cmd = ["wp", f"--path={self.wp_path}", "--no-color", *args]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise WPCliError(f"wp-cli execution failed for command: {' '.join(args[:2])}") from exc
        if proc.returncode != 0:
            raise WPCliError(
                f"wp-cli command {' '.join(args[:2])} exited {proc.returncode}"
            )
        return proc.stdout.strip()

    def eval_scalar(self, php_code: str) -> str:
        output = self.run(["eval", php_code])
        return output.splitlines()[-1].strip() if output else ""

    def eval_json(self, php_code: str) -> Any:
        output = self.run(["eval", php_code])
        if not output:
            raise WPCliError("wp eval returned empty output")
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            for line in reversed(output.splitlines()):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        raise WPCliError("wp eval returned non-JSON output")

    def find_product_id(self, sku: str) -> Optional[int]:
        php = (
            f"$id=function_exists('wc_get_product_id_by_sku') ? "
            f"wc_get_product_id_by_sku(base64_decode('{_b64(sku)}')) : 0; echo (string) $id;"
        )
        raw = self.eval_scalar(php)
        return int(raw) if raw.isdigit() and int(raw) > 0 else None

    def resolve_category_id(self, slug: str) -> int:
        if slug in self._category_cache:
            return self._category_cache[slug]
        php = (
            f"$t=get_term_by('slug', base64_decode('{_b64(slug)}'), 'product_cat'); "
            "if ($t && !is_wp_error($t)) { echo (string) $t->term_id; }"
        )
        raw = self.eval_scalar(php)
        if not raw.isdigit() or int(raw) <= 0:
            raise WPCliError(f"WooCommerce product category not found: {slug}")
        category_id = int(raw)
        expected_id = EXPECTED_CATEGORY_IDS[slug]
        if category_id != expected_id:
            raise WPCliError(
                f"category {slug} resolved to ID {category_id}, expected locked staging ID {expected_id}"
            )
        self._category_cache[slug] = category_id
        return category_id

    def upsert_product(self, row: ProductRow, category_id: int) -> Tuple[int, bool]:
        metadata: Dict[str, str] = {
            "pricing_mode": row.pricing_mode,
            "silver_purity": str(row.silver_purity),
            "silver_weight_grams": "" if row.weight_grams is None else format(row.weight_grams, "f"),
            "stone_type": row.stone_type,
            "stone_fixed_value_toman": str(row.stone_value_toman or ""),
            "legacy_price_toman": str(row.legacy_price_toman or ""),
            "manual_price_toman": str(row.manual_price_toman or ""),
            "price_locked": "1" if row.pricing_mode == rc.MODE_MANUAL_LOCKED else "0",
            "rounding_step_toman": str(rc.PRICE_ROUND_STEP),
            "radman_import_source": "owner_csv",
        }
        payload = {
            "sku": row.sku,
            "name": row.title_fa,
            "category_id": category_id,
            "stock": row.stock,
            "price": row.computed_price_toman,
            "short_description": row.short_description,
            "description": row.long_description,
            "meta": metadata,
        }
        encoded = _b64(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        php = f"""
if (!function_exists('wc_get_product_id_by_sku')) {{ fwrite(STDERR, 'WooCommerce unavailable'); exit(3); }}
$d=json_decode(base64_decode('{encoded}'), true);
$id=wc_get_product_id_by_sku($d['sku']);
$created=false;
if ($id) {{
  $p=wc_get_product($id);
  if (!$p || !($p instanceof WC_Product_Simple)) {{ fwrite(STDERR, 'Existing SKU is not a simple product'); exit(4); }}
}} else {{
  $p=new WC_Product_Simple();
  $p->set_sku($d['sku']);
  $p->set_status('draft');
  $p->set_catalog_visibility('visible');
  $created=true;
}}
$p->set_name($d['name']);
$p->set_short_description($d['short_description']);
$p->set_description($d['description']);
$p->set_regular_price((string) $d['price']);
$p->set_price((string) $d['price']);
$p->set_manage_stock(true);
$p->set_stock_quantity((int) $d['stock']);
$p->set_stock_status(((int) $d['stock']) > 0 ? 'instock' : 'outofstock');
$cats=$created ? array() : $p->get_category_ids('edit');
$cats[]=(int) $d['category_id'];
$p->set_category_ids(array_values(array_unique(array_map('intval', $cats))));
foreach ($d['meta'] as $key => $value) {{
  if ($value === '') {{ $p->delete_meta_data($key); }} else {{ $p->update_meta_data($key, (string) $value); }}
}}
$id=$p->save();
delete_post_meta($id, '_sale_price');
update_post_meta($id, '_price', (string) $d['price']);
wc_delete_product_transients($id);
echo wp_json_encode(array('id'=>(int) $id, 'created'=>$created));
"""
        result = self.eval_json(php)
        if not isinstance(result, dict) or not int(result.get("id", 0)):
            raise WPCliError(f"invalid WooCommerce upsert result for {row.sku}")
        return int(result["id"]), bool(result.get("created"))

    def _find_attachment(self, import_key: str) -> Optional[int]:
        php = (
            "$ids=get_posts(array('post_type'=>'attachment','post_status'=>'inherit',"
            "'posts_per_page'=>1,'fields'=>'ids','meta_key'=>'_radman_import_key',"
            f"'meta_value'=>base64_decode('{_b64(import_key)}'))); "
            "if ($ids) { echo (string) $ids[0]; }"
        )
        raw = self.eval_scalar(php)
        return int(raw) if raw.isdigit() and int(raw) > 0 else None

    def import_image(self, path: Path, title: str, product_id: int, sku: str) -> int:
        filename = path.name
        import_key = f"{sku}|{filename}"
        attachment_id = self._find_attachment(import_key)
        if attachment_id is None:
            output = self.run(
                [
                    "media",
                    "import",
                    str(path),
                    f"--title={title}",
                    f"--post_id={product_id}",
                    "--porcelain",
                ],
                timeout=300,
            )
            numeric = [line.strip() for line in output.splitlines() if line.strip().isdigit()]
            if not numeric:
                raise WPCliError(f"media import returned no attachment ID for {filename}")
            attachment_id = int(numeric[-1])
        self.run(["post", "meta", "update", str(attachment_id), "_radman_import_key", import_key])
        self.run(["post", "meta", "update", str(attachment_id), "_radman_import_filename", filename])
        self.run(["post", "meta", "update", str(attachment_id), "_wp_attachment_image_alt", title])
        php = f"wp_update_post(array('ID'=>{attachment_id}, 'post_parent'=>{product_id})); echo '{attachment_id}';"
        self.eval_scalar(php)
        return attachment_id

    def set_product_images(self, product_id: int, image_ids: Sequence[int]) -> None:
        if not image_ids:
            return
        ids = [int(value) for value in image_ids]
        featured = ids[0]
        gallery = ",".join(str(value) for value in ids[1:])
        php = f"""
$p=wc_get_product({int(product_id)});
if (!$p) {{ fwrite(STDERR, 'Product not found for image attach'); exit(5); }}
$p->set_image_id({featured});
$p->set_gallery_image_ids(array({gallery}));
$p->save();
echo (string) $p->get_id();
"""
        result = self.eval_scalar(php)
        if result != str(product_id):
            raise WPCliError(f"image attachment verification failed for product {product_id}")


def inspect_existing(rows: Iterable[ProductRow], gateway: WPGateway) -> None:
    for row in rows:
        row.existing_id = gateway.find_product_id(row.sku)
        row.inspection_complete = True


def render_preview(rows: Sequence[ProductRow], daily_rate: Optional[int], out: TextIO = sys.stdout) -> None:
    print("=" * 112, file=out)
    print("RADMAN PRODUCT IMPORT — DRY-RUN PREVIEW", file=out)
    print(f"Rows: {len(rows)} | daily_rate: {daily_rate if daily_rate else 'not required'} Toman/gram", file=out)
    print("All new products target status=draft. Existing product status is preserved.", file=out)
    print("-" * 112, file=out)
    print(f"{'ROW':>4}  {'SKU':<27} {'ACTION':<14} {'CATEGORY':<11} {'MODE':<25} {'STOCK':>5} {'PRICE':>13}  IMAGES", file=out)
    print("-" * 112, file=out)
    for row in rows:
        if row.existing_id is not None:
            action = f"UPDATE#{row.existing_id}"
        elif row.inspection_complete:
            action = "CREATE"
        else:
            action = "CHECK-AT-APPLY"
        image_note = f"{len(row.present_images)}/{len(row.image_filenames)} present"
        print(
            f"{row.row_number:>4}  {row.sku:<27} {action:<14} {row.category:<11} "
            f"{row.pricing_mode:<25} {row.stock:>5} {row.computed_price_toman:>13,}  {image_note}",
            file=out,
        )
    print("-" * 112, file=out)
    print("PLAN ONLY — no product, media, status, payment, or site setting was changed.", file=out)
    print("=" * 112, file=out)


def apply_import(rows: Sequence[ProductRow], gateway: WPGateway, out: TextIO = sys.stdout) -> List[ApplyResult]:
    results: List[ApplyResult] = []
    for row in rows:
        row.existing_id = gateway.find_product_id(row.sku)
        category_id = gateway.resolve_category_id(row.category)
        product_id, created = gateway.upsert_product(row, category_id)
        image_ids: List[int] = []
        for image_path in row.present_images:
            image_ids.append(gateway.import_image(image_path, row.title_fa, product_id, row.sku))
        if image_ids:
            gateway.set_product_images(product_id, image_ids)
        for missing in row.missing_images:
            print(f"[WARN] {row.sku}: image missing, skipped: {missing}", file=sys.stderr)
        status_note = "draft" if created else "preserved"
        print(
            f"[APPLY] {row.sku}: {'CREATED' if created else 'UPDATED'} product_id={product_id} "
            f"status={status_note} price={row.computed_price_toman} images={len(image_ids)}",
            file=out,
        )
        results.append(ApplyResult(product_id=product_id, created=created, image_ids=image_ids))
    return results


def require_apply_environment(wp_path: str) -> None:
    errors = []
    if os.environ.get("APP_ENV") != EXPECTED_APP_ENV:
        errors.append("APP_ENV must equal staging")
    if os.environ.get("WP_URL") != EXPECTED_WP_URL:
        errors.append(f"WP_URL must equal {EXPECTED_WP_URL}")
    if wp_path != EXPECTED_WP_PATH:
        errors.append(f"WP_PATH must equal {EXPECTED_WP_PATH}")
    if "public_html" in wp_path:
        errors.append("WP_PATH containing public_html is prohibited")
    if os.environ.get("CONFIRM_STAGING_APPLY") != "YES":
        errors.append("CONFIRM_STAGING_APPLY must equal YES")
    if errors:
        raise ImportValidationError(errors)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RADMAN validated product CSV importer")
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument("--daily-rate-file", required=True, type=Path)
    parser.add_argument("--wp-path", default=os.environ.get("WP_PATH", ""))
    parser.add_argument("--inspect-wp", action="store_true", help="read-only SKU inspection during plan")
    parser.add_argument("--apply-staging", action="store_true", help="mutate staging; guarded")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        rows, daily_rate = load_product_rows(args.csv, args.images_dir, args.daily_rate_file)
        gateway: Optional[WPGateway] = None
        if args.apply_staging:
            require_apply_environment(args.wp_path)
            gateway = WPGateway(args.wp_path)
        elif args.inspect_wp:
            if not args.wp_path:
                raise ImportValidationError(["--inspect-wp requires --wp-path"])
            gateway = WPGateway(args.wp_path)

        if gateway is not None:
            inspect_existing(rows, gateway)
        render_preview(rows, daily_rate)

        if args.apply_staging:
            assert gateway is not None
            results = apply_import(rows, gateway)
            print(f"[APPLY] complete: {len(results)} product row(s) processed; new products remain DRAFT.")
        return 0
    except ImportValidationError as exc:
        for error in exc.errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 2
    except WPCliError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
