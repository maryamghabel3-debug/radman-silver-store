#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Order Watch Agent (cron: every 5 minutes)
-------------------------------------------------------------
Runs on the staging (and later production) host via cron.  Polls WooCommerce
for new orders in 'processing' or 'on-hold' since the last seen ID stored in
RADMAN_PRIVATE_DIR/state/order_watch.json.  For each new order it composes a
concise Persian SMS notification to the owner (order ID, items, total in
Toman, customer city).

Default mode is DRY_RUN=1: notifications are written to outbox/sms-<ts>.txt.
If KAVENEGAR_API_KEY and OWNER_MOBILE are set in staging.env AND DRY_RUN=0,
it sends the SMS via Kavenegar REST API.  Order status is NEVER auto-changed;
HITL is strictly preserved.

Secrets are ONLY read from staging.env.  Telegram is NOT used.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import datetime as dt
from pathlib import Path
from typing import Dict, List, Any, Optional

# Make sure we can import lib/ when run directly or via launcher
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

from lib import radman_common as rc  # noqa: E402


STATE_FILENAME = "order_watch.json"
AGENT_NAME = "order_watch"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RADMAN Order Watch Agent")
    p.add_argument("--env-file", help="Path to staging.env (default: ~/.config/radman/staging.env)")
    p.add_argument("--dry-run", dest="dry_run", action="store_true",
                   help="Force dry run (write notifications to outbox, do NOT send)")
    p.add_argument("--force-rescan", action="store_true",
                   help="Re-process all processing/on-hold orders regardless of last-seen ID")
    p.add_argument("--lookback", type=int, default=50,
                   help="If no state file exists, look at most N latest orders (default 50)")
    return p.parse_args(argv)


def get_last_seen_id(state_path: Path) -> int:
    data = rc.read_json(state_path, default={"last_seen_id": 0, "last_run": None})
    try:
        return int(data.get("last_seen_id", 0) or 0)
    except (TypeError, ValueError):
        return 0


def fetch_new_orders(env: rc.Env, since_id: int, logger) -> List[Dict[str, Any]]:
    """Return list of order dicts in processing/on-hold with id > since_id,
    ordered by ID ascending.  Uses wp-cli wc order list."""
    args = [
        "wc", "order", "list",
        "--status=" + ",".join(rc.WATCH_STATUSES),
        "--orderby=id",
        "--order=asc",
        "--limit=200",
    ]
    if since_id > 0:
        args.append("--offset=0")
    try:
        orders = rc.wp_json(env, args)
    except rc.WPCliError as e:
        logger.error("wp wc order list failed: %s", rc.redact(str(e), env))
        return []
    out: List[Dict[str, Any]] = []
    for o in orders:
        try:
            oid = int(o.get("id") or o.get("order_id") or 0)
        except (TypeError, ValueError):
            continue
        if oid <= since_id:
            continue
        out.append(o)
    return out


def fetch_line_items(env: rc.Env, order_id: int, logger) -> List[Dict[str, Any]]:
    """Fetch line items for a single order.  Returns [] on failure."""
    try:
        items = rc.wp_json(env, ["wc", "order", "items", str(order_id)])
        if isinstance(items, list):
            return items
        return []
    except rc.WPCliError as e:
        logger.warning("Failed to fetch items for order %s: %s", order_id, rc.redact(str(e), env))
        return []


