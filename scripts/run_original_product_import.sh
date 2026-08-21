#!/bin/sh
# One-command host runner for PR-25. POSIX sh / cPanel-jailshell compatible.
set -eu

umask 077
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
RADMAN_PRIVATE_DIR=${RADMAN_PRIVATE_DIR:-/home/radmansi/private}
MODE=
LIMIT=10
SOURCE_MANIFEST=
PREPARED_MANIFEST=
LOCK_DIR=

cleanup() {
  if [ -n "$LOCK_DIR" ] && [ -d "$LOCK_DIR" ]; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

usage() {
  cat <<'EOF'
Usage: scripts/run_original_product_import.sh MODE [options]

Modes (choose exactly one):
  --plan              Print a zero-mutation plan
  --scrape-only       Scrape up to 10 real legacy products and original images
  --image-qa          Run color/detail QA and produce prepared reports
  --pricing-preview   Preview classification and Toman floor pricing, no import
  --import-drafts     Import a prepared QA manifest as create-only drafts
  --full-pilot        Scrape, QA, price, report, and import guarded drafts

Options:
  --limit N
  --source-manifest PATH
  --prepared-manifest PATH
  --private-dir PATH

Mutation requires APP_ENV=staging, WP_URL=https://staging.radmansilver.ir,
WP_PATH=/home/radmansi/staging.radmansilver.ir, CONFIRM_STAGING_APPLY=YES.
A fresh private database backup is created before draft import.
EOF
}

set_mode() {
  if [ -n "$MODE" ]; then
    echo "[ERROR] choose exactly one mode" >&2
    exit 2
  fi
  MODE=$1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --plan|--scrape-only|--image-qa|--pricing-preview|--import-drafts|--full-pilot)
      set_mode "$1"
      shift
      ;;
    --limit)
      [ "$#" -ge 2 ] || { echo "[ERROR] --limit requires a value" >&2; exit 2; }
      LIMIT=$2
      shift 2
      ;;
    --source-manifest)
      [ "$#" -ge 2 ] || { echo "[ERROR] --source-manifest requires a path" >&2; exit 2; }
      SOURCE_MANIFEST=$2
      shift 2
      ;;
    --prepared-manifest)
      [ "$#" -ge 2 ] || { echo "[ERROR] --prepared-manifest requires a path" >&2; exit 2; }
      PREPARED_MANIFEST=$2
      shift 2
      ;;
    --private-dir)
      [ "$#" -ge 2 ] || { echo "[ERROR] --private-dir requires a path" >&2; exit 2; }
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

[ -n "$MODE" ] || MODE=--plan
case "$LIMIT" in
  ''|*[!0-9]*) echo "[ERROR] --limit must be an integer from 1 to 10" >&2; exit 2 ;;
esac
[ "$LIMIT" -ge 1 ] && [ "$LIMIT" -le 10 ] || {
  echo "[ERROR] --limit must be from 1 to 10" >&2
  exit 2
}
case "$RADMAN_PRIVATE_DIR" in
  /*) ;;
  *) echo "[ERROR] RADMAN_PRIVATE_DIR must be an absolute private path" >&2; exit 2 ;;
esac
case "$RADMAN_PRIVATE_DIR" in
  *public_html*) echo "[ERROR] RADMAN_PRIVATE_DIR cannot contain public_html" >&2; exit 2 ;;
esac

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] Python is unavailable: $PYTHON_BIN" >&2
  exit 2
fi
PYTHON_VERSION=$($PYTHON_BIN -c 'import sys; print("%d.%d" % sys.version_info[:2])')
case "$PYTHON_VERSION" in
  3.11|3.12|3.13|3.14) ;;
  *) echo "[ERROR] Python 3.11+ is required; found $PYTHON_VERSION" >&2; exit 2 ;;
esac

MUTATING_MODE=0
if [ "$MODE" = "--import-drafts" ] || [ "$MODE" = "--full-pilot" ]; then
  MUTATING_MODE=1
  # Reject an unsafe target before creating a lock, backup, or any other artifact.
  [ "${APP_ENV:-}" = "staging" ] || { echo "[ERROR] APP_ENV must equal staging" >&2; exit 2; }
  [ "${WP_URL:-}" = "https://staging.radmansilver.ir" ] || {
    echo "[ERROR] WP_URL must equal https://staging.radmansilver.ir" >&2
    exit 2
  }
  [ "${WP_PATH:-}" = "/home/radmansi/staging.radmansilver.ir" ] || {
    echo "[ERROR] WP_PATH must equal /home/radmansi/staging.radmansilver.ir" >&2
    exit 2
  }
  [ "${CONFIRM_STAGING_APPLY:-}" = "YES" ] || {
    echo "[ERROR] CONFIRM_STAGING_APPLY must equal YES" >&2
    exit 2
  }
  case "$WP_PATH" in
    *public_html*) echo "[ERROR] public_html is prohibited" >&2; exit 2 ;;
  esac
  command -v wp >/dev/null 2>&1 || { echo "[ERROR] wp-cli is unavailable" >&2; exit 2; }
fi

if [ "$MODE" != "--plan" ]; then
  mkdir -p "$RADMAN_PRIVATE_DIR/locks"
  LOCK_DIR=$RADMAN_PRIVATE_DIR/locks/original-product-pipeline.lock
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "[ERROR] another original-product pipeline run holds the private lock" >&2
    exit 2
  fi
  trap cleanup EXIT
  trap 'exit 130' HUP INT TERM
fi

if [ "$MUTATING_MODE" -eq 1 ]; then
  BACKUP_DIR=$RADMAN_PRIVATE_DIR/backups
  mkdir -p "$BACKUP_DIR"
  BACKUP_STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  RADMAN_DB_BACKUP_PATH=$BACKUP_DIR/pre-original-products-$BACKUP_STAMP.sql
  export RADMAN_DB_BACKUP_PATH
  echo "[BACKUP] creating private staging database backup"
  wp --path="$WP_PATH" --no-color db export "$RADMAN_DB_BACKUP_PATH" --quiet
  [ -s "$RADMAN_DB_BACKUP_PATH" ] || { echo "[ERROR] database backup is empty" >&2; exit 2; }
fi

set -- "$MODE" --limit "$LIMIT" --private-dir "$RADMAN_PRIVATE_DIR"
if [ -n "$SOURCE_MANIFEST" ]; then
  set -- "$@" --source-manifest "$SOURCE_MANIFEST"
fi
if [ -n "$PREPARED_MANIFEST" ]; then
  set -- "$@" --prepared-manifest "$PREPARED_MANIFEST"
fi
if [ -n "${WP_PATH:-}" ]; then
  set -- "$@" --wp-path "$WP_PATH"
fi

cd "$REPO_ROOT"
export RADMAN_PRIVATE_DIR
export PYTHONDONTWRITEBYTECODE=1
"$PYTHON_BIN" agents/agent_original_product_pipeline.py "$@"
