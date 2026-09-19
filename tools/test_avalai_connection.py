#!/usr/bin/env python3
"""
AvalAI Connection & Capability Test Suite
=========================================
Independent, zero-dependency diagnostic tool for validating AvalAI
(OpenAI-compatible) endpoint connectivity, Persian text handling,
JSON structured output mode, and Tool Calling capabilities.

Usage:
  python tools/test_avalai_connection.py [--env-file ./ai.env] [--out-file connection-report.json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def mask_api_key(key: str) -> str:
    """Safely masks API key displaying only the last 4 characters."""
    if not key:
        return "NONE"
    clean = key.strip()
    if len(clean) <= 4:
        return "****"
    return "*" * (len(clean) - 4) + clean[-4:]


def load_env_file(env_path: Path) -> Dict[str, str]:
    """Parses a key-value env file without external libraries."""
    env_vars: Dict[str, str] = {}
    if not env_path.exists():
        return env_vars

    # Check file permissions on POSIX
    try:
        mode = os.stat(env_path).st_mode & 0o777
        if mode & 0o077:
            print(f"[هشدار امنیتی] دسترسی فایل {env_path} باز است ({oct(mode)}). پیشنهاد: chmod 600 {env_path}")
    except Exception:
        pass

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                env_vars[k] = v
    return env_vars


class AvalAIClient:
    """Lightweight HTTP client for AvalAI OpenAI-compatible endpoints."""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 30, max_retries: int = 2) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def _send_request(self, endpoint_path: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any], float]:
        """Sends HTTP POST request with retry backoff and latency measurement."""
        url = f"{self.base_url}/{endpoint_path.lstrip('/')}"
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "RADMAN-AvalAI-Tester/1.0",
        }

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 2):
            start_time = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    latency = time.perf_counter() - start_time
                    status_code = response.getcode()
                    res_body = response.read().decode("utf-8")
                    return status_code, json.loads(res_body), latency
            except urllib.error.HTTPError as e:
                latency = time.perf_counter() - start_time
                error_body = e.read().decode("utf-8", errors="ignore")
                try:
                    err_json = json.loads(error_body)
                except Exception:
                    err_json = {"error": error_body, "status": e.code}

                # If 429 or 5xx, retry with backoff
                if e.code in (429, 500, 502, 503, 504) and attempt <= self.max_retries:
                    time.sleep(1.5 * attempt)
                    continue
                return e.code, err_json, latency
            except urllib.error.URLError as e:
                latency = time.perf_counter() - start_time
                last_err = e
                if attempt <= self.max_retries:
                    time.sleep(1.5 * attempt)
                    continue
                return 0, {"error": str(e.reason)}, latency
            except Exception as e:
                latency = time.perf_counter() - start_time
                return 0, {"error": str(e)}, latency

        return 0, {"error": str(last_err)}, 0.0

    def test_text_chat(self) -> Dict[str, Any]:
        """T1_TEXT via Chat Completions."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "تو یک دستیار متخصص نقره و گوهرشناسی هستی. پاسخ کوتاه فارسی بده."},
                {"role": "user", "content": "عیار استاندارد نقره استرلینگ چیست؟ فقط در یک جمله کوتاه بگو."},
            ],
            "max_tokens": 100,
            "temperature": 0.2,
        }
        status_code, data, latency = self._send_request("chat/completions", payload)

        if status_code == 200:
            choices = data.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""
            # Check Persian encoding health
            is_healthy_persian = bool(re.search(r"[\u0600-\u06FF]", content)) and "۹۲۵" in content or "925" in content or "نقره" in content
            return {
                "status": "PASS" if is_healthy_persian else "WARN",
                "status_code": status_code,
                "latency_sec": round(latency, 3),
                "tokens": data.get("usage", {}),
                "response_sample": content.strip()[:120],
            }
        return {
            "status": "FAIL",
            "status_code": status_code,
            "latency_sec": round(latency, 3),
            "error": data.get("error"),
        }

    def test_json_mode(self) -> Dict[str, Any]:
        """T2_JSON via Chat Completions with JSON Object Mode."""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a jewelry database assistant. Return JSON only with keys: ring_name, silver_hallmark (integer), gemstone.",
                },
                {"role": "user", "content": "Generate spec for a Men's Carnelian Silver Ring."},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 150,
            "temperature": 0.1,
        }
        status_code, data, latency = self._send_request("chat/completions", payload)

        if status_code == 200:
            choices = data.get("choices", [])
            raw_text = choices[0].get("message", {}).get("content", "") if choices else ""
            try:
                parsed = json.loads(raw_text)
                has_keys = "ring_name" in parsed and "silver_hallmark" in parsed
                return {
                    "status": "PASS" if has_keys else "FAIL",
                    "status_code": status_code,
                    "latency_sec": round(latency, 3),
                    "tokens": data.get("usage", {}),
                    "parsed_json": parsed,
                }
            except json.JSONDecodeError as err:
                return {
                    "status": "FAIL",
                    "status_code": status_code,
                    "latency_sec": round(latency, 3),
                    "error": f"JSON decode failed: {err}",
                    "raw": raw_text,
                }
        return {
            "status": "FAIL",
            "status_code": status_code,
            "latency_sec": round(latency, 3),
            "error": data.get("error"),
        }

    def test_tool_calling(self) -> Dict[str, Any]:
        """T3_TOOLS via Chat Completions Tool Calling."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_product_stock",
                    "description": "Checks the verified 1:1 stock quantity of a luxury silver ring by product_id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "The WooCommerce product ID"}
                        },
                        "required": ["product_id"],
                    },
                },
            }
        ]

        messages = [
            {"role": "system", "content": "تو دستیار فروش رادمان سیلور هستی. در صورت نیاز به موجودی از ابزار استفاده کن."},
            {"role": "user", "content": "موجودی انگشتر با شناسه ۲۳۲ چقدر است؟"},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "max_tokens": 200,
            "temperature": 0.0,
        }
        status_code, data, latency1 = self._send_request("chat/completions", payload)

        if status_code != 200:
            return {
                "status": "FAIL",
                "status_code": status_code,
                "latency_sec": round(latency1, 3),
                "error": data.get("error"),
            }

        choices = data.get("choices", [])
        msg = choices[0].get("message", {}) if choices else {}
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            return {
                "status": "FAIL",
                "status_code": status_code,
                "latency_sec": round(latency1, 3),
                "error": "Model did not trigger tool_call for get_product_stock",
                "response": msg.get("content"),
            }

        call = tool_calls[0]
        fn_name = call.get("function", {}).get("name")
        fn_args_raw = call.get("function", {}).get("arguments", "{}")

        try:
            fn_args = json.loads(fn_args_raw)
        except json.JSONDecodeError:
            fn_args = {}

        # Simulate local tool execution
        tool_result = {"product_id": fn_args.get("product_id", 232), "stock_quantity": 1, "status": "instock"}

        # Step 2: Feed tool output back to model
        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": call.get("id", "call_mock_123"),
            "content": json.dumps(tool_result, ensure_ascii=False),
        })

        payload2 = {"model": self.model, "messages": messages, "max_tokens": 150}
        status_code2, data2, latency2 = self._send_request("chat/completions", payload2)

        total_latency = latency1 + latency2
        final_content = data2.get("choices", [{}])[0].get("message", {}).get("content", "") if status_code2 == 200 else ""

        is_success = fn_name == "get_product_stock" and fn_args.get("product_id") == 232 and status_code2 == 200
        return {
            "status": "PASS" if is_success else "FAIL",
            "status_code": status_code2,
            "total_latency_sec": round(total_latency, 3),
            "tool_triggered": fn_name,
            "tool_arguments": fn_args,
            "final_answer": final_content.strip()[:120],
        }

    def test_responses_api(self) -> Dict[str, Any]:
        """Tests optional /v1/responses endpoint; reports UNSUPPORTED gracefully if 404/501."""
        payload = {
            "model": self.model,
            "input": "سلام",
        }
        status_code, data, latency = self._send_request("responses", payload)
        if status_code == 200:
            return {"status": "PASS", "status_code": status_code, "latency_sec": round(latency, 3)}
        elif status_code in (404, 405, 501):
            return {
                "status": "UNSUPPORTED",
                "status_code": status_code,
                "message": "Responses API endpoint is not implemented on this proxy; Chat Completions is the active protocol.",
            }
        return {
            "status": "FAIL",
            "status_code": status_code,
            "latency_sec": round(latency, 3),
            "error": data.get("error"),
        }


def run_diagnostics(env_file_path: Optional[str] = None, out_file_path: Optional[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Test AvalAI endpoint connectivity and capabilities")
    parser.add_argument("--env-file", default="./ai.env", help="Path to env file with AvalAI credentials")
    parser.add_argument("--out-file", default="connection-report.json", help="Path to save diagnostic JSON report")
    args = parser.parse_args()

    env_path = Path(env_file_path or args.env_file)
    out_path = Path(out_file_path or args.out_file)

    env_vars = load_env_file(env_path) if env_path.exists() else {}

    api_key = os.environ.get("AVALAI_API_KEY") or env_vars.get("AVALAI_API_KEY")
    base_url = os.environ.get("AVALAI_BASE_URL") or env_vars.get("AVALAI_BASE_URL", "https://api.avalai.ir/v1")
    model = os.environ.get("AVALAI_MODEL") or env_vars.get("AVALAI_MODEL", "gpt-4o-mini")

    print("=" * 75)
    print("  RADMAN SILVER 925 — AVALAI ENDPOINT DIAGNOSTIC SUITE")
    print("=" * 75)

    # Dry-run handling when credentials are not yet supplied
    if not api_key or "your_avalai" in api_key.lower():
        print("\n[راهنمای تنظیم اولیه — MISSING_ENV]")
        print("  ❌ کلید معتبر AVALAI_API_KEY در فایل تنظیمات یافت نشد.")
        print("  راهنمای مالک برای فعال‌سازی:")
        print("    ۱. ایجاد فایل ai.env از روی نمونه:  cp tools/ai.env.example ai.env")
        print("    ۲. درج کلید دریافت شده از AvalAI در متغیر AVALAI_API_KEY")
        print("    ۳. اجرای مجدد دستور:")
        print("       python tools/test_avalai_connection.py --env-file ./ai.env")
        print("\n" + "=" * 75)
        print("  وضعیت: آماده‌باش برای دریافت کلید مالک (STATUS: MISSING_ENV)")
        print("=" * 75)
        return 0

    masked_key = mask_api_key(api_key)
    print(f"\n[1/4] پیکربندی اتصال:")
    print(f"  • Base URL   : {base_url}")
    print(f"  • Model      : {model}")
    print(f"  • API Key    : {masked_key} (محافظت‌شده)")

    client = AvalAIClient(api_key=api_key, base_url=base_url, model=model)

    print(f"\n[2/4] اجرای آزمون‌های سه‌گانه Chat Completions:")
    print("  ▸ آزمون T1 (متن فارسی سالم)...", end=" ", flush=True)
    t1_res = client.test_text_chat()
    print(f"[{t1_res['status']}] ({t1_res.get('latency_sec', 0)}s)")

    print("  ▸ آزمون T2 (خروجی ساختاریافته JSON)...", end=" ", flush=True)
    t2_res = client.test_json_mode()
    print(f"[{t2_res['status']}] ({t2_res.get('latency_sec', 0)}s)")

    print("  ▸ آزمون T3 (فراخوانی ابزار Tool Calling)...", end=" ", flush=True)
    t3_res = client.test_tool_calling()
    print(f"[{t3_res['status']}] ({t3_res.get('total_latency_sec', t3_res.get('latency_sec', 0))}s)")

    print(f"\n[3/4] بررسی اندپوینت Responses API:")
    print("  ▸ آزمون اندپوینت /v1/responses...", end=" ", flush=True)
    resp_api_res = client.test_responses_api()
    print(f"[{resp_api_res['status']}]")

    report_payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "base_url": base_url,
        "model": model,
        "masked_key": masked_key,
        "tests": {
            "T1_TEXT_PERSIAN": t1_res,
            "T2_JSON_MODE": t2_res,
            "T3_TOOL_CALLING": t3_res,
            "RESPONSES_API": resp_api_res,
        },
        "overall_verdict": "PASS" if (t1_res["status"] == "PASS" and t2_res["status"] == "PASS" and t3_res["status"] == "PASS") else "FAIL",
    }

    print(f"\n[4/4] ذخیره گزارش در {out_path}...")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2, ensure_ascii=False)
        print(f"  ✓ فایل لاگ تشخیصی با موفقیت ذخیره شد.")
    except Exception as e:
        print(f"  ✗ خطا در ذخیره فایل گزارش: {e}")

    print("\n" + "=" * 75)
    print(f"  نتیجه نهایی اتصال: {report_payload['overall_verdict']}")
    print("=" * 75)
    return 0 if report_payload["overall_verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(run_diagnostics())
