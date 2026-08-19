"""
RADMAN SILVER 925 — Shared on-host agent library
------------------------------------------------
stdlib-first helpers used by agent_order_watch.py, agent_price_engine.py,
and agent_stock_guard.py.

  * Env loader:  parse /home/radmansi/.config/radman/staging.env (KEY=VALUE shell
                 format, chmod 600). Never logs secret values.
  * WP-CLI wrapper: subprocess helper that forces --path=$WP_PATH.
  * Logger: rotating file logger (1 MB) writing to RADMAN_PRIVATE_DIR/logs/<agent>.log
            plus stderr. Never echoes secrets.
  * Lock helper: portable file lock via fcntl (Linux jailshell-compatible).

Hard rules enforced:
  - STAGING ONLY: APP_ENV==staging, WP_URL==https://staging.radmansilver.ir,
    WP_PATH != public_html.
  - DRY_RUN=1 default for ALL agents.
  - Kavenegar SMS sending requires DRY_RUN=0 AND KAVENEGAR_API_KEY set; otherwise
    notifications are written to outbox/*.txt.
  - Telegram is NOT used (blocked from Iran host).
  - No hardcoded secrets, mobile numbers, or tokens.
"""

from __future__ import annotations

import os
import sys
import fcntl
import hmac
import json
import time
import errno
import shlex
import logging
import datetime as dt
import subprocess
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Sequence

# ---------------------------------------------------------------------------
# Constants (do NOT read from code; all secrets via env)
# ---------------------------------------------------------------------------
EXPECTED_APP_ENV = "staging"
EXPECTED_WP_URL = "https://staging.radmansilver.ir"
EXPECTED_WP_PATH = "/home/radmansi/staging.radmansilver.ir"

SECRET_KEYS = {
    "KAVENEGAR_API_KEY",
    "OWNER_MOBILE",
    "DB_PASSWORD",
    "WP_ADMIN_PASSWORD",
    "LEGACY_API_KEY",
    "LEGACY_API_SECRET",
    "GATELAND_API_KEY",
}

# WooCommerce order statuses we watch for "new orders since last run"
WATCH_STATUSES = ("processing", "on-hold")

# Canonical WooCommerce meta keys from docs/PRODUCT-DATA-MODEL.md. Historical
# aliases remain readable so the old legacy-sync payload (`_pricing_mode`) and
# the first PR-19 implementation (`radman_pricing_mode`) do not become silent
# skips during migration.
META_PRICING_MODE = "pricing_mode"
META_PRICING_MODE_KEYS = (META_PRICING_MODE, "radman_pricing_mode", "_pricing_mode")
META_WEIGHT_G = "silver_weight_grams"           # grams (decimal)
META_WEIGHT_G_KEYS = (META_WEIGHT_G, "weight_grams", "_silver_weight_grams", "_silver_weight_g")
META_STONE_VALUE = "stone_fixed_value_toman"    # integer Toman
META_STONE_VALUE_KEYS = (META_STONE_VALUE, "_stone_fixed_value_toman")
META_LEGACY_PRICE = "legacy_price_toman"        # integer Toman
META_LEGACY_PRICE_KEYS = (META_LEGACY_PRICE, "_legacy_price_toman")
META_MANUAL_PRICE = "manual_price_toman"        # integer Toman
META_MANUAL_PRICE_KEYS = (META_MANUAL_PRICE, "_manual_price_toman")
MODE_WEIGHT_ONLY = "silver_weight_only"
MODE_WEIGHT_PLUS_STONE = "silver_weight_plus_stone"
MODE_LEGACY_MIRROR = "legacy_mirror"
MODE_MANUAL_LOCKED = "manual_locked"