def format_order_sms(order: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    """Compose the Persian SMS body for the owner."""
    oid = order.get("id", "?")
    total = str(order.get("total", "0"))
    currency = str(order.get("currency", "IRT"))
    status = str(order.get("status", "?"))

    # Billing/shipping city — wc order list JSON sometimes nests these.
    city = ""
    for key in ("shipping_city", "billing_city"):
        v = order.get(key)
        if v:
            city = str(v)
            break
    if not city:
        # Fall back to nested
        ship = order.get("shipping") or {}
        bill = order.get("billing") or {}
        city = str(ship.get("city") or bill.get("city") or "—")

    # Build item summary (max 3 lines to keep SMS short)
    lines: List[str] = []
    for it in items[:3]:
        name = str(it.get("name", "محصول"))[:40]
        qty = it.get("quantity", 1)
        lines.append(f"• {rc.to_fa_digits(qty)}× {name}")
    if len(items) > 3:
        lines.append(f"• و {rc.to_fa_digits(len(items) - 3)} قلم دیگر")
    if not lines:
        lines.append("• (فاقد جزئیات اقلام)")

    # Format total — total is a string like "2490000"
    try:
        total_int = int(float(str(total).replace(",", "")))
        total_fmt = rc.toman_str(total_int)
    except (TypeError, ValueError):
        total_fmt = rc.to_fa_digits(total)

    status_fa = {
        "processing": "در حال پردازش",
        "on-hold": "در انتظار بررسی",
    }.get(status, status)

    # Keep SMS compact (Kavenegar supports long SMS but short = cheaper + more reliable)
    body = (
        f"📦 سفارش جدید #{rc.to_fa_digits(oid)}\n"
        f"وضعیت: {status_fa}\n"
        f"شهر: {city}\n"
        f"{chr(10).join(lines)}\n"
        f"مبلغ: {total_fmt} تومان"
    )
    if currency and currency.upper() != "IRT":
        body += f" ({currency})"
    return body


def run(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    env = rc.Env(env_path=args.env_file)
    if args.dry_run:
        env.DRY_RUN = True

    logger = rc.get_logger(env, AGENT_NAME)
    try:
        env.require_staging()
    except RuntimeError as e:
        logger.error("STAGING GUARD FAILED: %s", rc.redact(str(e), env))
        return 2

    # Required directories
    state_dir = Path(env.RADMAN_PRIVATE_DIR) / "state"
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_path = state_dir / STATE_FILENAME

    lock = rc.FileLock(state_dir / f"{AGENT_NAME}.lock")
    try:
        lock.__enter__()
    except RuntimeError as e:
        logger.warning("Lock busy; exiting: %s", e)
        return 0

    try:
        since_id = 0 if args.force_rescan else get_last_seen_id(state_path)
        logger.info("Starting run: last_seen_id=%s, dry_run=%s", since_id, env.DRY_RUN)

        orders = fetch_new_orders(env, since_id, logger)
        logger.info("Found %d new order(s) since ID %s", len(orders), since_id)

        max_id = since_id
        processed = 0
        for order in orders:
            oid = int(order.get("id") or 0)
            if oid <= 0:
                continue
            items = fetch_line_items(env, oid, logger)
            text = format_order_sms(order, items)
            # Send or outbox
            res = rc.send_sms(env, to_override=None, text=text, logger=logger)
            processed += 1
            if oid > max_id:
                max_id = oid
            logger.info(
                "Order %s processed (items=%d, sent=%s, outbox=%s)",
                oid, len(items), res.get("sent"), res.get("outbox"),
            )

        # Update state (even on DRY_RUN we advance the cursor so a re-run
        # doesn't keep re-notifying about the same orders; if the user wants
        # to rescan, they pass --force-rescan).
        if max_id > since_id:
            rc.write_json_atomic(state_path, {
                "last_seen_id": max_id,
                "last_run": dt.datetime.now().isoformat(timespec="seconds"),
                "last_run_processed": processed,
            })
        else:
            # still touch last_run timestamp
            cur = rc.read_json(state_path, default={"last_seen_id": since_id})
            cur["last_run"] = dt.datetime.now().isoformat(timespec="seconds")
            cur["last_run_processed"] = processed
            rc.write_json_atomic(state_path, cur)

        logger.info("Done. processed=%d, new_last_seen_id=%s", processed, max_id)
        return 0
    finally:
        lock.__exit__(None, None, None)


if __name__ == "__main__":
    sys.exit(run())
