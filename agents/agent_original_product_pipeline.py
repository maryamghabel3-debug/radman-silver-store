#!/usr/bin/env python3
"""Orchestrate the ten-product original-media, classification, pricing, and draft path."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.agent_gemstone_classifier import classify_product  # noqa: E402
from agents.agent_legacy_catalog_pilot import (  # noqa: E402
    ORIGINAL_PRODUCT_MAX,
    scrape_original_products,
)
from agents.agent_original_image_processor import process_product  # noqa: E402
from agents.lib.legacy_pricing import (  # noqa: E402
    calculate_safe_price,
    price_difference_flags,
)
from scripts.import_products import (  # noqa: E402
    WPGateway,
    WPCliError,
    require_apply_environment,
)

EXPECTED_WP_PATH = "/home/radmansi/staging.radmansilver.ir"
PIPELINE_VERSION = "PR-25"
REPORT_TIMEZONE = ZoneInfo("Asia/Tehran")
REQUIRED_CURRENCY = "IRT"
VALID_CATEGORIES = {"rings", "necklaces", "bracelets"}
REPORT_COLUMNS = (
    "legacy_id",
    "legacy_code_raw",
    "legacy_code",
    "sku",
    "product_url",
    "title",
    "category",
    "weight_grams",
    "legacy_price_toman",
    "stone_class",
    "stone_confidence",
    "stone_source",
    "rate_toman_per_gram",
    "calculated_price_toman",
    "selected_pre_round_toman",
    "final_price_toman",
    "selection_reason",
    "image_qa_status",
    "optimized_featured_approved",
    "image_integrity_action",
    "conflict",
    "requires_review",
    "review_reasons",
    "import_action",
    "wordpress_product_id",
    "attachment_ids",
)


class PipelineError(RuntimeError):
    pass


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def now_tehran() -> datetime:
    return datetime.now(REPORT_TIMEZONE)


def timestamp_slug() -> str:
    return now_tehran().strftime("%Y%m%dT%H%M%S%z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def require_private_artifact(path: Path, private_dir: Path) -> Path:
    resolved = path.expanduser().resolve()
    private_root = private_dir.expanduser().resolve()
    if resolved != private_root and private_root not in resolved.parents:
        raise PipelineError(f"artifact must stay under RADMAN_PRIVATE_DIR: {resolved}")
    if not resolved.is_file():
        raise PipelineError(f"artifact is missing: {resolved}")
    return resolved


def validate_private_media(records: Sequence[Dict[str, Any]], private_dir: Path) -> None:
    private_root = private_dir.expanduser().resolve()
    for record in records:
        for raw_path in record.get("selected_import_paths", []):
            resolved = Path(raw_path).expanduser().resolve()
            if private_root not in resolved.parents:
                raise PipelineError(
                    f"selected media must stay under RADMAN_PRIVATE_DIR: {resolved}"
                )


def latest_artifact(private_dir: Path, name: str) -> Path:
    candidates = sorted(
        (private_dir / "legacy-cache" / "runs").glob(f"*/{name}"), reverse=True
    )
    if not candidates:
        raise PipelineError(f"no {name} artifact exists; run the required earlier phase")
    return candidates[0]


def load_products(source_manifest: Path) -> List[Dict[str, Any]]:
    payload = read_json(source_manifest)
    products = payload if isinstance(payload, list) else payload.get("products", [])
    if not isinstance(products, list) or not products:
        raise PipelineError(f"manifest contains no products: {source_manifest}")
    if len(products) > ORIGINAL_PRODUCT_MAX:
        raise PipelineError(
            f"manifest has {len(products)} products; hard maximum is {ORIGINAL_PRODUCT_MAX}"
        )
    return [dict(item) for item in products]


def _image_integrity_action(qa: Optional[Dict[str, Any]]) -> str:
    if qa is None:
        return "NOT_RUN"
    if qa.get("qa_status") == "PASS":
        return "OPTIMIZED_OUTPUT_APPROVED"
    return "UNTOUCHED_ORIGINAL_FALLBACK"


def prepare_products(
    products: Sequence[Dict[str, Any]],
    *,
    private_dir: Path,
    run_dir: Path,
    run_image_qa: bool,
) -> List[Dict[str, Any]]:
    qa_dir = run_dir / "image-qa"
    prepared: List[Dict[str, Any]] = []
    for product in products:
        category = str(
            product.get("category") or product.get("mapped_radman_category") or ""
        ).lower()
        original_paths = [Path(path) for path in product.get("original_image_paths", [])]
        private_root = private_dir.expanduser().resolve()
        for original_path in original_paths:
            resolved_original = original_path.expanduser().resolve()
            if private_root not in resolved_original.parents:
                raise PipelineError(
                    f"original media must stay under RADMAN_PRIVATE_DIR: {resolved_original}"
                )
        classification = classify_product(
            category=category,
            title=str(product.get("title") or product.get("title_fa") or ""),
            short_description=str(product.get("short_description") or ""),
            description=str(product.get("description") or ""),
            image_paths=original_paths,
        )
        pricing = calculate_safe_price(
            category=category,
            stone_class=classification.stone_class,
            stone_confidence=classification.confidence,
            weight_grams=product.get("weight_grams"),
            legacy_price_toman=product.get("visible_legacy_price_toman"),
        )
        qa: Optional[Dict[str, Any]] = None
        if run_image_qa:
            qa = process_product(
                str(product.get("legacy_id")),
                original_paths,
                private_dir,
                qa_dir,
            )

        review_reasons = list(product.get("review_reasons", []))
        review_reasons.extend(classification.evidence if classification.requires_review else [])
        review_reasons.extend(pricing.warnings)
        review_reasons.extend(price_difference_flags(pricing))
        if category not in VALID_CATEGORIES:
            review_reasons.append("unsupported category")
        if pricing.final_price_toman is None:
            review_reasons.append("no safe final price")
        if not original_paths:
            review_reasons.append("no archived original images")
        missing_originals = [str(path) for path in original_paths if not path.is_file()]
        if missing_originals:
            review_reasons.append("archived original image missing")
        if qa is not None and qa.get("qa_status") != "PASS":
            review_reasons.append("optimized media rejected; original selected")
        review_reasons = list(dict.fromkeys(str(reason) for reason in review_reasons if reason))

        selected_paths = (
            list(qa.get("selected_import_paths", []))
            if qa is not None
            else [str(path) for path in original_paths]
        )
        import_blocked = bool(
            pricing.final_price_toman is None
            or category not in VALID_CATEGORIES
            or not product.get("legacy_id")
            or not product.get("legacy_code")
            or not product.get("sku")
            or not selected_paths
            or bool(missing_originals)
        )
        import_action = "SKIP_INVALID_REVIEW" if import_blocked else "CREATE_DRAFT"
        if not run_image_qa and not import_blocked:
            import_action = "BLOCKED_IMAGE_QA_REQUIRED"

        title = str(product.get("title") or product.get("title_fa") or "").strip()
        description = str(product.get("description") or "").strip()
        short_description = str(product.get("short_description") or "").strip()
        if not short_description:
            short_description = description[:500] or title
        if not description:
            description = short_description or title

        record: Dict[str, Any] = {
            **product,
            "title": title,
            "short_description": short_description,
            "description": description,
            "category": category,
            "classification": classification.to_dict(),
            "pricing": pricing.to_dict(),
            "image_qa": qa,
            "image_qa_status": qa.get("qa_status") if qa else "NOT_RUN",
            "optimized_featured_approved": bool(
                qa and qa.get("optimized_featured_approved")
            ),
            "image_integrity_action": _image_integrity_action(qa),
            "selected_import_paths": selected_paths,
            "review_reasons": review_reasons,
            "requires_review": bool(review_reasons or pricing.requires_review),
            "conflict": "",
            "import_action": import_action,
        }
        prepared.append(record)
    return prepared


def _report_row(record: Dict[str, Any]) -> Dict[str, Any]:
    stone = record.get("classification", {})
    pricing = record.get("pricing", {})
    return {
        "legacy_id": record.get("legacy_id", ""),
        "legacy_code_raw": record.get("legacy_code_raw", ""),
        "legacy_code": record.get("legacy_code", ""),
        "sku": record.get("sku", ""),
        "product_url": record.get("product_url", ""),
        "title": record.get("title", ""),
        "category": record.get("category", ""),
        "weight_grams": pricing.get("weight_grams", ""),
        "legacy_price_toman": pricing.get("legacy_price_toman", ""),
        "stone_class": stone.get("stone_class", ""),
        "stone_confidence": stone.get("confidence", ""),
        "stone_source": stone.get("source", ""),
        "rate_toman_per_gram": pricing.get("rate_toman_per_gram", ""),
        "calculated_price_toman": pricing.get("calculated_price_toman", ""),
        "selected_pre_round_toman": pricing.get("selected_pre_round_toman", ""),
        "final_price_toman": pricing.get("final_price_toman", ""),
        "selection_reason": pricing.get("selection_reason", ""),
        "image_qa_status": record.get("image_qa_status", ""),
        "optimized_featured_approved": record.get("optimized_featured_approved", ""),
        "image_integrity_action": record.get("image_integrity_action", ""),
        "conflict": record.get("conflict", ""),
        "requires_review": record.get("requires_review", ""),
        "review_reasons": " | ".join(record.get("review_reasons", [])),
        "import_action": record.get("import_action", ""),
        "wordpress_product_id": record.get("wordpress_product_id", ""),
        "attachment_ids": " | ".join(
            str(value) for value in record.get("attachment_ids", [])
        ),
    }


def _scrape_skip_record(item: Dict[str, Any]) -> Dict[str, Any]:
    reason = str(item.get("reason") or "SCRAPE_SKIP")
    conflict = reason if "DUPLICATE" in reason or "CONFLICT" in reason else ""
    return {
        **item,
        "legacy_code_raw": item.get("legacy_code", ""),
        "sku": item.get("sku", ""),
        "title": "",
        "category": "",
        "classification": {},
        "pricing": {},
        "image_qa_status": "NOT_RUN",
        "optimized_featured_approved": False,
        "image_integrity_action": "NOT_RUN",
        "conflict": conflict,
        "requires_review": True,
        "review_reasons": [
            value for value in (reason, str(item.get("detail") or "")) if value
        ],
        "import_action": "SKIP_SCRAPE",
    }


def write_reports(
    records: Sequence[Dict[str, Any]],
    run_dir: Path,
    scrape_skipped: Sequence[Dict[str, Any]] = tuple(),
) -> Tuple[Path, Path]:
    report_stamp = timestamp_slug()
    csv_path = run_dir / f"original-products-{report_stamp}.csv"
    summary_path = run_dir / f"original-products-{report_stamp}-fa.txt"
    run_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    skipped_records = [_scrape_skip_record(item) for item in scrape_skipped]
    report_records = [*records, *skipped_records]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for record in report_records:
            writer.writerow(_report_row(record))
    os.chmod(csv_path, 0o600)

    review_count = sum(bool(record.get("requires_review")) for record in report_records)
    fallback_count = sum(
        record.get("image_integrity_action") == "UNTOUCHED_ORIGINAL_FALLBACK"
        for record in records
    )
    lines = [
        "گزارش خط لوله محصولات با تصاویر اصلی رادمان",
        f"زمان گزارش: {now_tehran().isoformat()} (Asia/Tehran)",
        f"تعداد محصولات آماده‌شده: {len(records)}",
        f"موارد ردشده در scrape: {len(skipped_records)}",
        f"نیازمند بازبینی: {review_count}",
        f"بازگشت به تصویر اصلی بدون تغییر: {fallback_count}",
        "واحد همه قیمت‌ها: تومان (IRT)؛ هیچ تبدیل ریال/تومان انجام نشده است.",
        "محصول جدید فقط به‌صورت پیش‌نویس، موجودی ۱ و بدون سفارشِ معوق ساخته می‌شود.",
        "",
    ]
    for record in report_records:
        pricing = record.get("pricing", {})
        stone = record.get("classification", {})
        lines.extend(
            [
                f"شناسه قدیمی {record.get('legacy_id')} | کد {record.get('legacy_code_raw')}",
                f"  SKU: {record.get('sku')} | دسته: {record.get('category')}",
                f"  نگین: {stone.get('stone_class')} ({stone.get('confidence')})",
                f"  قیمت قدیمی: {pricing.get('legacy_price_toman')} | کف وزنی: {pricing.get('calculated_price_toman')}",
                f"  قیمت نهایی: {pricing.get('final_price_toman')} | دلیل: {pricing.get('selection_reason')}",
                f"  سلامت تصویر: {record.get('image_integrity_action')} | اقدام: {record.get('import_action')}",
                f"  شناسه WordPress: {record.get('wordpress_product_id') or 'ندارد'}",
                f"  تعارض: {record.get('conflict') or 'ندارد'}",
                f"  بازبینی: {'؛ '.join(record.get('review_reasons', [])) or 'ندارد'}",
                "",
            ]
        )
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    os.chmod(summary_path, 0o600)
    return csv_path, summary_path


class LegacyDraftGateway(WPGateway):
    """Create-only extension of the existing WP-CLI gateway."""

    def get_currency(self) -> str:
        return self.eval_scalar("echo (string) get_option('woocommerce_currency', '');")

    def find_product_id_by_legacy_id(self, legacy_id: str) -> Optional[int]:
        encoded = _b64(legacy_id)
        php = f"""