# Rounding: nearest 10,000 Toman per mission spec
PRICE_ROUND_STEP = 10_000


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------
def load_env(env_path: Optional[str] = None) -> Dict[str, str]:
    """Parse a KEY=VALUE shell-style env file.  Lines starting with '#' are
    comments; blank lines are ignored; quoted values are unquoted.  Already-set
    environment variables take precedence so the file acts as defaults.

    The function NEVER prints the value of any key listed in SECRET_KEYS.
    """
    if env_path is None:
        env_path = os.environ.get(
            "RADMAN_ENV_FILE",
            str(Path.home() / ".config" / "radman" / "staging.env"),
        )
    env: Dict[str, str] = dict(os.environ)
    p = Path(env_path)
    if not p.is_file():
        return env
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return env
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if (len(v) >= 2) and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
            v = v[1:-1]
        # shell-style exports
        if k.startswith("export "):
            k = k[len("export "):].strip()
        if not k:
            continue
        # do NOT override already-set env
        env.setdefault(k, v)
    return env


class Env:
    """Helper object wrapping the loaded env with typed accessors."""

    def __init__(self, env_path: Optional[str] = None) -> None:
        self._e = load_env(env_path)
        # Normalise DRY_RUN
        dr = self._e.get("DRY_RUN", "1").strip()
        self.DRY_RUN = not (dr == "0" or dr.lower() == "false")
        self.APP_ENV = self._e.get("APP_ENV", "staging")
        self.WP_URL = self._e.get("WP_URL", EXPECTED_WP_URL)
        self.WP_PATH = self._e.get("WP_PATH", EXPECTED_WP_PATH)
        self.RADMAN_REPO_ROOT = self._e.get(
            "RADMAN_REPO_ROOT",
            str(Path.home() / "radman-deploy" / "repo"),
        )
        self.RADMAN_PRIVATE_DIR = self._e.get(
            "RADMAN_PRIVATE_DIR",
            str(Path.home() / ".config" / "radman"),
        )
        self.KAVENEGAR_API_KEY = self._e.get("KAVENEGAR_API_KEY", "").strip()
        self.OWNER_MOBILE = self._e.get("OWNER_MOBILE", "").strip()
        self.KAVENEGAR_SENDER = self._e.get("KAVENEGAR_SENDER", "").strip() or "10008445"

    @property
    def can_send_sms(self) -> bool:
        return (not self.DRY_RUN) and bool(self.KAVENEGAR_API_KEY) and bool(self.OWNER_MOBILE)

    def require_staging(self) -> None:
        """Hard staging-only guard.  Raises RuntimeError if env looks like prod."""
        if self.APP_ENV != EXPECTED_APP_ENV:
            raise RuntimeError(
                f"APP_ENV={self.APP_ENV!r} (expected {EXPECTED_APP_ENV!r}); "
                "refusing to run agents against non-staging."
            )
        if self.WP_URL != EXPECTED_WP_URL:
            raise RuntimeError(
                f"WP_URL={self.WP_URL!r} (expected {EXPECTED_WP_URL!r}); "
                "refusing to run agents against non-staging."
            )
        if self.WP_PATH != EXPECTED_WP_PATH:
            raise RuntimeError(
                f"WP_PATH={self.WP_PATH!r} (expected {EXPECTED_WP_PATH!r}); "
                "refusing an unknown WordPress path."
            )
        if "public_html" in self.WP_PATH:
            raise RuntimeError(
                f"WP_PATH={self.WP_PATH!r} contains 'public_html' — production path PROHIBITED."
            )
        private_dir = os.path.abspath(self.RADMAN_PRIVATE_DIR)
        wp_path = os.path.abspath(self.WP_PATH)
        if "public_html" in private_dir or private_dir == wp_path or private_dir.startswith(wp_path + os.sep):
            raise RuntimeError(
                "RADMAN_PRIVATE_DIR must be outside WP_PATH/public_html."
            )


# ---------------------------------------------------------------------------
# WP-CLI subprocess wrapper
# ---------------------------------------------------------------------------
class WPCliError(RuntimeError):
    pass


