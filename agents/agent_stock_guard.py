#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Stock Guard Agent (cron: hourly)
----------------------------------------------------
Read-only agent that audits WooCommerce inventory integrity and writes a
human-readable report to RADMAN_PRIVATE_DIR/outbox/stock_report_<ts>.txt.

Checks performed (pure read, never mutates):
  1. Published/catalog-visible products with managed stock_quantity=0.
  2. Products with stock_quantity<0 (oversell anomaly).
  3. Products in weight-based pricing modes (silver_weight_only /
     silver_weight_plus_stone) that are missing silver_weight_grams meta.
  4. Products in silver_weight_plus_stone missing stone_fixed_value_toman.
  5. Products with radman_pricing_mode set but manage_stock != true (oversell risk).
  6. Duplicate SKUs (if any).

Always DRY_RUN-safe; this agent NEVER changes the database.
"""

from __future__ import annotations

import os
import sys
import argparse
import datetime as dt
from pathlib import Path
from typing import Dict, List, Any, Optional, DefaultDict
from collections import defaultdict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

from lib import radman_common as rc  # noqa: E402


AGENT_NAME = "stock_guard"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RADMAN Stock Guard (read-only)")
    p.add_argument("--env-file", help="Path to staging.env")
    p.add_argument("--limit", type=int, default=500, help="Max products to scan")
    return p.parse_args(argv)


def fetch_products(env: rc.Env, limit: int, logger) -> List[Dict[str, Any]]:
    """Read products through one `wp eval` subprocess (never REST)."""
    scan_limit = max(1, min(int(limit), 5000))
    meta_keys = sorted(set(
        rc.META_PRICING_MODE_KEYS + rc.META_WEIGHT_G_KEYS + rc.META_STONE_VALUE_KEYS
    ))
    php_keys = ",".join("'" + key.replace("'", "\\'") + "'" for key in meta_keys)
    php_code = f'''
if (!function_exists('wc_get_products')) {{ fwrite(STDERR, "WooCommerce unavailable\\n"); exit(3); }}
$keys = array({php_keys});
$products = wc_get_products(array('status' => 'publish', 'limit' => {scan_limit}, 'return' => 'objects'));
$out = array();
foreach ($products as $product) {{
  $meta = array();
  foreach ($keys as $key) {{
    $value = $product->get_meta($key, true, 'edit');
    if ($value !== '' && $value !== null) {{ $meta[$key] = $value; }}
  }}
  $out[] = array(
    'id' => $product->get_id(),
    'name' => $product->get_name('edit'),
    'sku' => $product->get_sku('edit'),
    'manage_stock' => $product->managing_stock(),
    'stock_quantity' => $product->get_stock_quantity('edit'),
    'stock_status' => $product->get_stock_status('edit'),
    'catalog_visibility' => $product->get_catalog_visibility('edit'),
    'type' => $product->get_type(),
    'meta' => $meta,
  );
}}
echo wp_json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
'''
    try:
        rows = rc.wp_eval_json(env, php_code, timeout=300)
    except rc.WPCliError as e:
        logger.error("WooCommerce product query failed: %s", rc.redact(str(e), env))
        raise
    if not isinstance(rows, list):
        return []
    products: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            pid = int(row.get("id", 0))
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue
        raw_qty = row.get("stock_quantity")
        products.append({
            "id": pid,
            "name": str(row.get("name", "")),
            "sku": str(row.get("sku", "")),
            "manage_stock": row.get("manage_stock") is True or str(row.get("manage_stock", "")).lower() in ("1", "true", "yes"),
            "stock_quantity": _safe_int(raw_qty) if raw_qty not in (None, "") else None,
            "stock_status": str(row.get("stock_status", "")),
            "catalog_visibility": str(row.get("catalog_visibility", "visible")),
            "type": str(row.get("type", "")),
            "meta": row.get("meta") if isinstance(row.get("meta"), dict) else {},
        })
    return products


def _safe_int(v: Any) -> int:
    if v is None or v == "":
        return 0
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def scan(products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    buckets: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    seen_skus: Dict[str, int] = {}

    for p in products:
        pid = p["id"]
        sku = p.get("sku", "") or f"<no-sku>#{pid}"
        qty = p.get("stock_quantity")
        status = p.get("stock_status", "")
        visibility = p.get("catalog_visibility", "visible")
        meta = p.get("meta", p.get("_meta", {}))
        mode = str(rc.meta_get(meta, rc.META_PRICING_MODE_KEYS, "")).strip()

        # 1. managed stock=0 while product remains catalog-visible. This is an
        # anomaly report only; no visibility/stock status is changed.
        if p.get("manage_stock") and qty == 0 and visibility != "hidden":
            buckets["zero_visible"].append(p)
        # 2. negative stock
        if qty is not None and qty < 0:
            buckets["negative_stock"].append(p)
        # 3. weight-based but missing weight meta
        if mode in (rc.MODE_WEIGHT_ONLY, rc.MODE_WEIGHT_PLUS_STONE):
            w = rc.meta_get(meta, rc.META_WEIGHT_G_KEYS, "")
            try:
                wf = float(str(w).replace(",", "")) if w not in (None, "") else 0.0
            except (TypeError, ValueError):
                wf = 0.0
            if wf <= 0:
                buckets["missing_weight_meta"].append(p)
            # 4. weight+stone mode missing stone value
            if mode == rc.MODE_WEIGHT_PLUS_STONE:
                s = rc.meta_get(meta, rc.META_STONE_VALUE_KEYS, "")
                try:
                    sv = int(float(str(s).replace(",", "") or "0"))
                except (TypeError, ValueError):
                    sv = -1
                if sv <= 0:
                    buckets["missing_stone_value"].append(p)
            # 5. mode set but manage_stock not enabled (oversell risk)
            if not p["manage_stock"]:
                buckets["mode_no_manage_stock"].append(p)
        # 6. duplicate SKU
        if sku in seen_skus:
            buckets["duplicate_sku"].append(p)
        elif sku and not sku.startswith("<no-sku>"):
            seen_skus[sku] = pid

    return buckets


def render_report(buckets: Dict[str, List[Dict[str, Any]]], rate_note: str) -> str:
    lines: List[str] = []
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append("=" * 78)
    lines.append("  RADMAN STOCK GUARD — READ-ONLY INVENTORY REPORT")
    lines.append(f"  Generated: {ts}")
    if rate_note:
        lines.append(f"  Note: {rate_note}")
    lines.append("=" * 78)

    SECTIONS = [
        ("zero_visible",
         "⚠  محصولات منتشرشده/قابل‌مشاهده با موجودی مدیریت‌شده صفر:"),
        ("negative_stock",
         "⚠  محصولات با موجودی منفی (oversell anomaly):"),
        ("missing_weight_meta",
         "⚠  محصولات weight-based فاقد meta silver_weight_grams:"),
        ("missing_stone_value",
         "⚠  محصولات silver_weight_plus_stone فاقد meta stone_fixed_value_toman:"),
        ("mode_no_manage_stock",
         "⚠  محصولات با pricing mode ثبت‌شده ولی manage_stock=false (ریسک oversell):"),
        ("duplicate_sku",
         "⚠  SKU تکراری (باید یکتا باشد):"),
    ]
    any_issue = False
    for key, header in SECTIONS:
        items = buckets.get(key, [])
        if not items:
            continue
        any_issue = True
        lines.append("")
        lines.append(header + f"  (تعداد: {len(items)})")
        lines.append("-" * 78)
        lines.append(f"  {'ID':<8}{'SKU':<22} {'QTY':>5}  NAME")
        for p in items[:50]:
            qty = p["stock_quantity"]
            qty_label = "—" if qty is None else str(qty)
            pid = p["id"]
            sku = p["sku"] or f"#{pid}"
            name = (p["name"] or "")[:40]
            lines.append(f"  {pid:<8}{sku[:22]:<22} {qty_label:>5}  {name}")
        if len(items) > 50:
            lines.append(f"  ... and {len(items) - 50} more")
    if not any_issue:
        lines.append("")
        lines.append("  ✅ هیچ مشکل موجودی/متادیتایی پیدا نشد.")
    lines.append("")
    lines.append("=" * 78)
    lines.append("  This is a READ-ONLY report; no changes were made to WooCommerce.")
    lines.append("=" * 78)
    return "\n".join(lines)


def run(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    env = rc.Env(env_path=args.env_file)
    logger = rc.get_logger(env, AGENT_NAME)
    try:
        env.require_staging()
    except RuntimeError as e:
        logger.error("STAGING GUARD FAILED: %s", rc.redact(str(e), env))
        return 2

    for sub in ("state", "outbox", "logs"):
        (Path(env.RADMAN_PRIVATE_DIR) / sub).mkdir(parents=True, exist_ok=True, mode=0o700)

    lock = rc.FileLock(Path(env.RADMAN_PRIVATE_DIR) / "state" / f"{AGENT_NAME}.lock")
    try:
        lock.__enter__()
    except RuntimeError as e:
        logger.warning("Lock busy; exiting: %s", e)
        return 0

    try:
        try:
            products = fetch_products(env, args.limit, logger)
        except rc.WPCliError:
            return 4
        logger.info("Scanned %d products.", len(products))
        buckets = scan(products)
        rate_note = ""
        # Read daily rate if present, just to annotate the report
        rate_path = Path(env.RADMAN_PRIVATE_DIR) / "state" / "daily_rate.txt"
        if rate_path.is_file():
            try:
                rv = int(float(rate_path.read_text(encoding="utf-8").strip().replace(",", "") or "0"))
                if rv > 0:
                    rate_note = f"نرخ روز نقره = {rc.toman_str(rv)} تومان/گرم"
            except ValueError:
                pass
        report = render_report(buckets, rate_note)
        print(report)
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        outbox = Path(env.RADMAN_PRIVATE_DIR) / "outbox" / f"stock_report_{ts}.txt"
        rc.write_text_atomic(outbox, report + "\n")
        logger.info("Report written to %s", outbox)
        return 0
    finally:
        lock.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(run())
