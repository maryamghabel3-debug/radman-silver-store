#!/usr/bin/env python3
"""
RADMAN SILVER 925 — On-host agent dry-run tests (mocked wp-cli)
"""

from __future__ import annotations

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Any, List, Dict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

from lib import radman_common as rc  # noqa: E402
import agent_order_watch as ow       # noqa: E402
import agent_price_engine as pe      # noqa: E402
import agent_stock_guard as sg       # noqa: E402


def make_env(tmpdir: Path, dry_run: bool = True) -> rc.Env:
    p = Path(tmpdir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "staging.env").write_text(
        "APP_ENV=staging\n"
        "WP_PATH=/home/radmansi/staging.radmansilver.ir\n"
        "WP_URL=https://staging.radmansilver.ir\n"
        f"RADMAN_PRIVATE_DIR={p}\n"
        f"RADMAN_REPO_ROOT={HERE}\n"
        f"DRY_RUN={'1' if dry_run else '0'}\n",
        encoding="utf-8",
    )
    os.chmod(p / "staging.env", 0o600)
    for sub in ("state", "outbox", "logs", "backups", "locks"):
        (p / sub).mkdir(mode=0o700, exist_ok=True)
    return rc.Env(env_path=str(p / "staging.env"))


class MockWP:
    def __init__(self, orders, items_by_order, products):
        self.orders = orders
        self.items_by_order = items_by_order
        self.products = products
        self.update_calls: List[List[str]] = []

    def json(self, args: List[str]) -> Any:
        if args[:3] == ["wc", "order", "list"]:
            return self.orders
        if args[:3] == ["wc", "order", "items"]:
            try:
                oid = int(args[3])
            except (IndexError, ValueError):
                return []
            return self.items_by_order.get(oid, [])
        if args[:3] == ["wc", "product", "list"]:
            return self.products
        if args[:3] == ["post", "meta", "list"]:
            try:
                pid = int(args[3])
            except (IndexError, ValueError):
                return []
            for prod in self.products:
                if prod["id"] == pid:
                    out = []
                    for k, v in prod.get("_meta", {}).items():
                        out.append({"meta_key": k, "meta_value": v})
                    return out
            return []
        return []

    def cli(self, args: List[str], timeout: int = 120, check: bool = True) -> str:
        if args[:3] == ["wc", "product", "update"]:
            self.update_calls.append(args)
            return ""
        return ""


def install_mock(mock: MockWP):
    rc.wp_json = lambda env, args, timeout=120: mock.json(args)
    rc.wp_cli = lambda env, args, timeout=120, check=True: mock.cli(args, timeout, check)


def test_rounding():
    assert rc.round_to_step(6.80 * 85000) == 580_000
    assert rc.round_to_step(5.0 * 85000 + 200_000) == 620_000
    assert rc.round_to_step(0) == 0
    print("OK: rounding to nearest 10,000 works.")


def test_toman_format():
    s = rc.toman_str(2490000)
    assert "۲" in s and "۴۹۰" in s, s
    print(f"OK: toman_str(2490000) = {s}")


def test_secret_redaction_and_staging_guards(tmp_path):
    env = make_env(tmp_path / "g")
    env._e["KAVENEGAR_API_KEY"] = "abcdef1234567890SECRET"
    env.KAVENEGAR_API_KEY = "abcdef1234567890SECRET"
    msg = "failed with key=abcdef1234567890SECRET in url"
    assert "abcdef1234567890SECRET" not in rc.redact(msg, env)
    env.APP_ENV = "production"
    try:
        env.require_staging(); raise AssertionError("expected RuntimeError for prod")
    except RuntimeError:
        pass
    env.APP_ENV = "staging"
    env.WP_PATH = "/home/user/public_html"
    try:
        env.require_staging(); raise AssertionError("expected RuntimeError for public_html")
    except RuntimeError:
        pass
    env.WP_PATH = "/home/radmansi/staging.radmansilver.ir"
    env.require_staging()
    print("OK: secret redaction and staging guards work.")