$v=base64_decode('{encoded}');
$q=new WP_Query(array('post_type'=>'product','post_status'=>'any','posts_per_page'=>2,'fields'=>'ids',
'meta_query'=>array('relation'=>'OR',
 array('key'=>'radman_legacy_id','value'=>$v,'compare'=>'='),
 array('key'=>'legacy_id','value'=>$v,'compare'=>'='),
 array('key'=>'_legacy_store_id','value'=>$v,'compare'=>'=')
)));
if (count($q->posts)>1) {{ fwrite(STDERR, 'duplicate legacy ID metadata'); exit(8); }}
if ($q->posts) {{ echo (string) $q->posts[0]; }}
"""
        raw = self.eval_scalar(php)
        return int(raw) if raw.isdigit() and int(raw) > 0 else None

    def create_legacy_draft(
        self, record: Dict[str, Any], category_id: int
    ) -> int:
        pricing = record["pricing"]
        stone = record["classification"]
        qa = record.get("image_qa") or {}
        metadata = {
            "pricing_mode": "manual_locked",
            "radman_pricing_overlay": "legacy_gemstone_floor_v1",
            "silver_purity": "925",
            "silver_weight_grams": pricing.get("weight_grams") or "",
            "stone_type": stone.get("stone_class") or "uncertain",
            "stone_fixed_value_toman": "0",
            "legacy_price_toman": str(pricing.get("legacy_price_toman") or ""),
            "manual_price_toman": str(pricing["final_price_toman"]),
            "price_locked": "1",
            "rounding_step_toman": "50000",
            "legacy_id": str(record["legacy_id"]),
            "legacy_code": str(record["legacy_code_raw"]),
            "legacy_url": str(record["product_url"]),
            "_legacy_store_id": str(record["legacy_id"]),
            "_legacy_product_code": str(record["legacy_code_raw"]),
            "_legacy_product_url": str(record["product_url"]),
            "radman_import_source": "original_legacy_pipeline",
            "radman_import_version": PIPELINE_VERSION,
            "radman_legacy_id": str(record["legacy_id"]),
            "radman_legacy_code": str(record["legacy_code"]),
            "radman_legacy_code_raw": str(record["legacy_code_raw"]),
            "radman_legacy_url": str(record["product_url"]),
            "radman_legacy_price_toman": str(pricing.get("legacy_price_toman") or ""),
            "radman_legacy_price_source": str(record.get("price_source") or ""),
            "radman_weight_grams": str(pricing.get("weight_grams") or ""),
            "radman_gemstone_class": str(stone.get("stone_class") or "uncertain"),
            "radman_gemstone_confidence": str(stone.get("confidence") or "0"),
            "radman_gemstone_source": str(stone.get("source") or ""),
            "radman_requires_review": "1" if record.get("requires_review") else "0",
            "radman_review_reasons": " | ".join(record.get("review_reasons", [])),
            "radman_rate_toman_per_gram": str(pricing["rate_toman_per_gram"]),
            "radman_calculated_floor_toman": str(pricing.get("calculated_price_toman") or ""),
            "radman_final_price_toman": str(pricing["final_price_toman"]),
            "radman_price_selection_reason": str(pricing["selection_reason"]),
            "radman_rounding_step_toman": "50000",
            "radman_image_qa_status": str(record.get("image_qa_status") or ""),
            "radman_image_qa_sheet": str(qa.get("qa_sheet") or ""),
            "radman_image_integrity_action": str(record.get("image_integrity_action") or ""),
            "radman_image_fallback_used": (
                "1"
                if record.get("image_integrity_action")
                == "UNTOUCHED_ORIGINAL_FALLBACK"
                else "0"
            ),
            "radman_original_image_urls": json.dumps(record.get("image_urls", []), ensure_ascii=False),
            "radman_original_image_sha256": json.dumps(
                [
                    item.get("sha256")
                    for item in record.get("downloaded_images", [])
                    if item.get("sha256")
                ],
                ensure_ascii=False,
            ),
        }
        payload = {
            "sku": record["sku"],
            "name": record["title"],
            "category_id": int(category_id),
            "price": int(pricing["final_price_toman"]),
            "short_description": record["short_description"],
            "description": record["description"],
            "meta": metadata,
        }
        encoded = _b64(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        php = f"""
