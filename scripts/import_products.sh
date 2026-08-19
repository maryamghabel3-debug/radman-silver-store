#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Owner CSV Product Import Runner
# ------------------------------------------------------------------------------
# Default --plan parses/validates the owner CSV and prints a dry-run preview.
# --apply-staging creates mandatory backups, then idempotently creates/updates
# WooCommerce products by SKU through wp-cli. New products are ALWAYS Draft.
# Existing product publication status is preserved; this runner never publishes.
#
# Input:
#   $RADMAN_PRIVATE_DIR/import/products.csv
#   $RADMAN_PRIVATE_DIR/import/images/<owner-provided files>
#   $RADMAN_PRIVATE_DIR/state/daily_rate.txt
#
# Modes:
#   --plan             default, no mutation
#   --apply-staging    staging mutation, requires CONFIRM_STAGING_APPLY=YES
#
# There is intentionally no production or auto-publish mode.
# ==============================================================================

set -Eeuo pipefail
# Never use set -x: environment values and future private data must not leak.
export PATH="$HOME/bin:$PATH"

readonly EXPECTED_APP_ENV="staging"
readonly EXPECTED_WP_URL="https://staging.radmansilver.ir"
readonly EXPECTED_WP_PATH="/home/radmansi/staging.radmansilver.ir"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT_FALLBACK="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly LOCK_NAME="product-import.lock"

MODE="plan"
DRY_RUN=1

log()  { printf '[INFO]  %s\n' "$*"; }
warn() { printf '[WARN]  %s\n' "$*" >&2; }
err()  { printf '[ERROR] %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

on_error() {
    local exit_code=$?
    local line=$1
    err "Product import aborted at line ${line} (exit=${exit_code})."
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

usage() {
    cat <<'USAGE'
Usage:
  bash scripts/import_products.sh --plan
  CONFIRM_STAGING_APPLY=YES bash scripts/import_products.sh --apply-staging

Owner input paths:
  $RADMAN_PRIVATE_DIR/import/products.csv
  $RADMAN_PRIVATE_DIR/import/images/
  $RADMAN_PRIVATE_DIR/state/daily_rate.txt

New products are always created as Draft. No payment, SMS, legal-page,
production, publication, or remote-image operation exists in this runner.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)           MODE="plan";  DRY_RUN=1; shift ;;
        --apply-staging)  MODE="apply"; DRY_RUN=0; shift ;;
        -h|--help)        usage; exit 0 ;;
        *)                usage; die "Unknown argument: $1" ;;
    esac
done

RADMAN_REPO_ROOT="${RADMAN_REPO_ROOT:-$REPO_ROOT_FALLBACK}"
RADMAN_PRIVATE_DIR="${RADMAN_PRIVATE_DIR:-$HOME/.config/radman}"
APP_ENV="${APP_ENV:-}"
WP_URL="${WP_URL:-}"
WP_PATH="${WP_PATH:-}"
CONFIRM_STAGING_APPLY="${CONFIRM_STAGING_APPLY:-}"
CSV_PATH="$RADMAN_PRIVATE_DIR/import/products.csv"
IMAGES_DIR="$RADMAN_PRIVATE_DIR/import/images"
DAILY_RATE_FILE="$RADMAN_PRIVATE_DIR/state/daily_rate.txt"
IMPORT_HELPER="$RADMAN_REPO_ROOT/scripts/import_products.py"
WP_CAPTURE_LIB="$RADMAN_REPO_ROOT/scripts/lib/wp_cli_capture.sh"

[[ -f "$IMPORT_HELPER" ]] || die "Importer helper missing: ${IMPORT_HELPER}"
[[ -f "$WP_CAPTURE_LIB" ]] || die "WP capture helper missing: ${WP_CAPTURE_LIB}"
[[ "$RADMAN_PRIVATE_DIR" != *"public_html"* ]] \
    || die "RADMAN_PRIVATE_DIR contains public_html; private imports must stay outside web roots."
[[ -f "$CSV_PATH" ]] || die "Owner CSV not found: ${CSV_PATH}"

# CloudLinux's default python3 is 3.6.8. Select and verify Python >= 3.11.
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
    || die "Python >=3.11 required; expected ~/bin/python3 or /opt/alt/python311/bin/python3.11."

log "RADMAN product import mode=${MODE}"
log "CSV=${CSV_PATH}"
log "Images=${IMAGES_DIR}"
log "Python=${PYTHON_BIN} (${PYTHON_VERSION})"

wp() {
    command wp --path="$WP_PATH" --no-color "$@"
}

