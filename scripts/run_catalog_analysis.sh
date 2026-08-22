#!/usr/bin/env bash
# Read-only Excel catalog analysis runner for PR-28A.
set -euo pipefail

umask 077
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
EXCEL_PATH=/home/radmansi/radman-deploy/products_20260821_182238.xlsx
SHEET_NAME='همه محصولات'
RADMAN_PRIVATE_DIR=${RADMAN_PRIVATE_DIR:-/home/radmansi/private}
HEADER_ROW=1

usage() {
  cat <<'EOF'
Usage: bash scripts/run_catalog_analysis.sh [options]

Options:
  --excel PATH         XLSX source (default owner export path)
  --sheet NAME         Sheet name (default: همه محصولات)
  --header-row N       Header row number (default: 1)
  --private-dir PATH   Private report root (or set RADMAN_PRIVATE_DIR)
  --help               Show this help

Reads Excel only. It performs no WordPress, media, network, or import operation.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --excel)
      [ "$#" -ge 2 ] || { echo '[ERROR] --excel requires a path' >&2; exit 2; }
      EXCEL_PATH=$2
      shift 2
      ;;
    --sheet)
      [ "$#" -ge 2 ] || { echo '[ERROR] --sheet requires a value' >&2; exit 2; }
      SHEET_NAME=$2
      shift 2
      ;;
    --header-row)
      [ "$#" -ge 2 ] || { echo '[ERROR] --header-row requires a number' >&2; exit 2; }
      HEADER_ROW=$2
      shift 2
      ;;
    --private-dir)
      [ "$#" -ge 2 ] || { echo '[ERROR] --private-dir requires a path' >&2; exit 2; }
      RADMAN_PRIVATE_DIR=$2
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

case "$HEADER_ROW" in
  ''|*[!0-9]*) echo '[ERROR] --header-row must be a positive integer' >&2; exit 2 ;;
esac
[ "$HEADER_ROW" -ge 1 ] || { echo '[ERROR] --header-row must be >= 1' >&2; exit 2; }
case "$EXCEL_PATH" in
  /*) ;;
  *) echo '[ERROR] Excel path must be absolute' >&2; exit 2 ;;
esac
case "$EXCEL_PATH" in
  *public_html*) echo '[ERROR] reading any public_html path is prohibited' >&2; exit 2 ;;
esac
case "$RADMAN_PRIVATE_DIR" in
  /*) ;;
  *) echo '[ERROR] RADMAN_PRIVATE_DIR must be absolute' >&2; exit 2 ;;
esac
case "$RADMAN_PRIVATE_DIR" in
  *public_html*) echo '[ERROR] RADMAN_PRIVATE_DIR cannot contain public_html' >&2; exit 2 ;;
esac
[ -r "$EXCEL_PATH" ] || { echo "[ERROR] Excel file is not readable: $EXCEL_PATH" >&2; exit 2; }
command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "[ERROR] Python is unavailable: $PYTHON_BIN" >&2
  exit 2
}
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 2)' || {
  echo '[ERROR] Python 3.11+ is required' >&2
  exit 2
}

OUTPUT_DIR=$RADMAN_PRIVATE_DIR/legacy-cache
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$("$PYTHON_BIN" -c 'from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo("Asia/Tehran")).strftime("%Y%m%dT%H%M%S%f%z"))')
OUTPUT_PATH=$OUTPUT_DIR/catalog-analysis-$TIMESTAMP.txt
TEMP_PATH=$(mktemp "$OUTPUT_PATH.tmp.XXXXXX")
cleanup() {
  rm -f "$TEMP_PATH"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

cd "$REPO_ROOT"
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON_BIN" scripts/analyze_excel_catalog.py \
  --excel "$EXCEL_PATH" \
  --sheet "$SHEET_NAME" \
  --header-row "$HEADER_ROW" \
  | tee "$TEMP_PATH"

mv "$TEMP_PATH" "$OUTPUT_PATH"
trap - EXIT HUP INT TERM
printf '\n[SAVED] %s\n' "$OUTPUT_PATH"
printf '[SAFETY] Analysis only; no WordPress, image, network, or import operation ran.\n'
