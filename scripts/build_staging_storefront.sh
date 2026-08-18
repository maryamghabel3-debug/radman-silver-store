#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Final One-Command Staging Storefront Foundation
# ------------------------------------------------------------------------------
# Idempotent, staging-only, plan-by-default batch runner that:
#   1. Verifies strict staging guards (APP_ENV, WP_URL, WP_PATH, noindex, theme).
#   2. Delegates static content + child-theme sync to the reviewed runner
#      scripts/radman_stage_apply.sh (which itself calls the lower-level
#      radman_branding_and_content_import.sh runner).
#   3. Deploys the reviewed homepage foundation (Gutenberg blocks) onto
#      existing page ID 18 (Published on staging only; stays noindex).
#   4. Creates/updates three product categories (rings, necklaces, bracelets)
#      by slug — idempotent, never deletes existing terms.
#   5. Creates/updates the approved primary navigation menu ("منوی اصلی رادمان")
#      containing only approved items; Draft pages never appear.
#   6. Reads and reports WooCommerce baseline (currency, decimals, page IDs,
#      shipping, payment) without changing commercial behavior.
#   7. Reads and reports LiteSpeed status without enabling optimizations.
#   8. Creates timestamped DB + child-theme + homepage backups before mutation.
#
# MODES:
#   --plan            (default) Read-only dry run; prints intent, touches nothing.
#   --check           Read-only verification pass (WP-CLI status queries only).
#   --apply-staging   Execute mutating operations (CONFIRM_STAGING_APPLY=YES).
#
# PRODUCTION IS PROHIBITED BY DESIGN. There is no --apply-production flag.
# Payments, SMS, Redis, analytics, and SEO indexing are NEVER enabled by this
# script. All 11 static pages remain Draft.
#
# REQUIRED ENVIRONMENT VARIABLES (apply mode):
#   APP_ENV=staging
#   WP_URL=https://staging.radmansilver.ir
#   WP_PATH=/home/radmansi/staging.radmansilver.ir
#   RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo
#   RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman
#   CONFIRM_STAGING_APPLY=YES   (only for --apply-staging)
# ==============================================================================

set -Eeuo pipefail
# NO 'set -x' — credentials and env must never leak into logs.
export PATH="$HOME/bin:$PATH"

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
readonly EXPECTED_WP_URL="https://staging.radmansilver.ir"
readonly EXPECTED_WP_PATH="/home/radmansi/staging.radmansilver.ir"
readonly EXPECTED_APP_ENV="staging"
readonly EXPECTED_BLOG_PUBLIC=0
readonly LOCK_NAME="radman-storefront-batch.lock"
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT_FALLBACK="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly HOMEPAGE_TEMPLATE_RELPATH="templates/home-page-gutenberg.html"
readonly STATIC_RUNNER_RELPATH="scripts/radman_stage_apply.sh"
readonly REGISTRY_RELPATH="docs/STATIC-CONTENT-APPROVAL-REGISTRY.md"
readonly HOMEPAGE_ID=18
readonly SHOP_PAGE_ID=6
readonly CART_PAGE_ID=7
readonly CHECKOUT_PAGE_ID=8
readonly MYACCOUNT_PAGE_ID=9

MODE="plan"
DRY_RUN=1
CHECK_ONLY=0

readonly -a STATIC_SLUGS=(
    about-us contact-us faq shipping returns privacy-policy-radman terms
    ring-size-guide silver-care silver-925-authenticity gemstones
)

# Approved product categories (slug|name|parent)
readonly -a CATEGORY_SPECS=(
    "rings|انگشتر|"
    "necklaces|گردنبند|"
    "bracelets|دستبند|"
)

# Approved menu items. Defined in a function because readonly arrays freeze
# values at declaration time and we need to reference variables like
# HOMEPAGE_ID / SHOP_PAGE_ID / CART_PAGE_ID / MYACCOUNT_PAGE_ID.
# Format per item: label|type|object-id
# type can be: page, tax, custom
MENU_NAME="منوی اصلی رادمان"

build_menu_items() {
    MENU_ITEMS=(
        "خانه|page|${HOMEPAGE_ID}"
        "فروشگاه|page|${SHOP_PAGE_ID}"
        "انگشتر|tax|rings"
        "گردنبند|tax|necklaces"
        "دستبند|tax|bracelets"
        "حساب کاربری|page|${MYACCOUNT_PAGE_ID}"
        "سبد خرید|page|${CART_PAGE_ID}"
    )
}
build_menu_items