if [[ "$MODE" == "apply" ]]; then
    [[ "$APP_ENV" == "$EXPECTED_APP_ENV" ]] \
        || die "APP_ENV must equal staging."
    [[ "$WP_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WP_URL must equal ${EXPECTED_WP_URL}."
    [[ "$WP_PATH" == "$EXPECTED_WP_PATH" ]] \
        || die "WP_PATH must equal ${EXPECTED_WP_PATH}."
    [[ "$WP_PATH" != *"public_html"* ]] \
        || die "WP_PATH containing public_html is PROHIBITED."
    [[ "$CONFIRM_STAGING_APPLY" == "YES" ]] \
        || die "CONFIRM_STAGING_APPLY must equal YES for --apply-staging."
    [[ -f "$WP_PATH/wp-settings.php" ]] \
        || die "WP_PATH is not a WordPress installation: ${WP_PATH}"
    type -P wp >/dev/null 2>&1 || die "wp-cli binary is required in PATH."

    # shellcheck source=scripts/lib/wp_cli_capture.sh
    source "$WP_CAPTURE_LIB"
    HOME_OPTION=""
    SITEURL_OPTION=""
    BLOG_PUBLIC=""
    CURRENCY=""
    wp_read_option HOME_OPTION home || die "Cannot read WordPress home after fallbacks."
    wp_read_option SITEURL_OPTION siteurl || die "Cannot read WordPress siteurl after fallbacks."
    wp_read_option BLOG_PUBLIC blog_public || die "Cannot read blog_public after fallbacks."
    wp_read_option CURRENCY woocommerce_currency || die "Cannot read WooCommerce currency after fallbacks."
    [[ "$HOME_OPTION" == "$EXPECTED_WP_URL" && "$SITEURL_OPTION" == "$EXPECTED_WP_URL" ]] \
        || die "WordPress home/siteurl do not match staging."
    [[ "$BLOG_PUBLIC" == "0" ]] || die "Staging must remain noindex (blog_public=0)."
    [[ "$CURRENCY" == "IRT" ]] || die "WooCommerce currency must remain IRT (Toman direct)."

    mkdir -p "$RADMAN_PRIVATE_DIR/backups" "$RADMAN_PRIVATE_DIR/locks" "$IMAGES_DIR"
    chmod 700 "$RADMAN_PRIVATE_DIR" "$RADMAN_PRIVATE_DIR/backups" \
        "$RADMAN_PRIVATE_DIR/locks" "$RADMAN_PRIVATE_DIR/import" "$IMAGES_DIR"
    LOCK_FILE="$RADMAN_PRIVATE_DIR/locks/$LOCK_NAME"
    exec {LOCK_FD}>"$LOCK_FILE"
    flock -n "$LOCK_FD" || die "Another product import is running (lock held)."

    # Mandatory backups happen before the Python helper can mutate products/media.
    TIMESTAMP="$(date +%Y%m%d-%H%M%S)-$$"
    DB_BACKUP="$RADMAN_PRIVATE_DIR/backups/pre-product-import-${TIMESTAMP}.sql"
    INPUT_BACKUP="$RADMAN_PRIVATE_DIR/backups/product-import-input-${TIMESTAMP}.csv"
    log "Creating mandatory pre-change backups..."
    wp db export "$DB_BACKUP" >/dev/null
    [[ -s "$DB_BACKUP" ]] || die "Database backup is empty; refusing import."
    chmod 600 "$DB_BACKUP"
    install -m 600 "$CSV_PATH" "$INPUT_BACKUP"
    log "DB backup: ${DB_BACKUP}"
    log "CSV backup: ${INPUT_BACKUP}"

    "$PYTHON_BIN" "$IMPORT_HELPER" \
        --csv "$CSV_PATH" \
        --images-dir "$IMAGES_DIR" \
        --daily-rate-file "$DAILY_RATE_FILE" \
        --wp-path "$WP_PATH" \
        --apply-staging

    log "Product import completed on STAGING. New products remain DRAFT."
    log "No product was published. Payment, SMS, and site settings remain untouched."
    exit 0
fi

# PLAN: parse locally. If run on the actual host with wp available, also perform
# read-only SKU inspection so the preview says CREATE vs UPDATE.
PLAN_ARGS=(
    --csv "$CSV_PATH"
    --images-dir "$IMAGES_DIR"
    --daily-rate-file "$DAILY_RATE_FILE"
)
if [[ -n "$WP_PATH" && -f "$WP_PATH/wp-settings.php" ]] && type -P wp >/dev/null 2>&1; then
    PLAN_ARGS+=(--wp-path "$WP_PATH" --inspect-wp)
    log "WP detected: plan will perform read-only SKU inspection."
else
    log "WP not detected: action column will say CHECK-AT-APPLY (still no mutation)."
fi
"$PYTHON_BIN" "$IMPORT_HELPER" "${PLAN_ARGS[@]}"
log "PLAN complete. No host/product/media mutation was performed."