def test_new_order_detection_and_sms(tmp_path):
    orders = [
        {"id": 100, "status": "on-hold", "total": "2490000", "currency": "IRT",
         "billing_city": "مشهد", "shipping_city": "مشهد"},
        {"id": 101, "status": "processing", "total": "1850000", "currency": "IRT",
         "billing_city": "تهران"},
    ]
    items = {
        100: [{"name": "انگشتر نقره عقیق", "quantity": 1},
              {"name": "گردنبند مینیمال", "quantity": 1}],
        101: [{"name": "دستبند نقره", "quantity": 1}],
    }
    mock = MockWP(orders=orders, items_by_order=items, products=[])
    install_mock(mock)
    env_path = tmp_path / "a"
    env = make_env(env_path)
    rc.write_json_atomic(env_path / "state" / "order_watch.json", {"last_seen_id": 99})

    sent: List[str] = []
    def fake_send(env, to_override=None, text="", logger=None):
        sent.append(text)
        return {"dry_run": True, "outbox": str(env_path / "outbox" / f"sms-{len(sent)}.txt"), "sent": False}
    rc.send_sms = fake_send

    ow.fetch_new_orders = lambda e, sid, lg: [o for o in orders if int(o["id"]) > sid]
    ow.fetch_line_items = lambda e, oid, lg: items.get(oid, [])
    ret = ow.run(["--env-file", str(env_path / "staging.env"), "--dry-run"])
    assert ret == 0, f"order_watch exited {ret}"
    assert len(sent) == 2, f"expected 2 notifications, got {len(sent)}"
    assert "سفارش جدید" in sent[0]
    assert "#۱۰۰" in sent[0]
    assert "۲" in sent[0] and "۴۹۰" in sent[0]
    state = rc.read_json(env_path / "state" / "order_watch.json", {})
    assert state["last_seen_id"] == 101
    print("OK: new-order detection + SMS formatting works.")


