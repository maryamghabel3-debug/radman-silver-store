#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Pricing Engine Agent
----------------------------------------
Reads daily silver rate (Toman/gram) from
    RADMAN_PRIVATE_DIR/state/daily_rate.txt   (single integer, e.g. 85000)
and recomputes WooCommerce regular_price for products tagged
radman_pricing_mode in {silver_weight_only, silver_weight_plus_stone}.

Products in manual_locked or legacy_mirror are SKIPPED.  Products missing
required meta (silver_weight_grams) are reported but not touched.

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
    try:
        rate = int(float(raw))
    except ValueError as e:
        raise ValueError(f"Invalid daily rate in {rate_path!r}: {raw!r}") from e
    if rate <= 0:
        raise ValueError(f"Daily rate must be a positive integer (got {rate})")
    return rate


def fetch_products(env: rc.Env, logger) -> List[Dict[str, Any]]:
    """Fetch all published products with their meta.  Uses wc product list with
    --fields including meta_data via a small wrapper: we list IDs + basic fields
    and then query meta per product via wp post meta list (wp-cli is the only
    guaranteed channel on cPanel).
    """
    try:
        rows = rc.wp_json(env, [
            "wc", "product", "list",
            "--status=publish",
            "--limit=500",
            "--fields=id,name,sku,regular_price,price,status",
        ])
    except rc.WPCliError as e:
        logger.error("wc product list failed: %s", rc.redact(str(e), env))
        return []
    if not isinstance(rows, list):
        return []
    products: List[Dict[str, Any]] = []
    for r in rows:
        try:
            pid = int(r.get("id", 0))
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue
        meta = fetch_product_meta(env, pid, logger)
        products.append({
            "id": pid,
            "name": str(r.get("name", "")),
            "sku": str(r.get("sku", "")),
            "regular_price": str(r.get("regular_price") or r.get("price") or "0"),
            "meta": meta,
        })
    return products


def fetch_product_meta(env: rc.Env, pid: int, logger) -> Dict[str, Any]:
    """Return a dict of flattened meta_key -> scalar value for a product,
    using wp post meta list (--format=json)."""
    try:
        raw = rc.wp_json(env, ["post", "meta", "list", str(pid)])
    except rc.WPCliError as e:
        logger.warning("post meta list failed for product %s: %s", pid, rc.redact(str(e), env))
        return {}
    out: Dict[str, Any] = {}
    if not isinstance(raw, list):
        return out
    for m in raw:
        k = str(m.get("meta_key", ""))
        v = m.get("meta_value", "")
        # Skip hidden/internal keys
        if k.startswith("_") and k not in ("_regular_price", "_price", "_stock_status"):
            continue
        out[k] = v
    return out


def compute_new_price(meta: Dict[str, Any], rate: int) -> Tuple[Optional[int], str]:
    """Return (new_price_toman, reason) where reason is one of:
       'calc-weight', 'calc-weight-stone', 'skip-manual', 'skip-legacy',
       'skip-missing-weight', 'skip-bad-weight', 'skip-bad-stone'.
    """
    mode = str(meta.get(rc.META_PRICING_MODE, "")).strip()
    if mode == rc.MODE_MANUAL_LOCKED:
        return None, "skip-manual"
    if mode == rc.MODE_LEGACY_MIRROR:
        return None, "skip-legacy"

    # Weight-based modes
    w_raw = meta.get(rc.META_WEIGHT_G)
    try:
        weight = float(str(w_raw).strip()) if w_raw not in (None, "", "0") else 0.0
    except (TypeError, ValueError):
        return None, "skip-bad-weight"
    if weight <= 0:
        return None, "skip-missing-weight"

    base = weight * rate
    if mode == rc.MODE_WEIGHT_PLUS_STONE:
        s_raw = meta.get(rc.META_STONE_VALUE)
        if s_raw in (None, "", "0"):
            return None, "skip-missing-stone"
        try:
            stone = int(float(str(s_raw).replace(",", "") or "0"))
        except (TypeError, ValueError):
            return None, "skip-bad-stone"
        if stone < 0:
            return None, "skip-bad-stone"
        return rc.round_to_step(base + stone), "calc-weight-stone"

    # default: silver_weight_only (even if mode not explicitly set but weight present)
    return rc.round_to_step(base), "calc-weight"


def format_preview_table(rows: List[Dict[str, Any]], top: int = 20) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("  RADMAN PRICE ENGINE — PREVIEW")
    lines.append("=" * 78)
    calc = [r for r in rows if r.get("reason", "").startswith("calc")]
    skips = [r for r in rows if r.get("reason", "").startswith("skip")]
    lines.append(f"  Weight-based products to update : {len(calc)}")
    by_reason: Dict[str, int] = {}
    for r in skips:
        by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + 1
    for k, v in sorted(by_reason.items()):
        lines.append(f"  Skipped ({k}): {v}")
    lines.append("-" * 78)
    lines.append(f"{'SKU':<20}{'OLD':>14}{'NEW':>14}{'Δ%':>8}  MODE")
    lines.append("-" * 78)
    shown = 0
    for r in sorted(calc, key=lambda x: abs(x.get("delta_pct", 0)), reverse=True):
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


def apply_prices(env: rc.Env, to_update: List[Dict[str, Any]], logger) -> Path:
    """Apply new prices via wp-cli. Returns CSV backup path."""
    backups = Path(env.RADMAN_PRIVATE_DIR) / "backups"
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = backups / f"prices-{ts}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "sku", "old_regular_price", "new_regular_price", "mode", "rate"])
        for r in to_update:
            w.writerow([
                r["id"], r["sku"], r.get("old_price_int", 0), r["new_price"],
                r["reason"], r.get("rate", 0),
            ])
    os.chmod(csv_path, 0o600)
    logger.info("Pre-change CSV backup written: %s", csv_path)

    applied = 0
    for r in to_update:
        pid = r["id"]
        new_price = r["new_price"]
        try:
            rc.wp_cli(env, [
                "wc", "product", "update", str(pid),
                f"--regular_price={new_price}",
            ])
            applied += 1
        except rc.WPCliError as e:
            logger.error("Failed to update product %s: %s", pid, rc.redact(str(e), env))
    logger.info("Applied price updates to %d/%d products.", applied, len(to_update))
    return csv_path


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

        products = fetch_products(env, logger)
        logger.info("Fetched %d products.", len(products))

        rows: List[Dict[str, Any]] = []
        for p in products:
            new_price, reason = compute_new_price(p["meta"], rate)
            try:
                old = int(float(str(p["regular_price"]).replace(",", "") or "0"))
            except (TypeError, ValueError):
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
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        outbox_path = Path(env.RADMAN_PRIVATE_DIR) / "outbox" / f"price_preview_{ts}.txt"
        outbox_path.write_text(preview + "\n", encoding="utf-8")
        os.chmod(outbox_path, 0o600)
        logger.info("Preview written to %s", outbox_path)

        will_apply = args.apply and (not env.DRY_RUN)
        if will_apply:
            if not to_update:
                logger.info("No price changes needed; nothing to apply.")
            else:
                backup = apply_prices(env, to_update, logger)
                logger.info("APPLY complete. Backup: %s", backup)
        else:
            logger.info("DRY_RUN or no --apply flag; no prices written.")

        return 0
    finally:
        lock.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(run())
