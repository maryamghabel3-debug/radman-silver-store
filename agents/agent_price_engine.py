#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Pricing Engine Agent
----------------------------------------
Reads daily silver rate (Toman/gram) from
    RADMAN_PRIVATE_DIR/state/daily_rate.txt   (single integer, e.g. 85000)
and recomputes WooCommerce regular_price according to all four official
pricing modes. silver_weight_only and silver_weight_plus_stone are calculated;
legacy_mirror copies legacy_price_toman; manual_locked is reported and never
automatically overwritten. Products with missing/unknown metadata are skipped.

Modes:
  DRY_RUN=1 (default):  prints a preview table, saves to
                        outbox/price_preview_<ts>.txt, does NOT write to WP.
  DRY_RUN=0:            writes prices via wp-cli (wc product update or
                        post meta update); creates a CSV backup of prior
                        prices to backups/prices-<ts>.csv.

Never touches payment/SMS/Redis/analytics.  HITL is preserved: owner writes
the daily rate file manually (or via future input agent); DRY_RUN default
means a preview is always produced first.
"""

from __future__ import annotations

import os
import sys
import csv
import argparse
import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

from lib import radman_common as rc  # noqa: E402


AGENT_NAME = "price_engine"
RATE_FILENAME = "daily_rate.txt"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RADMAN Pricing Engine")
    p.add_argument("--env-file", help="Path to staging.env")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   help="Force preview / no writes (default if DRY_RUN env != 0)")
    p.add_argument("--apply", action="store_true",
                   help="Apply price changes (also requires DRY_RUN=0 env)")
    p.add_argument("--rate", type=int, default=0,
                   help="Override daily rate (Toman/gram) instead of reading state file")
    p.add_argument("--top", type=int, default=20, help="Preview top N changes in stdout")
    return p.parse_args(argv)


def read_daily_rate(env: rc.Env, override: int) -> int:
    """Return daily rate (Toman/gram).  Raises ValueError if unavailable/invalid."""
    if override and override > 0:
        return override
    rate_path = Path(env.RADMAN_PRIVATE_DIR) / "state" / RATE_FILENAME
    if not rate_path.is_file():
        raise ValueError(
            f"Daily rate file missing: {rate_path}. "
            "Owner must write one integer (Toman/gram) into this file."
        )
    raw = rate_path.read_text(encoding="utf-8").strip().replace(",", "")
    if not raw.isdigit():
        raise ValueError(f"Invalid daily rate in {rate_path!r}: expected one positive integer")
    rate = int(raw)
    if rate <= 0:
        raise ValueError(f"Daily rate must be a positive integer (got {rate})")
    return rate


def fetch_products(env: rc.Env, logger) -> List[Dict[str, Any]]:
    """Fetch all published WooCommerce products and required metadata in one
    HPOS-safe `wp eval` subprocess (never REST)."""
    meta_keys = sorted(set(
        rc.META_PRICING_MODE_KEYS
        + rc.META_WEIGHT_G_KEYS
        + rc.META_STONE_VALUE_KEYS
        + rc.META_LEGACY_PRICE_KEYS
        + rc.META_MANUAL_PRICE_KEYS
    ))
    php_keys = ",".join("'" + key.replace("'", "\\'") + "'" for key in meta_keys)
    php_code = f'''
if (!function_exists('wc_get_products')) {{ fwrite(STDERR, "WooCommerce unavailable\\n"); exit(3); }}
$keys = array({php_keys});
$products = wc_get_products(array('status' => 'publish', 'limit' => -1, 'return' => 'objects'));
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
    'regular_price' => $product->get_regular_price('edit'),
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
        products.append({
            "id": pid,
            "name": str(row.get("name", "")),
            "sku": str(row.get("sku", "")),
            "regular_price": str(row.get("regular_price") or "0"),
            "meta": row.get("meta") if isinstance(row.get("meta"), dict) else {},
        })
    return products


def _positive_decimal(value: Any) -> Optional[Decimal]:
    try:
        parsed = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed > 0 else None


def _nonnegative_toman(value: Any) -> Optional[int]:
    try:
        parsed = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    if parsed < 0:
        return None
    return int(parsed.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compute_new_price(meta: Dict[str, Any], rate: int) -> Tuple[Optional[int], str]:
    """Return `(new_price_toman, reason)` for the four locked modes.

    Only `silver_weight_only` is rounded to the nearest 10,000 Toman, exactly
    as specified. Weight-plus-stone preserves the fixed stone valuation and is
    rounded only to a whole Toman. `legacy_mirror` copies its explicit legacy
    price. `manual_locked` is never changed.
    """
    mode = str(rc.meta_get(meta, rc.META_PRICING_MODE_KEYS, "")).strip()
    if not mode:
        return None, "skip-missing-mode"
    if mode == rc.MODE_MANUAL_LOCKED:
        return None, "skip-manual-locked"
    if mode == rc.MODE_LEGACY_MIRROR:
        legacy_raw = rc.meta_get(meta, rc.META_LEGACY_PRICE_KEYS, "")
        legacy_price = _nonnegative_toman(legacy_raw)
        if legacy_price is None or legacy_price <= 0:
            return None, "skip-missing-legacy-price"
        return legacy_price, "mirror-legacy"
    if mode not in (rc.MODE_WEIGHT_ONLY, rc.MODE_WEIGHT_PLUS_STONE):
        return None, "skip-unknown-mode"

    w_raw = rc.meta_get(meta, rc.META_WEIGHT_G_KEYS, "")
    weight = _positive_decimal(w_raw)
    if weight is None:
        return None, "skip-missing-or-bad-weight"

    base = weight * Decimal(rate)
    if mode == rc.MODE_WEIGHT_PLUS_STONE:
        s_raw = rc.meta_get(meta, rc.META_STONE_VALUE_KEYS, "")
        stone = _nonnegative_toman(s_raw)
        if stone is None or stone <= 0:
            return None, "skip-missing-or-bad-stone"
        total = base + Decimal(stone)
        return int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)), "calc-weight-stone"

    return rc.round_to_step(base), "calc-weight"


def format_preview_table(rows: List[Dict[str, Any]], top: int = 20) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("  RADMAN PRICE ENGINE — PREVIEW")
    lines.append("=" * 78)
    calculated = [r for r in rows if r.get("new_price") is not None]
    skips = [r for r in rows if r.get("reason", "").startswith("skip")]
    by_mode: Dict[str, int] = {}
    for r in calculated:
        by_mode[r["reason"]] = by_mode.get(r["reason"], 0) + 1
    lines.append(f"  Products with computed/mirrored price : {len(calculated)}")
    for k, v in sorted(by_mode.items()):
        lines.append(f"  Eligible ({k}): {v}")
    by_reason: Dict[str, int] = {}
    for r in skips:
        by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + 1
    for k, v in sorted(by_reason.items()):
        lines.append(f"  Skipped ({k}): {v}")
    lines.append("-" * 78)
    lines.append(f"{'SKU':<20}{'OLD':>14}{'NEW':>14}{'Δ%':>8}  MODE")
    lines.append("-" * 78)
    shown = 0
    for r in sorted(calculated, key=lambda x: abs(x.get("delta_pct", 0)), reverse=True):
        if shown >= top:
            break
        old = r.get("old_price_int") or 0
        new = r.get("new_price") or 0
        pct = r.get("delta_pct", 0.0)
        sku_label = r["sku"] or f"pid={r['id']}"
        lines.append(
            f"{sku_label:<20}"
            f"{rc.toman_str(old):>14}"
            f"{rc.toman_str(new):>14}"
            f"{pct:>7.1f}%  {r['reason']}"
        )
        shown += 1
    lines.append("-" * 78)
    lines.append("DRY_RUN=1 — no prices written. Re-run with --apply + DRY_RUN=0 to apply.")
    lines.append("=" * 78)
    return "\n".join(lines)


def apply_prices(env: rc.Env, to_update: List[Dict[str, Any]], logger) -> Tuple[Path, int]:
    """Write a complete pre-change CSV, then save products through WooCommerce
    objects invoked by wp-cli. Returns `(backup_path, failure_count)`."""
    backups = Path(env.RADMAN_PRIVATE_DIR) / "backups"
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    csv_path = backups / f"prices-{ts}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "sku", "old_regular_price", "new_regular_price", "mode", "rate"])
        for r in to_update:
            w.writerow([
                r["id"], r["sku"], r.get("old_price_int", 0), r["new_price"],
                r["reason"], r.get("rate", 0),
            ])
        f.flush()
        os.fsync(f.fileno())
    os.chmod(csv_path, 0o600)
    logger.info("Pre-change CSV backup written: %s", csv_path)

    applied = 0
    failures = 0
    for r in to_update:
        pid = int(r["id"])
        new_price = int(r["new_price"])
        php_code = f'''
$product = function_exists('wc_get_product') ? wc_get_product({pid}) : false;
if (!$product) {{ fwrite(STDERR, "Product not found\\n"); exit(4); }}
$product->set_regular_price('{new_price}');
$product->set_price('{new_price}');
$product->save();
delete_post_meta({pid}, '_sale_price');
update_post_meta({pid}, '_price', '{new_price}');
wc_delete_product_transients({pid});
echo (string) $product->get_id();
'''
        try:
            result = rc.wp_cli(env, ["eval", php_code])
            if result.strip() != str(pid):
                raise rc.WPCliError(f"price update verification failed for product {pid}")
            applied += 1
        except rc.WPCliError as e:
            failures += 1
            logger.error("Failed to update product %s: %s", pid, rc.redact(str(e), env))
    logger.info("Applied price updates to %d/%d products (failures=%d).", applied, len(to_update), failures)
    return csv_path, failures


def run(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    env = rc.Env(env_path=args.env_file)
    if args.dry_run:
        env.DRY_RUN = True
    if args.apply and env.DRY_RUN:
        # --apply only works when DRY_RUN=0 in env AND flag given
        pass
    logger = rc.get_logger(env, AGENT_NAME)

    try:
        env.require_staging()
    except RuntimeError as e:
        logger.error("STAGING GUARD FAILED: %s", rc.redact(str(e), env))
        return 2

    # Private dirs
    for sub in ("state", "outbox", "backups", "logs"):
        (Path(env.RADMAN_PRIVATE_DIR) / sub).mkdir(parents=True, exist_ok=True, mode=0o700)

    lock = rc.FileLock(Path(env.RADMAN_PRIVATE_DIR) / "state" / f"{AGENT_NAME}.lock")
    try:
        lock.__enter__()
    except RuntimeError as e:
        logger.warning("Lock busy; exiting: %s", e)
        return 0

    try:
        try:
            rate = read_daily_rate(env, args.rate)
        except ValueError as e:
            logger.error(str(e))
            print(f"[ERROR] {e}", file=sys.stderr)
            return 3
        logger.info("Daily rate loaded: %s Toman/gram (dry_run=%s)", rate, env.DRY_RUN)

        try:
            products = fetch_products(env, logger)
        except rc.WPCliError:
            return 4
        logger.info("Fetched %d products.", len(products))

        rows: List[Dict[str, Any]] = []
        for p in products:
            new_price, reason = compute_new_price(p["meta"], rate)
            try:
                old_decimal = Decimal(str(p["regular_price"]).replace(",", "") or "0")
                old = int(old_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            except (InvalidOperation, TypeError, ValueError):
                old = 0
            delta_pct = 0.0
            if old > 0 and new_price is not None:
                delta_pct = (new_price - old) / old * 100.0
            rows.append({
                "id": p["id"],
                "sku": p["sku"],
                "name": p["name"],
                "old_price_int": old,
                "new_price": new_price,
                "reason": reason,
                "delta_pct": delta_pct,
                "rate": rate,
            })

        to_update = [r for r in rows if r["new_price"] is not None and r["new_price"] != r["old_price_int"]]
        # Also include products where new == old? No churn needed.
        preview = format_preview_table(rows, top=args.top)
        print(preview)

        # Save preview to outbox always
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        outbox_path = Path(env.RADMAN_PRIVATE_DIR) / "outbox" / f"price_preview_{ts}.txt"
        rc.write_text_atomic(outbox_path, preview + "\n")
        logger.info("Preview written to %s", outbox_path)

        will_apply = args.apply and (not env.DRY_RUN)
        if will_apply:
            if not to_update:
                logger.info("No price changes needed; nothing to apply.")
            else:
                backup, failures = apply_prices(env, to_update, logger)
                if failures:
                    logger.error("APPLY incomplete: %d product update(s) failed. Backup: %s", failures, backup)
                    return 5
                logger.info("APPLY complete. Backup: %s", backup)
        else:
            logger.info("DRY_RUN or no --apply flag; no prices written.")

        return 0
    finally:
        lock.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(run())