# -----------------------------------------------------------------------------
# Logging helpers (never echo env wholesale; never echo credentials).
# -----------------------------------------------------------------------------
log()  { printf '[INFO]  %s\n' "$*"; }
warn() { printf '[WARN]  %s\n' "$*" >&2; }
err()  { printf '[ERROR] %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

on_error() {
    local exit_code=$?
    local line=$1
    err "Script aborted (line ${line}, exit=${exit_code})."
    err "NO HOST MUTATION WAS PERFORMED unless [APPLY] messages above indicate otherwise."
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

usage() {
    cat <<'USAGE'
Usage:
  bash scripts/build_staging_storefront.sh --plan            # dry run (default)
  bash scripts/build_staging_storefront.sh --check           # read-only verification
  bash scripts/build_staging_storefront.sh --apply-staging   # mutate staging

Required env for --apply-staging:
  export PATH="$HOME/bin:$PATH"
  APP_ENV=staging
  CONFIRM_STAGING_APPLY=YES
  WP_PATH=/home/radmansi/staging.radmansilver.ir
  WP_URL=https://staging.radmansilver.ir
  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman

Production, payment, SMS, Redis, analytics, and SEO indexing are NEVER
enabled by this script. All 11 static pages remain Draft.
USAGE
}

# -----------------------------------------------------------------------------
# Argument parsing
# -----------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)            MODE="plan";      DRY_RUN=1; CHECK_ONLY=0; shift ;;
        --check)           MODE="check";     DRY_RUN=1; CHECK_ONLY=1; shift ;;
        --apply-staging)   MODE="apply";     DRY_RUN=0; CHECK_ONLY=0; shift ;;
        -h|--help)         usage; exit 0 ;;
        *)                 usage; die "Unknown argument: $1" ;;
    esac
done

RADMAN_REPO_ROOT="${RADMAN_REPO_ROOT:-$REPO_ROOT_FALLBACK}"
APP_ENV="${APP_ENV:-}"
WP_URL="${WP_URL:-}"
WP_PATH="${WP_PATH:-}"
RADMAN_PRIVATE_DIR="${RADMAN_PRIVATE_DIR:-}"
CONFIRM_STAGING_APPLY="${CONFIRM_STAGING_APPLY:-}"

log "RADMAN SILVER 925 — Final Staging Storefront Batch"
log "Mode: ${MODE}    (dry_run=${DRY_RUN})"
log "RADMAN_REPO_ROOT = ${RADMAN_REPO_ROOT}"

# -----------------------------------------------------------------------------
# Required repository files
# -----------------------------------------------------------------------------
[[ -d "$RADMAN_REPO_ROOT/content/static-pages" ]] \
    || die "RADMAN_REPO_ROOT does not contain content/static-pages/: ${RADMAN_REPO_ROOT}"
[[ -f "$RADMAN_REPO_ROOT/$HOMEPAGE_TEMPLATE_RELPATH" ]] \
    || die "Homepage Gutenberg template missing: ${RADMAN_REPO_ROOT}/${HOMEPAGE_TEMPLATE_RELPATH}"
[[ -f "$RADMAN_REPO_ROOT/$STATIC_RUNNER_RELPATH" ]] \
    || die "Static runner missing: ${RADMAN_REPO_ROOT}/${STATIC_RUNNER_RELPATH}"
[[ -f "$RADMAN_REPO_ROOT/$REGISTRY_RELPATH" ]] \
    || die "Approval registry missing: ${RADMAN_REPO_ROOT}/${REGISTRY_RELPATH}"
[[ -f "$RADMAN_REPO_ROOT/scripts/check_no_placeholders.py" ]] \
    || die "Placeholder gate missing: scripts/check_no_placeholders.py"
[[ -d "$RADMAN_REPO_ROOT/theme/blocksy-child" ]] \
    || die "Child theme source missing: theme/blocksy-child/"

# -----------------------------------------------------------------------------
# Python availability/version gate
# -----------------------------------------------------------------------------
PYTHON_BIN=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        PYTHON_BIN="$cand"
        break
    fi
done
[[ -n "$PYTHON_BIN" ]] || die "Python 3.11+ is required but no python3/python was found in PATH."
PY_VER="$($PYTHON_BIN -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PY_MAJOR="${PY_VER%%.*}"
PY_MINOR="${PY_VER##*.}"
[[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 11 ]] \
    || die "Python >= 3.11 required (found: ${PY_VER}). Ensure PATH includes ~/bin (or host-managed python3.11)."
log "Python binary: ${PYTHON_BIN} (${PY_VER}) ✓"