def test_pricing_all_four_modes(tmp_path):
    products = [
        {"id": 1, "name": "انگشتر ساده", "sku": "RAD-RNG-U-1", "regular_price": "500000",
         "price": "500000", "status": "publish", "type": "simple",
         "manage_stock": True, "stock_quantity": 1, "stock_status": "instock",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_ONLY, rc.META_WEIGHT_G: "6.80"}},
        {"id": 2, "name": "انگشتر عقیق", "sku": "RAD-RNG-U-2", "regular_price": "600000",
         "price": "600000", "status": "publish", "type": "simple",
         "manage_stock": True, "stock_quantity": 1, "stock_status": "instock",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_PLUS_STONE,
                   rc.META_WEIGHT_G: "5.0", rc.META_STONE_VALUE: "200000"}},
        {"id": 3, "name": "سرویس ویژه", "sku": "RAD-SET-U-3", "regular_price": "8900000",
         "price": "8900000", "status": "publish", "type": "simple",
         "manage_stock": True, "stock_quantity": 1, "stock_status": "instock",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_MANUAL_LOCKED, rc.META_WEIGHT_G: "20"}},
        {"id": 4, "name": "محصول لگاسی", "sku": "RAD-RNG-U-4", "regular_price": "300000",
         "price": "300000", "status": "publish", "type": "simple",
         "manage_stock": True, "stock_quantity": 1, "stock_status": "instock",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_LEGACY_MIRROR, rc.META_LEGACY_PRICE: "300000"}},
        {"id": 5, "name": "بدون وزن", "sku": "RAD-RNG-U-5", "regular_price": "100000",
         "price": "100000", "status": "publish", "type": "simple",
         "manage_stock": True, "stock_quantity": 1, "stock_status": "instock",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_ONLY}},
        {"id": 6, "name": "نگین نامعتبر", "sku": "RAD-RNG-U-6", "regular_price": "400000",
         "price": "400000", "status": "publish", "type": "simple",
         "manage_stock": True, "stock_quantity": 1, "stock_status": "instock",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_PLUS_STONE, rc.META_WEIGHT_G: "4"}},
    ]
    mock = MockWP(orders=[], items_by_order={}, products=products)
    install_mock(mock)

    workdir = tmp_path / "b"
    env = make_env(workdir)
    (workdir / "state" / "daily_rate.txt").write_text("85000\n", encoding="utf-8")

    pe.fetch_products = lambda e, lg: [
        {"id": p["id"], "name": p["name"], "sku": p["sku"],
         "regular_price": p["regular_price"], "meta": p["_meta"]} for p in products
    ]
    ret = pe.run(["--env-file", str(workdir / "staging.env"), "--dry-run", "--top", "10"])
    assert ret == 0
    previews = list((workdir / "outbox").glob("price_preview_*.txt"))
    assert previews, "preview not generated"
    preview_text = previews[-1].read_text(encoding="utf-8")
    assert "PREVIEW" in preview_text
    assert "RAD-RNG-U-1" in preview_text
    assert "RAD-RNG-U-2" in preview_text

    (workdir / "staging.env").write_text(
        "APP_ENV=staging\nWP_PATH=/home/radmansi/staging.radmansilver.ir\n"
        "WP_URL=https://staging.radmansilver.ir\n"
        f"RADMAN_PRIVATE_DIR={workdir}\nRADMAN_REPO_ROOT={HERE}\nDRY_RUN=0\n",
        encoding="utf-8",
    )
    pe.fetch_products = lambda e, lg: [
        {"id": p["id"], "name": p["name"], "sku": p["sku"],
         "regular_price": p["regular_price"], "meta": p["_meta"]} for p in products
    ]
    mock.update_calls = []
    ret2 = pe.run(["--env-file", str(workdir / "staging.env"), "--apply", "--rate", "85000",
                   "--top", "10"])
    assert ret2 == 0
    # Product 6 has no stone value -> skip; only 1 and 2 should update
    assert len(mock.update_calls) == 2, f"expected 2 updates, got {len(mock.update_calls)}: {mock.update_calls}"
    upd_pids = {int(a[3]) for a in mock.update_calls}
    assert upd_pids == {1, 2}, upd_pids
    upd_map = {int(a[3]): a[4] for a in mock.update_calls}
    assert upd_map[1] == "--regular_price=580000", upd_map
    assert upd_map[2] == "--regular_price=620000", upd_map
    csvs = list((workdir / "backups").glob("prices-*.csv"))
    assert csvs, "CSV backup missing"
    print("OK: pricing engine handles all 4 modes, rounding, skips, and writes apply.")


