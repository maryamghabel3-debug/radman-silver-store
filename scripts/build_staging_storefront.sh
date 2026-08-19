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
PY_VER=""
for cand in "$HOME/bin/python3" /opt/alt/python311/bin/python3.11 python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
        candidate_ver="$("$cand" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
        candidate_major="${candidate_ver%%.*}"
        candidate_minor="${candidate_ver##*.}"
        if [[ "$candidate_major" =~ ^[0-9]+$ && "$candidate_minor" =~ ^[0-9]+$ \
              && "$candidate_major" -eq 3 && "$candidate_minor" -ge 11 ]]; then
            PYTHON_BIN="$cand"
            PY_VER="$candidate_ver"
            break
        fi
    fi
done
[[ -n "$PYTHON_BIN" ]] \
    || die "Python >= 3.11 required. Expected ~/bin/python3 or /opt/alt/python311/bin/python3.11."
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

# `command -v wp` sees the wrapper function itself; type -P checks the binary.
wp_available() { type -P wp >/dev/null 2>&1; }

readonly WP_CAPTURE_LIB="$RADMAN_REPO_ROOT/scripts/lib/wp_cli_capture.sh"
[[ -f "$WP_CAPTURE_LIB" ]] || die "WP capture helper missing: ${WP_CAPTURE_LIB}"
# shellcheck source=scripts/lib/wp_cli_capture.sh
source "$WP_CAPTURE_LIB"

# -----------------------------------------------------------------------------
# Private dir / lock / backup locations
# -----------------------------------------------------------------------------
LOCK_FD=""
BACKUP_DIR=""
LOCKFILE=""
if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    mkdir -p "$RADMAN_PRIVATE_DIR"
    chmod 700 "$RADMAN_PRIVATE_DIR"
    # NOTE: do NOT use 'local' here — this block runs at top-level script scope
    # (outside any function). 'local' is only valid inside bash functions and
    # cPanel/CloudLinux jailshell aborts with: "local: can only be used in a function".
    locks_dir="$RADMAN_PRIVATE_DIR/locks"
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
# Guard verification (host-facing modes)
# -----------------------------------------------------------------------------
BLOG_PUBLIC="__PLAN__"
ACTIVE_THEME="__PLAN__"
THEME_DETECTION_SOURCE="__PLAN__"
CURRENCY="__PLAN__"
DECIMALS="__PLAN__"
SHOW_ON_FRONT="__PLAN__"
PAGE_ON_FRONT="__PLAN__"
HOME_URL="__PLAN__"
SITE_URL="__PLAN__"