# -----------------------------------------------------------------------------
# Enforce strict staging guards when any host-facing mode is used
# -----------------------------------------------------------------------------
if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    [[ -n "$WP_PATH" ]]           || die "WP_PATH is required in ${MODE} mode."
    [[ -n "$WP_URL" ]]            || die "WP_URL is required in ${MODE} mode."
    [[ -n "$RADMAN_PRIVATE_DIR" ]]|| die "RADMAN_PRIVATE_DIR is required in ${MODE} mode."

    [[ "$APP_ENV" == "$EXPECTED_APP_ENV" ]] \
        || die "APP_ENV must equal '${EXPECTED_APP_ENV}' (got: '${APP_ENV}'). Production is PROHIBITED."
    [[ "$WP_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WP_URL must equal '${EXPECTED_WP_URL}' (got: '${WP_URL}')."
    [[ "$WP_PATH" == "$EXPECTED_WP_PATH" ]] \
        || die "WP_PATH must equal '${EXPECTED_WP_PATH}' (got: '${WP_PATH}')."
    [[ "$WP_PATH" != *"public_html"* ]] \
        || die "WP_PATH contains 'public_html' — PRODUCTION PATH PROHIBITED."
    [[ -f "$WP_PATH/wp-settings.php" ]] \
        || die "WP_PATH does not look like a WordPress install (missing wp-settings.php): ${WP_PATH}"

    # wp-cli must be available
    command -v wp >/dev/null 2>&1 || die "wp-cli (wp) is required in PATH for ${MODE} mode."
fi

if [[ "$MODE" == "apply" ]]; then
    [[ "$CONFIRM_STAGING_APPLY" == "YES" ]] \
        || die "CONFIRM_STAGING_APPLY must equal 'YES' for --apply-staging."
fi

# -----------------------------------------------------------------------------
# WP-CLI wrapper (forces --path; never leaks env wholesale)
# -----------------------------------------------------------------------------
wp() {
    command wp --path="$WP_PATH" --no-color "$@"
}

wp_available() { command -v wp >/dev/null 2>&1; }

# -----------------------------------------------------------------------------
# Private dir / lock / backup locations
# -----------------------------------------------------------------------------
LOCK_FD=""
BACKUP_DIR=""
LOCKFILE=""
if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    mkdir -p "$RADMAN_PRIVATE_DIR"
    chmod 700 "$RADMAN_PRIVATE_DIR"
    local locks_dir="$RADMAN_PRIVATE_DIR/locks"
    mkdir -p "$locks_dir"
    chmod 700 "$locks_dir"
    LOCKFILE="$locks_dir/${LOCK_NAME}"
    BACKUP_DIR="$RADMAN_PRIVATE_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
    log "Opening lock on ${LOCKFILE}"
    exec {LOCK_FD}>"$LOCKFILE"
    if [[ "$DRY_RUN" -eq 0 ]]; then
        flock -n "$LOCK_FD" || die "Another deployment appears to be running (lock held)."
    else
        flock -n "$LOCK_FD" || warn "Lock currently held by another process."
    fi
fi

TS="$(date +%Y%m%d-%H%M%S)"

# -----------------------------------------------------------------------------
# Helper: read WP option safely
# -----------------------------------------------------------------------------
wp_opt() {
    wp option get "$1" --format=trim 2>/dev/null || echo "__MISSING__"
}

# -----------------------------------------------------------------------------
# Guard verification (host-facing modes)
# -----------------------------------------------------------------------------
BLOG_PUBLIC="__PLAN__"
ACTIVE_THEME="__PLAN__"
CURRENCY="__PLAN__"
DECIMALS="__PLAN__"
SHOW_ON_FRONT="__PLAN__"
PAGE_ON_FRONT="__PLAN__"
HOME_URL="__PLAN__"
SITE_URL="__PLAN__"

if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    log "Verifying staging identity..."
    BLOG_PUBLIC="$(wp_opt blog_public)"
    [[ "$BLOG_PUBLIC" == "$EXPECTED_BLOG_PUBLIC" ]] \
        || die "blog_public is '${BLOG_PUBLIC}' (expected '${EXPECTED_BLOG_PUBLIC}'). Staging must remain noindex."

    HOME_URL="$(wp_opt home)"
    SITE_URL="$(wp_opt siteurl)"
    [[ "$HOME_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WordPress home option is '${HOME_URL}' (expected '${EXPECTED_WP_URL}')."
    [[ "$SITE_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WordPress siteurl option is '${SITE_URL}' (expected '${EXPECTED_WP_URL}')."

    ACTIVE_THEME="$(wp theme list --status=active --field=name --format=trim 2>/dev/null || echo unknown)"
    if [[ "$ACTIVE_THEME" != "blocksy-child" && "$ACTIVE_THEME" != "blocksy" ]]; then
        die "Active theme '${ACTIVE_THEME}' is not Blocksy-compatible. Refusing to proceed."
    fi

    CURRENCY="$(wp_opt woocommerce_currency)"
    DECIMALS="$(wp_opt woocommerce_price_num_decimals)"
    SHOW_ON_FRONT="$(wp_opt show_on_front)"
    PAGE_ON_FRONT="$(wp_opt page_on_front)"

    # Verify page 18 exists
    if ! wp post get "$HOMEPAGE_ID" --format=ids >/dev/null 2>&1; then
        die "Homepage ID ${HOMEPAGE_ID} does not exist. Refusing to create a new homepage outside of plan."
    fi
fi

# -----------------------------------------------------------------------------
# Print PLAN / CHECK / APPLY header table
# -----------------------------------------------------------------------------
print_guard_section() {
    log ""
    log "=================== ENVIRONMENT GUARDS ==================="
    printf '  %-32s %s\n' "APP_ENV"          "$APP_ENV"
    printf '  %-32s %s\n' "WP_URL"           "$WP_URL"
    printf '  %-32s %s\n' "WP_PATH"          "$WP_PATH"
    printf '  %-32s %s\n' "blog_public (noindex)" "${BLOG_PUBLIC} (expected ${EXPECTED_BLOG_PUBLIC})"
    printf '  %-32s %s\n' "home"             "$HOME_URL"
    printf '  %-32s %s\n' "siteurl"          "$SITE_URL"
    printf '  %-32s %s\n' "Active theme"     "$ACTIVE_THEME"
    printf '  %-32s %s\n' "WooCommerce currency"  "$CURRENCY (expected IRT)"
    printf '  %-32s %s\n' "Price decimals"        "$DECIMALS (expected 0)"
    printf '  %-32s %s\n' "show_on_front"         "$SHOW_ON_FRONT (expected page)"
    printf '  %-32s %s\n' "page_on_front"         "$PAGE_ON_FRONT (expected ${HOMEPAGE_ID})"
    log "=========================================================="
    log ""
}
print_guard_section

# -----------------------------------------------------------------------------
# Phase 1 — Static content + Child Theme (delegated to reviewed runner)
# -----------------------------------------------------------------------------
run_static_runner_subplan() {
    # Sub-runner already handles its own plan output; we wrap to clearly
    # delimit phases in the batch log.
    local sub_mode="$1"
    log ">>>>>>>>>> Phase 1: Static pages + Child theme (mode=${sub_mode})"
    if [[ "$sub_mode" == "plan" ]]; then
        APP_ENV="$APP_ENV" WP_URL="$WP_URL" WP_PATH="$WP_PATH" \
        RADMAN_REPO_ROOT="$RADMAN_REPO_ROOT" RADMAN_PRIVATE_DIR="$RADMAN_PRIVATE_DIR" \
            bash "$RADMAN_REPO_ROOT/$STATIC_RUNNER_RELPATH" --plan
    elif [[ "$sub_mode" == "check" ]]; then
        APP_ENV="$APP_ENV" WP_URL="$WP_URL" WP_PATH="$WP_PATH" \
        RADMAN_REPO_ROOT="$RADMAN_REPO_ROOT" RADMAN_PRIVATE_DIR="$RADMAN_PRIVATE_DIR" \
            bash "$RADMAN_REPO_ROOT/$STATIC_RUNNER_RELPATH" --check
    elif [[ "$sub_mode" == "apply" ]]; then
        APP_ENV="$APP_ENV" WP_URL="$WP_URL" WP_PATH="$WP_PATH" \
        RADMAN_REPO_ROOT="$RADMAN_REPO_ROOT" RADMAN_PRIVATE_DIR="$RADMAN_PRIVATE_DIR" \
        CONFIRM_STAGING_APPLY=YES \
            bash "$RADMAN_REPO_ROOT/$STATIC_RUNNER_RELPATH" --apply-staging
    fi
    log "<<<<<<<<<< Phase 1 complete (${sub_mode})"
}

# -----------------------------------------------------------------------------
# Phase 2 — Homepage foundation (page ID 18)
# -----------------------------------------------------------------------------
HOMEPAGE_TEMPLATE="$RADMAN_REPO_ROOT/$HOMEPAGE_TEMPLATE_RELPATH"
HOMEPAGE_BACKUP_PATH="${BACKUP_DIR:-__PLAN__}/home-page-${HOMEPAGE_ID}-${TS}.html"

apply_homepage() {
    log ">>>>>>>>>> Phase 2: Homepage foundation (page ID ${HOMEPAGE_ID})"
    local current_title current_status
    current_title="$(wp post get "$HOMEPAGE_ID" --field=post_title --format=trim 2>/dev/null || echo __MISSING__)"
    current_status="$(wp post get "$HOMEPAGE_ID" --field=post_status --format=trim 2>/dev/null || echo __MISSING__)"
    log "Current page ${HOMEPAGE_ID}: title='${current_title}' status='${current_status}'"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[PLAN/CHECK] Would back up current page ${HOMEPAGE_ID} post_content → ${HOMEPAGE_BACKUP_PATH}"
        log "[PLAN/CHECK] Would update page ${HOMEPAGE_ID} post_content from template (${HOMEPAGE_TEMPLATE})"
        log "[PLAN/CHECK] Would set post_title='خانه' post_status (keeps current, target=publish on staging)"
        log "[PLAN/CHECK] Would enforce show_on_front=page page_on_front=${HOMEPAGE_ID}"
    else
        # Back up current content
        wp post get "$HOMEPAGE_ID" --field=post_content > "$HOMEPAGE_BACKUP_PATH"
        chmod 600 "$HOMEPAGE_BACKUP_PATH"
        log "[APPLY] Current homepage content backed up → ${HOMEPAGE_BACKUP_PATH}"

        # Apply new content from template; keep ID and status. We publish on
        # staging (the homepage is the public shell) but the site remains
        # noindex via blog_public=0.
        wp post update "$HOMEPAGE_ID" \
            --post_title="خانه" \
            --post_name="home" \
            --post_status=publish \
            --post_content="$(cat "$HOMEPAGE_TEMPLATE")" >/dev/null
        log "[APPLY] Page ${HOMEPAGE_ID} updated with Gutenberg template."

        wp option update show_on_front page >/dev/null
        wp option update page_on_front "$HOMEPAGE_ID" >/dev/null
        log "[APPLY] show_on_front=page page_on_front=${HOMEPAGE_ID} enforced."
    fi

    # Verify
    if [[ "$MODE" == "apply" ]]; then
        local new_content
        new_content="$(wp post get "$HOMEPAGE_ID" --field=post_content 2>/dev/null || true)"
        if [[ "$new_content" != *"نقره ۹۲۵؛ اصالت در جزئیات"* ]]; then
            die "Homepage hero title not present after update — aborting."
        fi
        log "[APPLY] Hero H1 verified in rendered homepage content."
    fi
    log "<<<<<<<<<< Phase 2 complete"
}

# -----------------------------------------------------------------------------
# Phase 3 — Product categories (idempotent)
# -----------------------------------------------------------------------------
find_product_cat_id() {
    local slug="$1"
    wp_available || { echo ""; return 0; }
    wp term list product_cat --slug="$slug" --fields=term_id --format=ids 2>/dev/null \
        | tr -d '[:space:]' | head -c 20 || true
}

apply_categories() {
    log ">>>>>>>>>> Phase 3: Product categories"
    printf '  %-14s %-20s %-10s %s\n' "SLUG" "NAME" "ACTION" "ID"
    local created=0 existing=0
    local spec slug name parent cid action
    for spec in "${CATEGORY_SPECS[@]}"; do
        slug="${spec%%|*}"
        rest="${spec#*|}"
        name="${rest%%|*}"
        parent="${rest##*|}"
        cid="$(find_product_cat_id "$slug")"
        if [[ -n "$cid" ]]; then
            action="EXISTING"
            existing=$((existing+1))
            if [[ "$DRY_RUN" -eq 0 ]]; then
                # Idempotent name update (safe)
                wp term update product_cat "$cid" --name="$name" >/dev/null 2>&1 || true
            fi
        else
            action="CREATE"
            if [[ "$DRY_RUN" -eq 0 ]]; then
                cid="$(wp term create product_cat "$name" --slug="$slug" --porcelain 2>/dev/null || echo __FAIL__)"
                [[ "$cid" != "__FAIL__" ]] || die "Failed to create category slug=${slug}"
            fi
            created=$((created+1))
        fi
        printf '  %-14s %-20s %-10s %s\n' "$slug" "$name" "$action" "${cid:-__will_create__}"
    done
    log "Categories: created=${created} existing=${existing} (DRY_RUN=${DRY_RUN})"
    log "<<<<<<<<<< Phase 3 complete"
}

# -----------------------------------------------------------------------------
# Phase 4 — Primary navigation menu (idempotent; no Draft pages)
# -----------------------------------------------------------------------------
find_menu_id() {
    # Returns empty string in local/plan mode when wp is unavailable.
    wp_available || { echo ""; return 0; }
    wp menu list --fields=term_id,name --format=csv 2>/dev/null \
        | awk -F',' -v name="$MENU_NAME" '$2 == name {print $1; exit}' || true
}

menu_item_exists() {
    # Returns the db-id of an existing menu item that matches (menu-id, object-type, object-id-or-url)
    # Uses a temp file (jailshell-safe; no process substitution <()).
    local menu_id="$1" otype="$2" oid="$3" ourl="${4:-}"
    wp_available || return 1
    local tmp_csv
    tmp_csv="$(mktemp "${TMPDIR:-/tmp}/radman-menu-items.XXXXXX")"
    wp menu item list "$menu_id" \
        --fields=db_id,title,object,object_id,url --format=csv 2>/dev/null \
        | sed '1d' > "$tmp_csv" || true
    local line mid mtitle mtype moid murl
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        IFS=',' read -r mid mtitle mtype moid murl <<<"$line"
        if [[ "$otype" == "custom" ]]; then
            if [[ "$mtype" == "custom" && "$murl" == "$ourl" ]]; then
                rm -f "$tmp_csv"
                echo "$mid"
                return 0
            fi
        else
            if [[ "$mtype" == "$otype" && "$moid" == "$oid" ]]; then
                rm -f "$tmp_csv"
                echo "$mid"
                return 0
            fi
        fi
    done < "$tmp_csv"
    rm -f "$tmp_csv"
    return 1
}

detect_primary_menu_location() {
    # Heuristic: prefer a location whose slug/description contains "primary"
    # or "header" or "main". Returns empty if ambiguous OR if wp unavailable.
    wp_available || { echo ""; return 0; }
    local loc
    loc="$(wp menu location list --format=csv 2>/dev/null \
        | awk -F',' 'NR>1 && (tolower($1) ~ /primary|main|header|top/) {print $1; exit}' || true)"
    echo "$loc"
}

apply_menu() {
    log ">>>>>>>>>> Phase 4: Primary navigation menu"
    local menu_id
    menu_id="$(find_menu_id)"
    if [[ -z "$menu_id" ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
            log "[PLAN/CHECK] Would CREATE menu '${MENU_NAME}'."
            menu_id="__will_create__"
        else
            menu_id="$(wp menu create "$MENU_NAME" --porcelain 2>/dev/null || echo __FAIL__)"
            [[ "$menu_id" != "__FAIL__" ]] || die "Failed to create menu '${MENU_NAME}'."
            log "[APPLY] Menu '${MENU_NAME}' created (term_id=${menu_id})."
        fi
    else
        log "Menu '${MENU_NAME}' already exists (term_id=${menu_id}) — reconciling items."
    fi

    # Process approved items
    local label otype oid ourl
    local added=0 updated=0 skipped=0
    for spec in "${MENU_ITEMS[@]}"; do
        label="${spec%%|*}"
        rest="${spec#*|}"
        otype="${rest%%|*}"
        oid_or_url="${rest##*|}"
        ourl=""
        if [[ "$otype" == "custom" ]]; then
            ourl="$oid_or_url"
            oid=""
        else
            oid="$oid_or_url"
        fi

        if [[ "$DRY_RUN" -eq 1 ]]; then
            printf '  [PLAN/CHECK] Menu item: %-18s -> %s (%s=%s)\n' "$label" "$otype" "$([[ "$otype" == custom ]] && echo url || echo id)" "$oid_or_url"
            skipped=$((skipped+1))
            continue
        fi

        # Safety: if target is a page, verify it's NOT Draft before linking
        if [[ "$otype" == "page" ]]; then
            local pstatus
            pstatus="$(wp post get "$oid" --field=post_status --format=trim 2>/dev/null || echo __MISSING__)"
            if [[ "$pstatus" == "draft" || "$pstatus" == "__MISSING__" ]]; then
                warn "Skipping menu item '${label}' → page ID ${oid} (status=${pstatus}); Draft pages are never linked."
                continue
            fi
        fi

        local existing_mid=""
        existing_mid="$(menu_item_exists "$menu_id" "$otype" "$oid" "$ourl")"
        if [[ -n "$existing_mid" ]]; then
            # Idempotent: ensure title matches
            wp menu item update "$menu_id" "$existing_mid" --title="$label" >/dev/null 2>&1 || true
            updated=$((updated+1))
        else
            if [[ "$otype" == "page" ]]; then
                wp menu item add-post "$menu_id" "$oid" --title="$label" >/dev/null
            elif [[ "$otype" == "tax" ]]; then
                wp menu item add-term "$menu_id" product_cat "$oid" --title="$label" >/dev/null
            else
                wp menu item add-custom "$menu_id" "$ourl" "$label" >/dev/null
            fi
            added=$((added+1))
        fi
    done
    if [[ "$DRY_RUN" -eq 0 ]]; then
        log "Menu items: added=${added} reconciled=${updated}"
    fi

    # Detect and assign primary location (if unambiguous)
    local location
    location="$(detect_primary_menu_location)"
    if [[ -n "$location" && "$menu_id" != "__will_create__" ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
            log "[PLAN/CHECK] Would assign menu '${MENU_NAME}' to detected location: ${location}"
        else
            wp menu location assign "$menu_id" "$location" >/dev/null 2>&1 || true
            log "[APPLY] Menu assigned to location: ${location}"
        fi
    else
        if [[ "$DRY_RUN" -eq 0 ]]; then
            warn "Could not auto-detect an unambiguous primary menu location."
            warn "Menu '${MENU_NAME}' was created/updated; assign it manually via Customize → Menus."
        else
            log "[PLAN/CHECK] Menu-location assignment may be PENDING OWNER UI SELECTION if location detection is ambiguous on host."
        fi
    fi
    log "<<<<<<<<<< Phase 4 complete"
}

# -----------------------------------------------------------------------------
# Phase 5 — WooCommerce baseline verification (read-only, no mutation)
# -----------------------------------------------------------------------------
verify_woocommerce_baseline() {
    log ">>>>>>>>>> Phase 5: WooCommerce baseline (read-only)"
    if [[ "$MODE" == "plan" ]]; then
        log "[PLAN] Would verify the following on host (no mutation):"
        printf '  %-30s %s\n' "woocommerce_currency"         "(expected IRT)"
        printf '  %-30s %s\n' "woocommerce_price_num_decimals" "(expected 0)"
        printf '  %-30s %s\n' "woocommerce_shop_page_id"     "(expected ${SHOP_PAGE_ID})"
        printf '  %-30s %s\n' "woocommerce_cart_page_id"     "(expected ${CART_PAGE_ID})"
        printf '  %-30s %s\n' "woocommerce_checkout_page_id" "(expected ${CHECKOUT_PAGE_ID})"
        printf '  %-30s %s\n' "woocommerce_myaccount_page_id" "(expected ${MYACCOUNT_PAGE_ID})"
        log "[PLAN] Shipping zones/methods: READ-ONLY report (no shipping method auto-enabled)."
        log "[PLAN] Payment gateways: READ-ONLY report (Gateland remains installed-only; nothing enabled)."
        log "[PLAN] Currency Gate B remains PENDING (checkout/order/email/schema/callback)."
    else
        local shop_id cart_id checkout_id myacct_id
        shop_id="$(wp_opt woocommerce_shop_page_id)"
        cart_id="$(wp_opt woocommerce_cart_page_id)"
        checkout_id="$(wp_opt woocommerce_checkout_page_id)"
        myacct_id="$(wp_opt woocommerce_myaccount_page_id)"
        printf '  %-32s %s\n' "woocommerce_currency"         "${CURRENCY}"
        printf '  %-32s %s\n' "woocommerce_price_num_decimals" "${DECIMALS}"
        printf '  %-32s %s\n' "woocommerce_shop_page_id"     "${shop_id} (expected ${SHOP_PAGE_ID})"
        printf '  %-32s %s\n' "woocommerce_cart_page_id"     "${cart_id} (expected ${CART_PAGE_ID})"
        printf '  %-32s %s\n' "woocommerce_checkout_page_id" "${checkout_id} (expected ${CHECKOUT_PAGE_ID})"
        printf '  %-32s %s\n' "woocommerce_myaccount_page_id" "${myacct_id} (expected ${MYACCOUNT_PAGE_ID})"

        # Currency/decimals: report but do NOT silently change
        if [[ "$CURRENCY" != "IRT" ]]; then
            warn "woocommerce_currency is '${CURRENCY}' (expected IRT). Reviewer must resolve; NOT auto-changed."
        fi
        if [[ "$DECIMALS" != "0" ]]; then
            warn "woocommerce_price_num_decimals is '${DECIMALS}' (expected 0). Reviewer must resolve; NOT auto-changed."
        fi

        log "--- Shipping (read-only) ---"
        wp wc shipping zone list --user=1 2>/dev/null \
            | while IFS= read -r line; do log "  $line"; done \
            || warn "Could not list shipping zones (WooCommerce may not be fully installed yet)."
        log "[INFO] Shipping configuration is NOT auto-enabled; PENDING owner decision."

        log "--- Payment gateways (read-only) ---"
        if wp option get woocommerce_gateland_settings >/dev/null 2>&1; then
            local g_enabled
            g_enabled="$(wp option get woocommerce_gateland_settings --format=json 2>/dev/null | $PYTHON_BIN -c 'import sys,json; d=json.load(sys.stdin); print(d.get("enabled","__unknown__"))' 2>/dev/null || echo __readerr__)"
            log "  Gateland settings: enabled=${g_enabled} (expected NOT enabled)."
        else
            log "  Gateland settings option not present (plugin inactive or not yet configured)."
        fi
        log "[INFO] No payment gateway is enabled or configured by this script. Currency Gate B remains PENDING."
    fi
    log "<<<<<<<<<< Phase 5 complete"
}

# -----------------------------------------------------------------------------
# Phase 6 — LiteSpeed read-only status
# -----------------------------------------------------------------------------
verify_litespeed_status() {
    log ">>>>>>>>>> Phase 6: LiteSpeed Cache status (read-only)"
    if [[ "$MODE" == "plan" ]]; then
        log "[PLAN] Would report LiteSpeed plugin + cache status (no tuning applied)."
        log "[PLAN] CSS/JS combine, delayed JS, unused CSS, Guest Mode/Opti, QUIC.cloud, Redis — NOT touched."
    else
        local lscache_active="no"
        if wp plugin is-active litespeed-cache 2>/dev/null; then
            lscache_active="yes"
        fi
        log "  LiteSpeed Cache plugin active: ${lscache_active}"
        if [[ "$lscache_active" == "yes" ]]; then
            # Attempt to read a couple of key options without modifying
            local page_cache guest_opt css_combine js_combine
            page_cache="$(wp eval 'echo get_option("litespeed.conf.cache-page", "__missing__");' 2>/dev/null || echo __readerr__)"
            guest_opt="$(wp eval 'echo get_option("litespeed.conf.cache-guest", "__missing__");' 2>/dev/null || echo __readerr__)"
            css_combine="$(wp eval 'echo get_option("litespeed.conf.optm-css-combine", "__missing__");' 2>/dev/null || echo __readerr__)"
            js_combine="$(wp eval 'echo get_option("litespeed.conf.optm-js-combine", "__missing__");' 2>/dev/null || echo __readerr__)"
            log "  page-cache enabled:   ${page_cache}"
            log "  guest-mode:           ${guest_opt}"
            log "  css-combine:          ${css_combine}"
            log "  js-combine:           ${js_combine}"
        fi
        log "[INFO] No LiteSpeed optimization tuning is applied in this mission (dedicated tuning mission later)."
    fi
    log "<<<<<<<<<< Phase 6 complete"
}

# -----------------------------------------------------------------------------
# Backup creation (apply mode only; before any mutation)
# -----------------------------------------------------------------------------
create_backups() {
    log ">>>>>>>>>> Phase 0: Backups (pre-mutation)"
    TS_LONG="$(date +%Y%m%d-%H%M%S)"
    DB_BACKUP="${BACKUP_DIR}/pre-storefront-${TS_LONG}.sql"
    wp db export "$DB_BACKUP" >/dev/null
    chmod 600 "$DB_BACKUP"
    log "[APPLY] DB backup → ${DB_BACKUP}"

    THEME_TARGET="${WP_PATH}/wp-content/themes/blocksy-child"
    THEME_BACKUP="__none__"
    if [[ -d "$THEME_TARGET" ]]; then
        THEME_BACKUP="${BACKUP_DIR}/blocksy-child-pre-storefront-${TS_LONG}.tar.gz"
        tar -C "$(dirname "$THEME_TARGET")" -czf "$THEME_BACKUP" "$(basename "$THEME_TARGET")"
        chmod 600 "$THEME_BACKUP"
        log "[APPLY] Child-theme backup → ${THEME_BACKUP}"
    fi
    log "<<<<<<<<<< Phase 0 complete"
}

# -----------------------------------------------------------------------------
# Final static-page draft verification (post-apply)
# -----------------------------------------------------------------------------
verify_static_pages_draft() {
    log ">>>>>>>>>> Phase 7: Static pages draft verification"
    local slug pid status
    local bad=0
    for slug in "${STATIC_SLUGS[@]}"; do
        if [[ "$MODE" == "plan" ]]; then
            printf '  [PLAN] %-28s status=draft (enforced by sub-runner)\n' "$slug"
        else
            pid="$(wp post list --post_type=page --post_name__in="$slug" --fields=ID --format=ids --allow-root 2>/dev/null | tr -d '[:space:]' | head -c 20 || true)"
            if [[ -z "$pid" ]]; then
                warn "Slug '${slug}' not found after apply — will be CREATED as draft on next run."
                bad=$((bad+1))
                continue
            fi
            status="$(wp post get "$pid" --field=post_status --format=trim 2>/dev/null || echo unknown)"
            printf '  %-28s ID=%-8s status=%s\n' "$slug" "$pid" "$status"
            if [[ "$status" != "draft" ]]; then
                err "Static page '${slug}' (ID ${pid}) has status '${status}' — expected 'draft'."
                bad=$((bad+1))
            fi
        fi
    done
    if [[ $bad -gt 0 && "$DRY_RUN" -eq 0 ]]; then
        die "One or more static pages are NOT in draft status after apply."
    fi
    log "<<<<<<<<<< Phase 7 complete"
}

# -----------------------------------------------------------------------------
# Plan output for items that the sub-runner also touches (summarized)
# -----------------------------------------------------------------------------
log ""
log "========= STOREFRONT BATCH PLAN (mode=${MODE}) ========="
log ""

# Phase 1: call sub-runner in the matching mode (PLAN/CHECK/APPLY)
if [[ "$MODE" == "plan" ]]; then
    # In pure plan mode without WP_PATH we cannot invoke --check against host;
    # call the sub-runner's plan mode (which renders locally and shows plan).
    if [[ -z "$WP_PATH" ]]; then
        log "[PLAN] (WP_PATH not set — running sub-runner in local plan mode; no host access.)"
        RADMAN_REPO_ROOT="$RADMAN_REPO_ROOT" \
            bash "$RADMAN_REPO_ROOT/$STATIC_RUNNER_RELPATH" --plan
    else
        run_static_runner_subplan "plan"
    fi
elif [[ "$MODE" == "check" ]]; then
    run_static_runner_subplan "check"
elif [[ "$MODE" == "apply" ]]; then
    create_backups
    run_static_runner_subplan "apply"
fi

log ""
# Homepage plan
log "--- Homepage ---"
if [[ "$MODE" == "plan" ]]; then
    log "  Target:   page ID ${HOMEPAGE_ID} (slug=home)"
    log "  Template: ${HOMEPAGE_TEMPLATE}"
    log "  Backup:   ${HOMEPAGE_BACKUP_PATH}"
    log "  Action:   UPDATE page ${HOMEPAGE_ID} post_content from Gutenberg template"
    log "  Enforce:  show_on_front=page, page_on_front=${HOMEPAGE_ID}"
    log "  Status:   keep published on staging (site remains noindex via blog_public=0)"
else
    apply_homepage
fi

# Categories
log ""
apply_categories

# Menu
log ""
apply_menu

# WooCommerce baseline
log ""
verify_woocommerce_baseline

# LiteSpeed
log ""
verify_litespeed_status

# Static pages draft check
log ""
verify_static_pages_draft

# -----------------------------------------------------------------------------
# Prohibited items summary (always printed)
# -----------------------------------------------------------------------------
log ""
log "========= PROHIBITED ITEMS (REMAIN UNTOUCHED) ========="
log "  ✓ Production (public_html) — NEVER touched"
log "  ✓ Payment gateways — NOT enabled (Gateland installed-only)"
log "  ✓ SMS (Kavenegar) — NOT enabled"
log "  ✓ Telegram bot / agents — NOT deployed"
log "  ✓ Redis object cache — NOT enabled"
log "  ✓ SEO indexing (blog_public) — remains 0 (noindex)"
log "  ✓ Analytics / tracking pixels — NOT added"
log "  ✓ All 11 static pages — remain DRAFT"
log "  ✓ Products, orders, users — NOT modified"
log "  ✓ LiteSpeed aggressive optimizations (CSS/JS combine, delayed JS, UCSS, Guest Opti, QUIC.cloud) — NOT touched"
log ""

if [[ "$MODE" != "apply" ]]; then
    log "Dry-run (--${MODE}) complete. No WordPress content was modified."
    log "Run with --apply-staging and CONFIRM_STAGING_APPLY=YES after reviewer approval."
    exit 0
fi

log "========================================================================"
log "STOREFRONT FOUNDATION APPLIED TO STAGING (${WP_URL})"
log "  Active theme : ${ACTIVE_THEME}"
log "  DB backup    : ${DB_BACKUP}"
log "  Theme backup : ${THEME_BACKUP}"
log "  Homepage     : page ID ${HOMEPAGE_ID} updated (hero H1 verified)"
log "  Menu         : '${MENU_NAME}' reconciled"
log "  Categories   : rings, necklaces, bracelets ensured (idempotent)"
log "  Static pages: all 11 remain DRAFT"
log "PRODUCTION (public_html) WAS NOT TOUCHED."
log "Payments / SMS / Redis / analytics / indexing WERE NOT ENABLED."
log "========================================================================"
