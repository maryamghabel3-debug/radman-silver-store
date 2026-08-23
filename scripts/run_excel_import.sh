#!/usr/bin/env bash
# PR-31 owner runner: HTML-primary spec repair for existing Draft products.
set -euo pipefail

umask 077
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
EXCEL_FILE=${EXCEL_FILE:-/home/radmansi/radman-deploy/products_20260821_182238.xlsx}
MAX_PRODUCTS=${MAX_PRODUCTS:-1000}
RADMAN_PRIVATE_DIR=${RADMAN_PRIVATE_DIR:-/home/radmansi/private}
MODE=
MANIFEST=
LOCK_DIR=

cleanup() {
  if [ -n "$LOCK_DIR" ] && [ -d "$LOCK_DIR" ]; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

usage() {
  cat <<'EOF'
Usage: bash scripts/run_excel_import.sh MODE [options]

Modes (choose exactly one):
  --inspect         Re-print Excel structure/selection summary; read-only
  --plan            Select newest eligible products and preview pricing
  --fetch-images    Select products and fetch/process original galleries
  --import-drafts   Import the latest fetched manifest as create-only Drafts
  --enrich-existing Repair existing Draft descriptions/meta from HTML product pages
  --identity-report Read-only SKU/legacy identity reconciliation report
  --full-pilot      Plan, fetch specs/images, then import guarded Drafts

Options:
  --excel PATH      Override EXCEL_FILE
  --max-products N  Override MAX_PRODUCTS (hard maximum 1000)
  --private-dir P   Override RADMAN_PRIVATE_DIR
  --manifest PATH   Explicit prepared manifest for --import-drafts
  --help

Excel controls selection/price/stock/active. HTML product pages are primary for specs; API is deferred.
EOF
}

set_mode() {
  if [ -n "$MODE" ]; then
    echo '[ERROR] choose exactly one mode' >&2
    exit 2
  fi
  MODE=$1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --inspect|--plan|--fetch-images|--import-drafts|--enrich-existing|--identity-report|--full-pilot)
      set_mode "$1"
      shift
      ;;
    --excel)
      [ "$#" -ge 2 ] || { echo '[ERROR] --excel requires a path' >&2; exit 2; }
      EXCEL_FILE=$2
      shift 2
      ;;
    --max-products)
      [ "$#" -ge 2 ] || { echo '[ERROR] --max-products requires a number' >&2; exit 2; }
      MAX_PRODUCTS=$2
      shift 2
      ;;
    --private-dir)
      [ "$#" -ge 2 ] || { echo '[ERROR] --private-dir requires a path' >&2; exit 2; }
      RADMAN_PRIVATE_DIR=$2
      shift 2
      ;;
    --manifest)
      [ "$#" -ge 2 ] || { echo '[ERROR] --manifest requires a path' >&2; exit 2; }
      MANIFEST=$2
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[ -n "$MODE" ] || MODE=--plan
case "$MAX_PRODUCTS" in
  ''|*[!0-9]*) echo '[ERROR] MAX_PRODUCTS must be an integer from 1 to 1000' >&2; exit 2 ;;