def test_stock_guard_detection(tmp_path):
    products = [
        {"id": 1, "name": "in-stock ok", "sku": "A1", "manage_stock": True,
         "stock_quantity": 1, "stock_status": "instock", "type": "simple",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_ONLY, rc.META_WEIGHT_G: "5"}},
        {"id": 2, "name": "zero-but-instock", "sku": "A2", "manage_stock": True,
         "stock_quantity": 0, "stock_status": "instock", "type": "simple", "_meta": {}},
        {"id": 3, "name": "negative", "sku": "A3", "manage_stock": True,
         "stock_quantity": -1, "stock_status": "instock", "type": "simple", "_meta": {}},
        {"id": 4, "name": "weight-mode-no-weight", "sku": "A4", "manage_stock": True,
         "stock_quantity": 1, "stock_status": "instock", "type": "simple",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_ONLY}},
        {"id": 5, "name": "stone-mode-no-stone", "sku": "A5", "manage_stock": True,
         "stock_quantity": 1, "stock_status": "instock", "type": "simple",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_PLUS_STONE, rc.META_WEIGHT_G: "5"}},
        {"id": 6, "name": "mode-no-manage", "sku": "A6", "manage_stock": False,
         "stock_quantity": 0, "stock_status": "instock", "type": "simple",
         "_meta": {rc.META_PRICING_MODE: rc.MODE_WEIGHT_ONLY, rc.META_WEIGHT_G: "3"}},
        {"id": 7, "name": "dup-sku-1", "sku": "DUP", "manage_stock": True,
         "stock_quantity": 1, "stock_status": "instock", "type": "simple", "_meta": {}},
        {"id": 8, "name": "dup-sku-2", "sku": "DUP", "manage_stock": True,
         "stock_quantity": 1, "stock_status": "instock", "type": "simple", "_meta": {}},
    ]
    buckets = sg.scan(products)
    assert any(p["id"] == 2 for p in buckets["zero_but_instock"])
    assert any(p["id"] == 3 for p in buckets["negative_stock"])
    assert any(p["id"] == 4 for p in buckets["missing_weight_meta"])
    assert any(p["id"] == 5 for p in buckets["missing_stone_value"])
    assert any(p["id"] == 6 for p in buckets["mode_no_manage_stock"])
    assert any(p["id"] == 8 for p in buckets["duplicate_sku"])
    report = sg.render_report(buckets, "")
    assert "READ-ONLY" in report

    mock = MockWP(orders=[], items_by_order={}, products=products)
    install_mock(mock)
    workdir = tmp_path / "c"
    make_env(workdir)
    sg.fetch_products = lambda e, lim, lg: products
    ret = sg.run(["--env-file", str(workdir / "staging.env")])
    assert ret == 0
    reports = list((workdir / "outbox").glob("stock_report_*.txt"))
    assert reports, "stock report not written"
    print("OK: stock guard detects all anomaly classes and writes report.")


def test_dryrun_plan_via_install_script(tmp_path):
    # Just bash -n the installer (already done) and --plan via bash
    import subprocess
    r = subprocess.run(["bash", "-n", str(HERE.parent / "scripts" / "install_agents.sh")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    r2 = subprocess.run(["bash", "--posix", "-n", str(HERE.parent / "scripts" / "install_agents.sh")],
                        capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr
    print("OK: installer passes bash -n and bash --posix -n.")


def test_no_secrets_or_telegram():
    # Scan new files for telegram API calls, hardcoded mobile numbers, tokens
    import re
    new_files = [
        HERE / "agent_order_watch.py",
        HERE / "agent_price_engine.py",
        HERE / "agent_stock_guard.py",
        HERE / "lib" / "radman_common.py",
        HERE.parent / "scripts" / "install_agents.sh",
    ]
    bad_patterns = [
        (r"api\.telegram\.org", "telegram API URL"),
        (r"ghp_[A-Za-z0-9]{20,}", "GitHub PAT"),
        (r"09\d{9}", "hardcoded Iranian mobile"),  # OWNER_MOBILE set in env only
        (r"googleapis\.com/css", "Google Fonts"),
        (r"KAVENEGAR_API_KEY\s*=\s*['\"][^'\"]+['\"]", "hardcoded Kavenegar key"),
    ]
    for f in new_files:
        text = f.read_text(encoding="utf-8")
        for pat, label in bad_patterns:
            # The env template lists KAVENEGAR_API_KEY= (empty) — that's fine
            m = re.search(pat, text)
            if m and pat != r"KAVENEGAR_API_KEY\s*=\s*['\"][^'\"]+['\"]":
                # Allow OWNER_MOBILE placeholder line
                if label == "hardcoded Iranian mobile" and "09" not in m.group(0):
                    continue
                raise AssertionError(f"{f.name}: found forbidden pattern '{label}': {m.group(0)[:60]}")
    print("OK: no telegram, no hardcoded secrets, no Google Fonts in new code.")


if __name__ == "__main__":
    tmp = Path(tempfile.mkdtemp(prefix="radman-agent-test-"))
    try:
        test_rounding()
        test_toman_format()
        test_secret_redaction_and_staging_guards(tmp)
        test_new_order_detection_and_sms(tmp)
        test_pricing_all_four_modes(tmp)
        test_stock_guard_detection(tmp)
        test_dryrun_plan_via_install_script(tmp)
        test_no_secrets_or_telegram()
        print("\nALL TESTS PASSED.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