if (!function_exists('wc_get_product_id_by_sku')) {{ fwrite(STDERR, 'WooCommerce unavailable'); exit(3); }}
$d=json_decode(base64_decode('{encoded}'), true);
if (wc_get_product_id_by_sku($d['sku'])) {{ fwrite(STDERR, 'SKU conflict during create'); exit(9); }}
$legacy=(string)$d['meta']['radman_legacy_id'];
$q=new WP_Query(array('post_type'=>'product','post_status'=>'any','posts_per_page'=>1,'fields'=>'ids',
 'meta_query'=>array('relation'=>'OR',
   array('key'=>'radman_legacy_id','value'=>$legacy,'compare'=>'='),
   array('key'=>'legacy_id','value'=>$legacy,'compare'=>'='),
   array('key'=>'_legacy_store_id','value'=>$legacy,'compare'=>'=')
 )));
if ($q->posts) {{ fwrite(STDERR, 'legacy ID appeared during create'); exit(10); }}
$p=new WC_Product_Simple();
$p->set_sku($d['sku']);
$p->set_status('draft');
$p->set_catalog_visibility('visible');
$p->set_name($d['name']);
$p->set_short_description($d['short_description']);
$p->set_description($d['description']);
$p->set_regular_price((string)$d['price']);
$p->set_price((string)$d['price']);
$p->set_manage_stock(true);
$p->set_stock_quantity(1);
$p->set_stock_status('instock');
$p->set_backorders('no');
$p->set_category_ids(array((int)$d['category_id']));
foreach ($d['meta'] as $key=>$value) {{
  if ($value !== '') {{ $p->update_meta_data($key, (string)$value); }}
}}
$id=$p->save();
if (!$id || $p->get_status('edit') !== 'draft' || $p->get_stock_quantity('edit') !== 1 || $p->get_backorders('edit') !== 'no') {{
 fwrite(STDERR, 'draft/stock/backorder verification failed'); exit(11);
}}
echo wp_json_encode(array('id'=>(int)$id,'status'=>$p->get_status('edit')));
"""
        result = self.eval_json(php)
        if not isinstance(result, dict) or result.get("status") != "draft":
            raise WPCliError(f"invalid draft create result for {record['sku']}")
        return int(result["id"])


def require_original_import_environment(wp_path: str) -> Path:
    require_apply_environment(wp_path)
    backup_raw = os.environ.get("RADMAN_DB_BACKUP_PATH", "")
    if not backup_raw:
        raise PipelineError("RADMAN_DB_BACKUP_PATH must name the pre-import database backup")
    backup = Path(backup_raw)
    if not backup.is_file() or backup.stat().st_size <= 0:
        raise PipelineError(f"database backup is missing or empty: {backup}")
    if "public_html" in str(backup):
        raise PipelineError("database backup cannot be stored under public_html")
    if not (backup.name.endswith(".sql") or backup.name.endswith(".sql.gz")):
        raise PipelineError("database backup must be a .sql or .sql.gz file")
    if time.time() - backup.stat().st_mtime > 6 * 60 * 60:
        raise PipelineError("database backup must be less than six hours old")
    return backup


def preflight_import(
    records: Sequence[Dict[str, Any]], gateway: LegacyDraftGateway
) -> List[Tuple[Dict[str, Any], str, Optional[int]]]:
    currency = gateway.get_currency()
    if currency != REQUIRED_CURRENCY:
        raise PipelineError(
            f"WooCommerce currency must be {REQUIRED_CURRENCY}; found {currency or 'blank'}"
        )
    decisions: List[Tuple[Dict[str, Any], str, Optional[int]]] = []
    sku_conflicts: List[str] = []
    seen_legacy_ids: set[str] = set()
    seen_skus: set[str] = set()
    for record in records:
        if record.get("import_action") != "CREATE_DRAFT":
            decisions.append((record, str(record.get("import_action")), None))
            continue
        legacy_id = str(record.get("legacy_id") or "")
        sku = str(record.get("sku") or "")
        if not legacy_id or not sku:
            raise PipelineError("import candidate is missing legacy ID or SKU")
        if legacy_id in seen_legacy_ids:
            raise PipelineError(f"duplicate legacy ID in prepared batch: {legacy_id}")
        if sku.casefold() in seen_skus:
            raise PipelineError(f"duplicate SKU in prepared batch: {sku}")
        seen_legacy_ids.add(legacy_id)
        seen_skus.add(sku.casefold())
        if record.get("image_qa_status") not in {"PASS", "FAIL"}:
            raise PipelineError(f"image QA is required before import: {sku}")
        selected_paths = [Path(path) for path in record.get("selected_import_paths", [])]
        if not selected_paths or any(not path.is_file() for path in selected_paths):
            raise PipelineError(f"selected ordered media is missing for {sku}")
        if record.get("pricing", {}).get("final_price_toman") is None:
            raise PipelineError(f"safe final Toman price is missing for {sku}")
        legacy_product_id = gateway.find_product_id_by_legacy_id(legacy_id)
        if legacy_product_id:
            decisions.append((record, "SKIP_EXISTING_LEGACY_ID", legacy_product_id))
            continue
        sku_product_id = gateway.find_product_id(str(record["sku"]))
        if sku_product_id:
            record["conflict"] = f"SKU exists on product {sku_product_id}"
            record["import_action"] = "STOP_SKU_CONFLICT"
            record["requires_review"] = True
            record.setdefault("review_reasons", []).append(record["conflict"])
            sku_conflicts.append(
                f"{record['sku']} conflicts with product {sku_product_id}"
            )
            decisions.append((record, "STOP_SKU_CONFLICT", sku_product_id))
            continue
        decisions.append((record, "CREATE_DRAFT", None))
    if sku_conflicts:
        raise PipelineError(
            "SKU conflict preflight stopped all mutation: " + "; ".join(sku_conflicts)
        )
    return decisions


def import_drafts(
    records: Sequence[Dict[str, Any]],
    *,
    gateway: LegacyDraftGateway,
) -> List[Dict[str, Any]]:
    decisions = preflight_import(records, gateway)
    actions: List[Dict[str, Any]] = []
    for record, decision, existing_id in decisions:
        if decision != "CREATE_DRAFT":
            record["import_action"] = decision
            record["wordpress_product_id"] = existing_id
            record["attachment_ids"] = []
            actions.append(
                {
                    "legacy_id": record.get("legacy_id"),
                    "sku": record.get("sku"),
                    "action": decision,
                    "product_id": existing_id,
                }
            )
            continue
        category_id = gateway.resolve_category_id(str(record["category"]))
        product_id = gateway.create_legacy_draft(record, category_id)
        attachment_ids = []
        for image_path in record.get("selected_import_paths", []):
            path = Path(image_path)
            if not path.is_file():
                raise PipelineError(f"selected import image is missing: {path}")
            attachment_ids.append(
                gateway.import_image(path, record["title"], product_id, record["sku"])
            )
        if attachment_ids:
            gateway.set_product_images(product_id, attachment_ids)
        record["import_action"] = "CREATED_DRAFT"
        record["wordpress_product_id"] = product_id
        record["attachment_ids"] = attachment_ids
        actions.append(
            {
                "legacy_id": record["legacy_id"],
                "sku": record["sku"],
                "action": "CREATED_DRAFT",
                "product_id": product_id,
                "attachment_ids": attachment_ids,
                "status": "draft",
                "stock": 1,
                "backorders": "no",
            }
        )
    return actions


def print_plan(private_dir: Path, limit: int) -> None:
    print("RADMAN original-product pipeline — PLAN ONLY")
    print(f"  source: https://noghrehmashhad.ir (public, robots-aware, automatic)")
    print(f"  maximum products: {limit} (hard cap {ORIGINAL_PRODUCT_MAX})")
    print(f"  private cache: {private_dir / 'legacy-cache'}")
    print("  currency: IRT; legacy prices are already Toman; conversion disabled")
    print("  image policy: aspect-preserving, color-gated; failed outputs use originals")
    print("  price rates: 590000 only for >=0.85 large-stone rings; otherwise 650000")
    print("  import: create-only WooCommerce drafts, stock=1, backorders=no")
    print("  mutation in this command: NONE")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--scrape-only", action="store_true")
    modes.add_argument("--image-qa", action="store_true")
    modes.add_argument("--pricing-preview", action="store_true")
    modes.add_argument("--import-drafts", action="store_true")
    modes.add_argument("--full-pilot", action="store_true")
    parser.add_argument("--limit", type=int, default=ORIGINAL_PRODUCT_MAX)
    parser.add_argument("--private-dir", type=Path, default=None)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--prepared-manifest", type=Path)
    parser.add_argument("--wp-path", default=os.environ.get("WP_PATH", ""))
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    private_dir = args.private_dir or Path(
        os.environ.get("RADMAN_PRIVATE_DIR", "/home/radmansi/private")
    )
    if not private_dir.is_absolute() or "public_html" in str(private_dir):
        print("[ERROR] RADMAN_PRIVATE_DIR must be an absolute private path outside public_html", file=sys.stderr)
        return 2
    if args.limit < 1 or args.limit > ORIGINAL_PRODUCT_MAX:
        print(f"[ERROR] --limit must be 1..{ORIGINAL_PRODUCT_MAX}", file=sys.stderr)
        return 2
    try:
        if args.plan:
            print_plan(private_dir, args.limit)
            return 0

        if args.scrape_only:
            manifest = scrape_original_products(private_dir, limit=args.limit)
            print(manifest["manifest_path"])
            return 0

        if args.import_drafts:
            require_original_import_environment(args.wp_path)
            prepared_path = args.prepared_manifest or latest_artifact(
                private_dir, "prepared-products.json"
            )
            prepared_path = require_private_artifact(prepared_path, private_dir)
            payload = read_json(prepared_path)
            records = payload.get("products", [])
            if not isinstance(records, list) or not records or len(records) > ORIGINAL_PRODUCT_MAX:
                raise PipelineError(
                    f"prepared manifest must contain 1..{ORIGINAL_PRODUCT_MAX} products"
                )
            validate_private_media(records, private_dir)
            gateway = LegacyDraftGateway(args.wp_path)
            run_dir = prepared_path.parent
            try:
                actions = import_drafts(records, gateway=gateway)
            except PipelineError:
                # Preserve conflict/review evidence even though preflight made no mutation.
                write_json(prepared_path, {**payload, "products": records})
                write_reports(records, run_dir, payload.get("scrape_skipped", []))
                raise
            write_json(run_dir / "import-actions.json", {"actions": actions})
            write_json(prepared_path, {**payload, "products": records, "import_actions": actions})
            write_reports(records, run_dir, payload.get("scrape_skipped", []))
            print(f"[IMPORT] {len(actions)} action(s); all creations remain DRAFT")
            return 0

        if args.full_pilot:
            source = scrape_original_products(private_dir, limit=args.limit)
            source_path = Path(str(source["manifest_path"]))
        else:
            source_path = args.source_manifest or latest_artifact(private_dir, "scrape.json")
        source_path = require_private_artifact(source_path, private_dir)
        source_payload = read_json(source_path)
        scrape_skipped = (
            source_payload.get("skipped", []) if isinstance(source_payload, dict) else []
        )
        products = load_products(source_path)
        run_dir = private_dir / "legacy-cache" / "runs" / timestamp_slug()
        run_qa = bool(args.image_qa or args.full_pilot)
        records = prepare_products(
            products,
            private_dir=private_dir,
            run_dir=run_dir,
            run_image_qa=run_qa,
        )
        prepared_path = run_dir / "prepared-products.json"
        write_json(
            prepared_path,
            {
                "generated_at": now_tehran().isoformat(),
                "timezone": "Asia/Tehran",
                "pipeline_version": PIPELINE_VERSION,
                "legacy_prices_are_toman": True,
                "source_manifest": str(source_path),
                "scrape_skipped": scrape_skipped,
                "products": records,
            },
        )
        csv_path, summary_path = write_reports(records, run_dir, scrape_skipped)
        print(f"[REPORT] {csv_path}")
        print(f"[REPORT] {summary_path}")

        if args.full_pilot:
            require_original_import_environment(args.wp_path)
            validate_private_media(records, private_dir)
            try:
                actions = import_drafts(records, gateway=LegacyDraftGateway(args.wp_path))
            except PipelineError:
                write_json(
                    prepared_path,
                    {
                        "generated_at": now_tehran().isoformat(),
                        "timezone": "Asia/Tehran",
                        "pipeline_version": PIPELINE_VERSION,
                        "legacy_prices_are_toman": True,
                        "source_manifest": str(source_path),
                        "scrape_skipped": scrape_skipped,
                        "products": records,
                    },
                )
                write_reports(records, run_dir, scrape_skipped)
                raise
            write_json(run_dir / "import-actions.json", {"actions": actions})
            write_json(
                prepared_path,
                {
                    "generated_at": now_tehran().isoformat(),
                    "timezone": "Asia/Tehran",
                    "pipeline_version": PIPELINE_VERSION,
                    "legacy_prices_are_toman": True,
                    "source_manifest": str(source_path),
                    "scrape_skipped": scrape_skipped,
                    "products": records,
                    "import_actions": actions,
                },
            )
        return 0
    except (PipelineError, WPCliError, OSError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