def wp_cli(env: Env, args: List[str], timeout: int = 120, check: bool = True) -> str:
    """Run wp-cli with --path=$WP_PATH forced.  Returns stripped stdout.

    All output is treated as potentially sensitive (may contain customer
    PII); callers decide what to log.
    """
    cmd = ["wp", "--path=" + env.WP_PATH, "--no-color"] + list(args)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as e:
        raise WPCliError("wp-cli executable was not found in PATH") from e
    except subprocess.TimeoutExpired as e:
        raise WPCliError(
            f"wp {' '.join(shlex.quote(a) for a in args)} timed out after {timeout}s"
        ) from e
    except OSError as e:
        raise WPCliError("wp-cli could not be executed") from e
    if check and proc.returncode != 0:
        # Do NOT include stdout/stderr which may leak PII; caller can inspect.
        raise WPCliError(
            f"wp {' '.join(shlex.quote(a) for a in args)} exited {proc.returncode}"
        )
    return proc.stdout.strip()


def wp_json(env: Env, args: List[str], timeout: int = 120) -> Any:
    """Run wp-cli with --format=json and parse. Returns [] for empty output."""
    out = wp_cli(env, args + ["--format=json"], timeout=timeout)
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise WPCliError(f"wp returned non-JSON output: {e}") from e


def wp_eval_json(env: Env, php_code: str, timeout: int = 120) -> Any:
    """Execute PHP through `wp eval` and decode its JSON stdout.

    This is still a wp-cli subprocess (never REST) and is used as the reliable
    WooCommerce bridge on cPanel, where optional `wp wc` command namespaces and
    shell captures vary by installed versions.
    """
    out = wp_cli(env, ["eval", php_code], timeout=timeout)
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise WPCliError(f"wp eval returned non-JSON output: {e}") from e


# ---------------------------------------------------------------------------
# Product-meta helpers
# ---------------------------------------------------------------------------
def meta_get(meta: Dict[str, Any], keys: Sequence[str], default: Any = "") -> Any:
    """Return the first present, non-empty value among canonical/legacy keys."""
    for key in keys:
        if key in meta and meta[key] not in (None, ""):
            return meta[key]
    return default


