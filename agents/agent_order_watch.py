#!/usr/bin/env python3
"""
RADMAN SILVER 925 — Order Watch Agent (cron: every 5 minutes)
-------------------------------------------------------------
Runs on the staging (and later production) host via cron.  Polls WooCommerce
for new orders in 'processing' or 'on-hold' since the last seen ID stored in
RADMAN_PRIVATE_DIR/state/order_watch.json.  For each new order it composes a
concise Persian SMS notification to the owner (order ID, items, total in
Toman, customer city).

Default mode is DRY_RUN=1: each notification is written atomically to
outbox/order_<ID>.txt.
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


def fetch_new_orders(
    env: rc.Env,
    since_id: int,
    logger,
    initial_lookback: int = 50,
) -> List[Dict[str, Any]]:
    """Return processing/on-hold orders with ID > cursor, ascending.

    WooCommerce data is read through a `wp eval` subprocess (never REST). This
    works with both classic order storage and HPOS and avoids optional/renamed
    `wp wc order` command namespaces. The latest 200 matching orders are more
    than enough for a five-minute polling window.
    """
    php_code = r'''
if (!function_exists('wc_get_orders')) { fwrite(STDERR, "WooCommerce unavailable\n"); exit(3); }
$orders = wc_get_orders(array(
  'status' => array('processing', 'on-hold'),
  'limit' => 200,
  'orderby' => 'ID',
  'order' => 'DESC',
  'return' => 'objects',
));
$out = array();
foreach ($orders as $order) {
  $items = array();
  foreach ($order->get_items('line_item') as $item) {
    $items[] = array('name' => $item->get_name(), 'quantity' => $item->get_quantity());
  }
  $out[] = array(
    'id' => $order->get_id(),
    'status' => $order->get_status(),
    'total' => $order->get_total(),
    'currency' => $order->get_currency(),
    'shipping_city' => $order->get_shipping_city(),
    'billing_city' => $order->get_billing_city(),
    'line_items' => $items,
  );
}
echo wp_json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
'''
    try:
        orders = rc.wp_eval_json(env, php_code)
    except rc.WPCliError as e:
        logger.error("wp-cli WooCommerce order query failed: %s", rc.redact(str(e), env))
        raise
    if not isinstance(orders, list):
        return []

    out: List[Dict[str, Any]] = []
    for o in orders:
        if not isinstance(o, dict):
            continue
        try:
            oid = int(o.get("id") or o.get("order_id") or 0)
        except (TypeError, ValueError):
            continue
        if oid > since_id:
            out.append(o)
    out.sort(key=lambda row: int(row.get("id") or 0))
    if since_id <= 0 and initial_lookback > 0:
        out = out[-initial_lookback:]
    return out


def fetch_line_items(env: rc.Env, order_id: int, logger) -> List[Dict[str, Any]]:
    """Fallback line-item query through wp eval for one order."""
    if order_id <= 0:
        return []
    php_code = f'''
$order = function_exists('wc_get_order') ? wc_get_order({int(order_id)}) : false;
if (!$order) {{ echo '[]'; return; }}
$out = array();
foreach ($order->get_items('line_item') as $item) {{
  $out[] = array('name' => $item->get_name(), 'quantity' => $item->get_quantity());
}}
echo wp_json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
'''
    try:
        items = rc.wp_eval_json(env, php_code)
        return items if isinstance(items, list) else []
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

        lookback = 200 if args.force_rescan else max(1, min(args.lookback, 200))
        try:
            orders = fetch_new_orders(env, since_id, logger, initial_lookback=lookback)
        except rc.WPCliError:
            return 4
        logger.info("Found %d new order(s) since ID %s", len(orders), since_id)

        max_id = since_id
        processed = 0
        for order in orders:
            oid = int(order.get("id") or 0)
            if oid <= 0:
                continue
            embedded_items = order.get("line_items")
            items = embedded_items if isinstance(embedded_items, list) else fetch_line_items(env, oid, logger)
            text = format_order_sms(order, items)
            # Stable dry-run contract: outbox/order_<ID>.txt
            res = rc.send_sms(
                env,
                to_override=None,
                text=text,
                logger=logger,
                outbox_name=f"order_{oid}.txt",
            )
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