esac
[ "$MAX_PRODUCTS" -ge 1 ] && [ "$MAX_PRODUCTS" -le 1000 ] || {
  echo '[ERROR] MAX_PRODUCTS must be from 1 to 1000' >&2
  exit 2
}
case "$EXCEL_FILE" in
  /*) ;;
  *) echo '[ERROR] EXCEL_FILE must be absolute' >&2; exit 2 ;;
esac
case "$EXCEL_FILE" in
  *public_html*) echo '[ERROR] public_html Excel paths are prohibited' >&2; exit 2 ;;
esac
case "$RADMAN_PRIVATE_DIR" in
  /*) ;;
  *) echo '[ERROR] RADMAN_PRIVATE_DIR must be absolute' >&2; exit 2 ;;
esac
case "$RADMAN_PRIVATE_DIR" in
  *public_html*) echo '[ERROR] public_html private paths are prohibited' >&2; exit 2 ;;
esac
case "$MANIFEST" in
  *public_html*) echo '[ERROR] public_html manifest paths are prohibited' >&2; exit 2 ;;
esac
command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "[ERROR] Python unavailable: $PYTHON_BIN" >&2
  exit 2
}
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 2)' || {
  echo '[ERROR] Python 3.11+ is required' >&2
  exit 2
}
"$PYTHON_BIN" -c 'import openpyxl; assert openpyxl.__version__' || {
  echo '[ERROR] کتابخانه openpyxl نصب نیست؛ اجرا کنید: python3 -m pip install --user openpyxl' >&2
  exit 2
}

if [ "$MODE" != "--import-drafts" ] && [ "$MODE" != "--identity-report" ]; then
  [ -r "$EXCEL_FILE" ] || {
    echo "[ERROR] Excel file is not readable: $EXCEL_FILE" >&2
    exit 2
  }
fi

if [ "$MODE" = "--identity-report" ]; then
  [ "${APP_ENV:-}" = "staging" ] || { echo '[ERROR] APP_ENV must equal staging' >&2; exit 2; }
  [ "${WP_URL:-}" = "https://staging.radmansilver.ir" ] || {
    echo '[ERROR] WP_URL must equal https://staging.radmansilver.ir' >&2
    exit 2
  }
  [ "${WP_PATH:-}" = "/home/radmansi/staging.radmansilver.ir" ] || {
    echo '[ERROR] WP_PATH must equal /home/radmansi/staging.radmansilver.ir' >&2
    exit 2
  }
  command -v wp >/dev/null 2>&1 || { echo '[ERROR] wp-cli unavailable' >&2; exit 2; }
fi

MUTATING_MODE=0
if [ "$MODE" = "--import-drafts" ] || [ "$MODE" = "--enrich-existing" ] || [ "$MODE" = "--full-pilot" ]; then
  MUTATING_MODE=1
  [ "${APP_ENV:-}" = "staging" ] || { echo '[ERROR] APP_ENV must equal staging' >&2; exit 2; }
  [ "${WP_URL:-}" = "https://staging.radmansilver.ir" ] || {
    echo '[ERROR] WP_URL must equal https://staging.radmansilver.ir' >&2
    exit 2
  }
  [ "${WP_PATH:-}" = "/home/radmansi/staging.radmansilver.ir" ] || {
    echo '[ERROR] WP_PATH must equal /home/radmansi/staging.radmansilver.ir' >&2
    exit 2
  }
  [ "${CONFIRM_STAGING_APPLY:-}" = "YES" ] || {
    echo '[ERROR] CONFIRM_STAGING_APPLY must equal YES' >&2
    exit 2
  }
  case "$WP_PATH" in
    *public_html*) echo '[ERROR] public_html WP_PATH is prohibited' >&2; exit 2 ;;
  esac
  command -v wp >/dev/null 2>&1 || { echo '[ERROR] wp-cli unavailable' >&2; exit 2; }
fi

if [ "$MODE" != "--inspect" ] && [ "$MODE" != "--plan" ] && [ "$MODE" != "--identity-report" ]; then
  mkdir -p "$RADMAN_PRIVATE_DIR/locks"
  LOCK_DIR=$RADMAN_PRIVATE_DIR/locks/excel-import-pipeline.lock
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo '[ERROR] another Excel import pipeline run holds the private lock' >&2
    exit 2
  fi
  trap cleanup EXIT
  trap 'exit 130' HUP INT TERM
fi

if [ "$MUTATING_MODE" -eq 1 ]; then
  BACKUP_DIR=$RADMAN_PRIVATE_DIR/backups
  mkdir -p "$BACKUP_DIR"
  BACKUP_STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  RADMAN_DB_BACKUP_PATH=$BACKUP_DIR/pre-excel-import-$BACKUP_STAMP.sql
  export RADMAN_DB_BACKUP_PATH
  echo '[BACKUP] creating staging database backup before Draft import'
  wp --path="$WP_PATH" --no-color db export "$RADMAN_DB_BACKUP_PATH" --quiet
  [ -s "$RADMAN_DB_BACKUP_PATH" ] || {
    echo '[ERROR] database backup is empty' >&2
    exit 2
  }
fi

printf '[SOURCE] Excel controls selection/price/stock/active; HTML product pages are the primary spec source.\n'
printf '[API] DEFERRED — no API probe or API credential is used.\n'

set -- "$MODE" \
  --excel "$EXCEL_FILE" \
  --max-products "$MAX_PRODUCTS" \
  --private-dir "$RADMAN_PRIVATE_DIR"
if [ -n "$MANIFEST" ]; then
  set -- "$@" --manifest "$MANIFEST"
fi
if [ -n "${WP_PATH:-}" ]; then
  set -- "$@" --wp-path "$WP_PATH"
fi

cd "$REPO_ROOT"
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON_BIN" agents/agent_excel_product_pipeline.py "$@"