# ---------------------------------------------------------------------------
# Logging (rotating, 1 MB, 5 backups)
# ---------------------------------------------------------------------------
def get_logger(env: Env, name: str) -> logging.Logger:
    logger = logging.getLogger(f"radman.{name}")
    if getattr(logger, "_radman_configured", False):
        return logger
    logger.setLevel(logging.INFO)
    logs_dir = Path(env.RADMAN_PRIVATE_DIR) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(logs_dir, 0o700)
    log_path = logs_dir / f"{name}.log"
    log_path.touch(mode=0o600, exist_ok=True)
    os.chmod(log_path, 0o600)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = RotatingFileHandler(
        log_path,
        maxBytes=1_048_576,  # 1 MB
        backupCount=5,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    logger._radman_configured = True  # type: ignore[attr-defined]
    return logger


# ---------------------------------------------------------------------------
# Safe redaction for logs
# ---------------------------------------------------------------------------
def redact(text: str, env: Env) -> str:
    """Redact any known secret values that might appear in exception messages."""
    out = text
    for k in SECRET_KEYS:
        v = env._e.get(k, "")
        if v and len(v) >= 6:
            out = out.replace(v, "*" * 8)
    return out


# ---------------------------------------------------------------------------
# Portable file lock (fcntl on Linux, jailshell-safe)
# ---------------------------------------------------------------------------
class FileLock:
    """Context-manager exclusive file lock."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._fd: Optional[int] = None

    def __enter__(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._fd = os.open(str(self.path), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            os.close(self._fd)
            self._fd = None
            if e.errno in (errno.EAGAIN, errno.EACCES):
                raise RuntimeError(
                    f"Another instance holds the lock: {self.path}"
                ) from e
            raise
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None


# ---------------------------------------------------------------------------
# JSON state read/write
# ---------------------------------------------------------------------------
def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
                  encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Persian digit helpers (not used for SMS since Toman numerals stay Persian)
# ---------------------------------------------------------------------------
_EN_FA_DIGIT = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_fa_digits(s: Any) -> str:
    return str(s).translate(_EN_FA_DIGIT)


def toman_str(amount: int) -> str:
    """Format an integer Toman amount with thousands separator + Persian digits."""
    if amount < 0:
        return "-" + toman_str(-amount)
    return to_fa_digits(f"{amount:,}")


# ---------------------------------------------------------------------------
# Rounding
# ---------------------------------------------------------------------------
def round_to_step(price: Any, step: int = PRICE_ROUND_STEP) -> int:
    """Round to nearest *step* Toman using commercial half-up semantics."""
    try:
        amount = Decimal(str(price))
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"invalid price: {price!r}") from e
    if step <= 0:
        return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if amount <= 0:
        return 0
    units = (amount / Decimal(step)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    rounded = int(units * Decimal(step))
    return max(rounded, step)


# ---------------------------------------------------------------------------
# Kavenegar SMS (DRY_RUN aware)
# ---------------------------------------------------------------------------
def send_sms(
    env: Env,
    to_override: Optional[str],
    text: str,
    logger: logging.Logger,
    outbox_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Send SMS via Kavenegar REST, or atomically persist an outbox file.

    `outbox_name` lets order-watch meet the stable `order_<ID>.txt` contract.
    Unsafe/path-containing names are rejected and replaced with a timestamp.
    """
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    outbox = Path(env.RADMAN_PRIVATE_DIR) / "outbox"
    outbox.mkdir(parents=True, exist_ok=True, mode=0o700)

    safe_name = ""
    if outbox_name:
        candidate = Path(outbox_name).name
        if candidate == outbox_name and candidate.endswith(".txt"):
            safe_name = candidate
    base_path = outbox / (safe_name or f"sms-{ts}.txt")

    if not env.can_send_sms:
        # Always write an outbox copy so the owner can see what WOULD have sent.
        write_text_atomic(base_path, text)
        logger.info("DRY_RUN=1 (or missing key/mobile); notification written to %s", base_path)
        return {"dry_run": True, "outbox": str(base_path), "sent": False}

    to = (to_override or env.OWNER_MOBILE or "").strip()
    if not to:
        write_text_atomic(base_path, text)
        logger.warning("No recipient mobile; notification saved to %s", base_path)
        return {"dry_run": True, "outbox": str(base_path), "sent": False}

    api_key = env.KAVENEGAR_API_KEY
    sender = env.KAVENEGAR_SENDER or "10008445"
    url = (
        f"https://api.kavenegar.com/v1/{urllib.parse.quote(api_key, safe='')}/sms/send.json"
    )
    post_data = urllib.parse.urlencode({
        "receptor": to,
        "sender": sender,
        "message": text,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=post_data, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        logger.info("SMS sent to %s via Kavenegar (len=%d)", to[:4] + "***", len(text))
        # Save a sent copy too (never overwrite the pending dry-run filename).
        if safe_name:
            path = outbox / f"{Path(safe_name).stem}.sent.txt"
        else:
            path = outbox / f"sms-sent-{ts}.txt"
        write_text_atomic(path, text)
        return {"dry_run": False, "outbox": str(path), "sent": True, "response": body[:200]}
    except Exception as e:  # network/auth failure
        # Keep the stable order_<ID>.txt pending file on failure so the alert is
        # visible to the owner and a later --force-rescan can retry it.
        path = base_path if safe_name else outbox / f"sms-failed-{ts}.txt"
        write_text_atomic(path, text)
        logger.error("Kavenegar send failed: %s (saved to %s)", redact(str(e), env), path)
        return {"dry_run": False, "outbox": str(path), "sent": False, "error": redact(str(e), env)}


# ---------------------------------------------------------------------------
# Constant-compare / timing-safe helpers for future webhooks
# ---------------------------------------------------------------------------
def const_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
