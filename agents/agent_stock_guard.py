#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Stock Guard Agent (cron: hourly)
----------------------------------------------------
Read-only agent that audits WooCommerce inventory integrity and writes a
human-readable report to RADMAN_PRIVATE_DIR/outbox/stock_report_<ts>.txt.

Checks performed (pure read, never mutates):
  1. Products with stock_quantity=0 but stock_status='instock' (visible but sold out).
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
    try:
        rows = rc.wp_json(env, [
            "wc", "product", "list",
            "--status=publish",
            f"--limit={limit}",
            "--fields=id,name,sku,manage_stock,stock_quantity,stock_status,status,type",
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
        meta = {}
        try:
            meta_raw = rc.wp_json(env, ["post", "meta", "list", str(pid)])
            if isinstance(meta_raw, list):
                for m in meta_raw:
                    k = str(m.get("meta_key", ""))
                    if k.startswith("_") and k not in ("_stock", "_stock_status", "_manage_stock"):
                        continue
                    meta[k] = m.get("meta_value", "")
        except rc.WPCliError:
            # If a meta fetch fails for one product, continue with empty meta.
            pass
        products.append({
            "id": pid,
            "name": str(r.get("name", "")),
            "sku": str(r.get("sku", "")),
            "manage_stock": bool(r.get("manage_stock", False)),
            "stock_quantity": _safe_int(r.get("stock_quantity")),
            "stock_status": str(r.get("stock_status", "")),
            "type": str(r.get("type", "")),
            "meta": meta,
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
        qty = p.get("stock_quantity", 0)
        status = p.get("stock_status", "")
        meta = p.get("meta", p.get("_meta", {}))
        mode = str(meta.get(rc.META_PRICING_MODE, "")).strip()

        # 1. stock=0 but instock (still visible)
        if qty <= 0 and status == "instock":
            buckets["zero_but_instock"].append(p)
        # 2. negative stock
        if qty < 0:
            buckets["negative_stock"].append(p)
        # 3. weight-based but missing weight meta
        if mode in (rc.MODE_WEIGHT_ONLY, rc.MODE_WEIGHT_PLUS_STONE):
            w = meta.get(rc.META_WEIGHT_G)
            try:
                wf = float(str(w).replace(",", "")) if w not in (None, "") else 0.0
            except (TypeError, ValueError):
                wf = 0.0
            if wf <= 0:
                buckets["missing_weight_meta"].append(p)
            # 4. weight+stone mode missing stone value
            if mode == rc.MODE_WEIGHT_PLUS_STONE:
                s = meta.get(rc.META_STONE_VALUE)
                try:
                    sv = int(float(str(s).replace(",", "") or "0"))
                except (TypeError, ValueError):
                    sv = -1
                if sv < 0:
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
        ("zero_but_instock",
         "⚠  محصولات با موجودی صفر اما وضعیت instock (قابل‌مشاهده/خرید):"),
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
            pid = p["id"]
            sku = p["sku"] or f"#{pid}"
            name = (p["name"] or "")[:40]
            lines.append(f"  {pid:<8}{sku[:22]:<22} {qty:>5}  {name}")
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
        products = fetch_products(env, args.limit, logger)
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
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        outbox = Path(env.RADMAN_PRIVATE_DIR) / "outbox" / f"stock_report_{ts}.txt"
        outbox.write_text(report + "\n", encoding="utf-8")
        os.chmod(outbox, 0o600)
        logger.info("Report written to %s", outbox)
        return 0
    finally:
        lock.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(run())
