#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER — Three-product catalog + media QA pilot
# ------------------------------------------------------------------------------
# Repo/host-safe orchestration only. No WordPress, product import, publishing,
# payment, SMS, production, model download, or generative imagery operation.
# ==============================================================================

set -Eeuo pipefail
# Never use set -x: private paths and future owner data must not leak.
export PATH="$HOME/bin:$PATH"

readonly EXPECTED_APP_ENV="staging"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT_FALLBACK="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly HARD_MAX_PRODUCTS=3

MODE="plan"

log()  { printf '[INFO]  %s\n' "$*"; }
err()  { printf '[ERROR] %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

on_error() {
    local exit_code=$?
    local line=$1
    err "Media pilot stopped at line ${line} (exit=${exit_code})."
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

usage() {
    cat <<'USAGE'
Usage:
  MODEL_NAME=birefnet-general-lite bash scripts/run_product_media_pilot.sh --plan
  bash scripts/run_product_media_pilot.sh --scrape-three
  MODEL_NAME=birefnet-general-lite bash scripts/run_product_media_pilot.sh --process-three
  MODEL_NAME=birefnet-general-lite bash scripts/run_product_media_pilot.sh --full-pilot

Required for every mode:
  APP_ENV=staging
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman

BRIA is blocked unless IMAGE_PIPELINE_EVALUATION_ONLY=1. It is never approved
for commercial publication by this pilot. There is no WordPress import mode.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)           MODE="plan"; shift ;;
        --scrape-three)   MODE="scrape"; shift ;;
        --process-three)  MODE="process"; shift ;;
        --full-pilot)     MODE="full"; shift ;;
        -h|--help)        usage; exit 0 ;;
        *)                usage; die "Unknown argument: $1" ;;
    esac
done

RADMAN_REPO_ROOT="${RADMAN_REPO_ROOT:-$REPO_ROOT_FALLBACK}"
RADMAN_PRIVATE_DIR="${RADMAN_PRIVATE_DIR:-}"
APP_ENV="${APP_ENV:-}"
WP_PATH="${WP_PATH:-}"
MODEL_NAME="${MODEL_NAME:-}"

[[ "$APP_ENV" == "$EXPECTED_APP_ENV" ]] || die "APP_ENV must equal staging."
[[ -n "$RADMAN_PRIVATE_DIR" ]] || die "RADMAN_PRIVATE_DIR is required."
[[ "$RADMAN_PRIVATE_DIR" != *"public_html"* ]] || die "RADMAN_PRIVATE_DIR containing public_html is prohibited."
[[ "$WP_PATH" != *"public_html"* ]] || die "WP_PATH containing public_html is prohibited."
[[ "$RADMAN_PRIVATE_DIR" != "$WP_PATH" || -z "$WP_PATH" ]] \
    || die "RADMAN_PRIVATE_DIR must not equal WP_PATH."

CATALOG_AGENT="$RADMAN_REPO_ROOT/agents/agent_legacy_catalog_pilot.py"
MEDIA_AGENT="$RADMAN_REPO_ROOT/agents/agent_product_media_processor.py"
[[ -f "$CATALOG_AGENT" ]] || die "Missing catalog pilot: ${CATALOG_AGENT}"
[[ -f "$MEDIA_AGENT" ]] || die "Missing media processor: ${MEDIA_AGENT}"

PYTHON_BIN=""
PYTHON_VERSION=""
for candidate in "$HOME/bin/python3" /opt/alt/python311/bin/python3.11 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        candidate_version="$("$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
        candidate_major="${candidate_version%%.*}"
        candidate_minor="${candidate_version##*.}"
        if [[ "$candidate_major" =~ ^[0-9]+$ && "$candidate_minor" =~ ^[0-9]+$ \
              && "$candidate_major" -eq 3 && "$candidate_minor" -ge 11 ]]; then
            PYTHON_BIN="$candidate"
            PYTHON_VERSION="$candidate_version"
            break
        fi
    fi
done
[[ -n "$PYTHON_BIN" ]] \
    || die "Python >=3.11 required; expected /opt/alt/python311/bin/python3.11."

if [[ "$MODE" == "plan" || "$MODE" == "process" || "$MODE" == "full" ]]; then
    [[ -n "$MODEL_NAME" ]] \
        || die "MODEL_NAME must be explicit (birefnet-general-lite or u2net)."
fi

if [[ "$MODE" != "plan" ]]; then
    mkdir -p "$RADMAN_PRIVATE_DIR/locks"
    chmod 700 "$RADMAN_PRIVATE_DIR" "$RADMAN_PRIVATE_DIR/locks"
    LOCK_FILE="$RADMAN_PRIVATE_DIR/locks/product-media-pilot.lock"
    exec {LOCK_FD}>"$LOCK_FILE"
    flock -n "$LOCK_FD" || die "Another product media pilot is running (lock held)."
fi

log "RADMAN three-product media pilot mode=${MODE}"
log "Python=${PYTHON_BIN} (${PYTHON_VERSION})"
log "Private dir=${RADMAN_PRIVATE_DIR}"
log "Hard maximum products=${HARD_MAX_PRODUCTS}"
log "WordPress/product import=DISABLED"

case "$MODE" in
    plan)
        "$PYTHON_BIN" "$CATALOG_AGENT" \
            --plan --limit "$HARD_MAX_PRODUCTS" --private-dir "$RADMAN_PRIVATE_DIR"
        "$PYTHON_BIN" "$MEDIA_AGENT" \
            --plan --limit "$HARD_MAX_PRODUCTS" --private-dir "$RADMAN_PRIVATE_DIR" \
            --model-name "$MODEL_NAME"
        ;;
    scrape)
        "$PYTHON_BIN" "$CATALOG_AGENT" \
            --scrape --limit "$HARD_MAX_PRODUCTS" --private-dir "$RADMAN_PRIVATE_DIR"
        ;;
    process)
        "$PYTHON_BIN" "$MEDIA_AGENT" \
            --process --limit "$HARD_MAX_PRODUCTS" --private-dir "$RADMAN_PRIVATE_DIR" \
            --model-name "$MODEL_NAME"
        ;;
    full)
        "$PYTHON_BIN" "$CATALOG_AGENT" \
            --scrape --limit "$HARD_MAX_PRODUCTS" --private-dir "$RADMAN_PRIVATE_DIR"
        "$PYTHON_BIN" "$MEDIA_AGENT" \
            --process --limit "$HARD_MAX_PRODUCTS" --private-dir "$RADMAN_PRIVATE_DIR" \
            --model-name "$MODEL_NAME"
        ;;
esac

log "Pilot stage complete. Review contact sheets before any later import mission."
log "NO WORDPRESS IMPORT OR PRODUCT PUBLICATION WAS PERFORMED."