if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    log "Verifying staging identity..."
    wp_read_option BLOG_PUBLIC blog_public \
        || die "Could not read blog_public after option-get and wp-eval fallbacks."
    [[ "$BLOG_PUBLIC" == "$EXPECTED_BLOG_PUBLIC" ]] \
        || die "blog_public is '${BLOG_PUBLIC}' (expected '${EXPECTED_BLOG_PUBLIC}'). Staging must remain noindex."

    wp_read_option HOME_URL home \
        || die "Could not read WordPress home option after all fallbacks."
    wp_read_option SITE_URL siteurl \
        || die "Could not read WordPress siteurl option after all fallbacks."
    [[ "$HOME_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WordPress home option is '${HOME_URL}' (expected '${EXPECTED_WP_URL}')."
    [[ "$SITE_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WordPress siteurl option is '${SITE_URL}' (expected '${EXPECTED_WP_URL}')."

    THEME_DETECTION_SOURCE="none"
    wp_detect_active_theme ACTIVE_THEME THEME_DETECTION_SOURCE || true
    if [[ "$THEME_DETECTION_SOURCE" == "directory" ]]; then
        warn "WP-CLI theme reads were empty; blocksy-child directory exists, accepting directory fallback."
    fi
    if [[ "$ACTIVE_THEME" != "blocksy-child" && "$ACTIVE_THEME" != "blocksy" ]]; then
        die "Active theme '${ACTIVE_THEME}' is not Blocksy-compatible. Refusing to proceed."
    fi

    wp_read_option CURRENCY woocommerce_currency || CURRENCY="__MISSING__"
    wp_read_option DECIMALS woocommerce_price_num_decimals || DECIMALS="__MISSING__"
    wp_read_option SHOW_ON_FRONT show_on_front || SHOW_ON_FRONT="__MISSING__"
    wp_read_option PAGE_ON_FRONT page_on_front || PAGE_ON_FRONT="__MISSING__"

    # Verify page 18 exists without the invalid `post get --format=ids` form.
    homepage_exists_id=""
    wp_post_exists homepage_exists_id "$HOMEPAGE_ID" \
        || die "Homepage ID ${HOMEPAGE_ID} does not exist. Refusing to create a new homepage outside of plan."
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
    printf '  %-32s %s\n' "Theme detection source" "$THEME_DETECTION_SOURCE"
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
    current_title="__MISSING__"
    current_status="__MISSING__"
    wp_read_post_field current_title "$HOMEPAGE_ID" post_title || true
    wp_read_post_field current_status "$HOMEPAGE_ID" post_status || true
    log "Current page ${HOMEPAGE_ID}: title='${current_title}' status='${current_status}'"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[PLAN/CHECK] Would back up current page ${HOMEPAGE_ID} post_content → ${HOMEPAGE_BACKUP_PATH}"
        log "[PLAN/CHECK] Would update page ${HOMEPAGE_ID} post_content from template (${HOMEPAGE_TEMPLATE})"
        log "[PLAN/CHECK] Would set post_title='خانه' post_status (keeps current, target=publish on staging)"
        log "[PLAN/CHECK] Would enforce show_on_front=page page_on_front=${HOMEPAGE_ID}"
    else
        # Back up current content through the same robust read chain.
        local backup_content=""
        wp_read_post_field backup_content "$HOMEPAGE_ID" post_content \
            || die "Could not read homepage content for the mandatory backup."
        printf '%s' "$backup_content" > "$HOMEPAGE_BACKUP_PATH"
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
        new_content=""
        wp_read_post_field new_content "$HOMEPAGE_ID" post_content || true
        if [[ "$new_content" != *"نقره ۹۲۵؛"*"اصالت در جزئیات"* ]]; then
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
    local out_var="$1"
    local slug="$2"
    if ! wp_available; then
        printf -v "$out_var" '%s' ''
        return 0
    fi
    wp_find_term_id_by_slug "$out_var" product_cat "$slug" || true
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
        cid=""
        find_product_cat_id cid "$slug"
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
                cid=""
                wp_capture_to_var cid term create product_cat "$name" --slug="$slug" --porcelain \
                    || die "Failed to create category slug=${slug}"
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
    # Sets OUT_VAR to an existing menu term_id or empty.
    local out_var="$1"
    local menu_csv="" found_menu_id="" name_b64 php_code
    if ! wp_available; then
        printf -v "$out_var" '%s' ''
        return 0
    fi
    if wp_capture_to_var menu_csv menu list --fields=term_id,name --format=csv; then
        found_menu_id="$(printf '%s\n' "$menu_csv" | awk -F',' -v name="$MENU_NAME" '$2 == name {print $1; exit}')"
        if [[ -n "$found_menu_id" ]]; then
            printf -v "$out_var" '%s' "$found_menu_id"
            return 0
        fi
    fi

    # An empty/mangled CSV lookup must be independently verified before a new
    # menu is created, otherwise an idempotent run could create duplicates.
    name_b64="$(printf '%s' "$MENU_NAME" | base64 | tr -d '\n')"
    php_code="\$m=wp_get_nav_menu_object(base64_decode('${name_b64}')); if (\$m) { echo (string) \$m->term_id; }"
    wp_capture_to_var found_menu_id eval "$php_code" || true
    [[ -n "$found_menu_id" ]] && warn "Menu lookup recovered via wp eval fallback."
    printf -v "$out_var" '%s' "$found_menu_id"
}

menu_item_exists() {
    # Sets OUT_VAR to the db-id of a matching menu item. Uses wp eval as an
    # independent fallback, preventing duplicate items when CSV capture is
    # empty/mangled on jailshell.
    local out_var="$1" menu_id="$2" otype="$3" oid="$4" ourl="${5:-}"
    local menu_csv="" line mid mtitle mobject moid murl expected_object
    local url_b64 php_code found=""
    printf -v "$out_var" '%s' ''
    wp_available || return 1

    expected_object="$otype"
    [[ "$otype" == "tax" ]] && expected_object="product_cat"
    if wp_capture_to_var menu_csv menu item list "$menu_id" \
        --fields=db_id,title,object,object_id,url --format=csv; then
        while IFS= read -r line; do
            [[ -z "$line" || "$line" == db_id,* ]] && continue
            IFS=',' read -r mid mtitle mobject moid murl <<<"$line"
            if [[ "$otype" == "custom" ]]; then
                if [[ "$mobject" == "custom" && "$murl" == "$ourl" ]]; then
                    printf -v "$out_var" '%s' "$mid"
                    return 0
                fi
            elif [[ "$mobject" == "$expected_object" && "$moid" == "$oid" ]]; then
                printf -v "$out_var" '%s' "$mid"
                return 0
            fi
        done <<<"$menu_csv"
    fi

    url_b64="$(printf '%s' "$ourl" | base64 | tr -d '\n')"
    php_code="\$items=wp_get_nav_menu_items(${menu_id}); foreach ((array) \$items as \$i) { if ('${otype}' === 'custom') { if ('custom' === \$i->object && \$i->url === base64_decode('${url_b64}')) { echo (string) \$i->db_id; break; } } elseif (\$i->object === '${expected_object}' && (string) \$i->object_id === '${oid}') { echo (string) \$i->db_id; break; } }"
    if wp_capture_to_var found eval "$php_code"; then
        warn "Menu-item lookup recovered via wp eval fallback."
        printf -v "$out_var" '%s' "$found"
        return 0
    fi
    return 1
}

detect_primary_menu_location() {
    # Sets OUT_VAR. Prefer known Blocksy locations first, then a conservative
    # primary/main/header/top heuristic. Falls back to registered nav menus.
    local out_var="$1"
    local locations_csv="" loc="" php_code
    printf -v "$out_var" '%s' ''
    wp_available || return 0
    if wp_capture_to_var locations_csv menu location list --format=csv; then
        loc="$(printf '%s\n' "$locations_csv" | awk -F',' 'NR>1 && ($1 == "menu_1" || $1 == "menu_mobile") {print $1; exit}')"
        if [[ -z "$loc" ]]; then
            loc="$(printf '%s\n' "$locations_csv" | awk -F',' 'NR>1 && (tolower($1) ~ /primary|main|header|top/) {print $1; exit}')"
        fi
    fi
    if [[ -z "$loc" ]]; then
        php_code="foreach ((array) get_registered_nav_menus() as \$slug => \$desc) { if (in_array(\$slug, array('menu_1','menu_mobile'), true) || preg_match('/primary|main|header|top/i', \$slug)) { echo \$slug; break; } }"
        wp_capture_to_var loc eval "$php_code" || true
        [[ -n "$loc" ]] && warn "Menu-location detection recovered via wp eval fallback."
    fi
    printf -v "$out_var" '%s' "$loc"
}

apply_menu() {
    log ">>>>>>>>>> Phase 4: Primary navigation menu"
    local menu_id
    menu_id=""
    find_menu_id menu_id
    if [[ -z "$menu_id" ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
            log "[PLAN/CHECK] Would CREATE menu '${MENU_NAME}'."
            menu_id="__will_create__"
        else
            menu_id=""
            wp_capture_to_var menu_id menu create "$MENU_NAME" --porcelain \
                || die "Failed to create menu '${MENU_NAME}'."
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

        # Resolve taxonomy slug to its numeric term_id before matching/adding.
        # `wp menu item add-term` expects an ID, not the approved slug string.
        if [[ "$otype" == "tax" ]]; then
            local tax_term_id=""
            find_product_cat_id tax_term_id "$oid"
            if [[ -z "$tax_term_id" ]]; then
                warn "Skipping menu item '${label}' — product category slug '${oid}' was not found."
                continue
            fi
            oid="$tax_term_id"
        fi

        # Safety: if target is a page, verify it's NOT Draft before linking
        if [[ "$otype" == "page" ]]; then
            local pstatus
            pstatus="__MISSING__"
            wp_read_post_field pstatus "$oid" post_status || true
            if [[ "$pstatus" == "draft" || "$pstatus" == "__MISSING__" || -z "$pstatus" ]]; then
                warn "Skipping menu item '${label}' → page ID ${oid} (status=${pstatus}); Draft pages are never linked."
                continue
            fi
        fi

        local existing_mid=""
        menu_item_exists existing_mid "$menu_id" "$otype" "$oid" "$ourl" || true
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
    location=""
    detect_primary_menu_location location
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
        shop_id="__MISSING__"
        cart_id="__MISSING__"
        checkout_id="__MISSING__"
        myacct_id="__MISSING__"
        wp_read_option shop_id woocommerce_shop_page_id || true
        wp_read_option cart_id woocommerce_cart_page_id || true
        wp_read_option checkout_id woocommerce_checkout_page_id || true
        wp_read_option myacct_id woocommerce_myaccount_page_id || true
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
        local shipping_report=""
        if wp_capture_to_var shipping_report wc shipping zone list --user=1; then
            while IFS= read -r line; do log "  $line"; done <<<"$shipping_report"
        else
            warn "Could not list shipping zones after retry (WooCommerce may not be fully installed yet)."
        fi
        log "[INFO] Shipping configuration is NOT auto-enabled; PENDING owner decision."

        log "--- Payment gateways (read-only) ---"
        local gateland_json="" g_enabled="__unknown__"
        if wp_read_option_json gateland_json woocommerce_gateland_settings; then
            g_enabled="$("$PYTHON_BIN" -c 'import sys,json; d=json.load(sys.stdin); print(d.get("enabled","__unknown__") if isinstance(d,dict) else "__unknown__")' <<<"$gateland_json" 2>/dev/null || true)"
            [[ -n "$g_enabled" ]] || g_enabled="__readerr__"
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
        if wp plugin is-active litespeed-cache >/dev/null; then
            lscache_active="yes"
        fi
        log "  LiteSpeed Cache plugin active: ${lscache_active}"
        if [[ "$lscache_active" == "yes" ]]; then
            # Attempt to read a couple of key options without modifying
            local page_cache="__readerr__" guest_opt="__readerr__" css_combine="__readerr__" js_combine="__readerr__"
            wp_capture_to_var page_cache eval 'echo get_option("litespeed.conf.cache-page", "__missing__");' || true
            wp_capture_to_var guest_opt eval 'echo get_option("litespeed.conf.cache-guest", "__missing__");' || true
            wp_capture_to_var css_combine eval 'echo get_option("litespeed.conf.optm-css-combine", "__missing__");' || true
            wp_capture_to_var js_combine eval 'echo get_option("litespeed.conf.optm-js-combine", "__missing__");' || true
            page_cache="${page_cache:-__readerr__}"
            guest_opt="${guest_opt:-__readerr__}"
            css_combine="${css_combine:-__readerr__}"
            js_combine="${js_combine:-__readerr__}"
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
            pid=""
            wp_find_post_id_by_slug pid page "$slug" || true
            if [[ -z "$pid" ]]; then
                warn "Slug '${slug}' not found after apply — will be CREATED as draft on next run."
                bad=$((bad+1))
                continue
            fi
            status="unknown"
            wp_read_post_field status "$pid" post_status || true
            status="${status:-unknown}"
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
