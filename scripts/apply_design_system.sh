#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Professional Luxury Design System Apply Runner
# ------------------------------------------------------------------------------
# Idempotent, staging-only, plan-by-default runner that applies the PR-18
# design system to the staging storefront:
#   1. Verifies strict staging guards (APP_ENV, WP_URL, WP_PATH, active theme).
#   2. Auto-heals blog_public=0 (noindex) instead of aborting when empty.
#   3. Creates timestamped backups (DB + child theme + homepage) before any
#      mutation.
#   4. Syncs reviewed child-theme files (style.css, functions.php, assets/*):
#      local WOFF2 webfonts (Estedad + Vazirmatn), @font-face CSS, and the
#      design-system stylesheet that covers header/nav/hero/trust/cards/
#      shop/product/buttons/footer/forms/tabs/pagination/static pages.
#   5. Imports approved Persian ivory header logo (radman-logo-header-ivory.png)
#      into the WP media library and sets it as the site custom_logo, BUT ONLY
#      if no valid existing custom_logo is already configured (preserves the
#      owner-configured ivory logo on the dark/matte-black header). Same
#      idempotent-preservation rule applies to site_icon (favicon).
#   6. Updates page ID 18 (homepage) with the refined Gutenberg template.
#   7. Applies a curated set of safe theme_mod values (sticky header off,
#      dark header surface, logo max-height). Everything else is left to
#      Customizer UI (documented in DESIGN-SYSTEM-RUNBOOK.md).
#   8. Flushes object cache + LiteSpeed cache (when available) at the end.
#
# MODES:
#   --plan            (default) Read-only dry run; prints intent, touches nothing.
#   --apply-staging   Execute mutating operations (requires CONFIRM_STAGING_APPLY=YES).
#
# PRODUCTION IS PROHIBITED BY DESIGN. There is no --apply-production flag.
# Payments, SMS, Redis, analytics, SEO indexing, and LiteSpeed aggressive
# optimizations (CSS/JS combine, UCSS, Delayed JS, Guest Mode, QUIC.cloud) are
# NEVER enabled by this script. All 11 static pages remain Draft.
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
readonly LOCK_NAME="radman-design-system.lock"
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT_FALLBACK="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly HOMEPAGE_ID=18
readonly DESIGN_VERSION="1.1.0"

MODE="plan"
DRY_RUN=1

# -----------------------------------------------------------------------------
# Branding assets (relative to RADMAN_REPO_ROOT/assets/branding/)
# -----------------------------------------------------------------------------
readonly LOGO_HEADER_FILE="radman-logo-header-ivory.png"
readonly FAVICON_FILE="logo-icon-512.png"

# -----------------------------------------------------------------------------
# Child-theme source files to sync (relative to RADMAN_REPO_ROOT/theme/blocksy-child/)
# -----------------------------------------------------------------------------
readonly -a CHILD_THEME_TOP_FILES=( style.css functions.php README.md )
readonly -a CHILD_THEME_ASSETS=(
    assets/radman-fonts.css
    assets/radman-design-system.css
)
# Webfont files (WOFF2) — local only; no Google Fonts.
readonly -a CHILD_THEME_FONTS=(
    fonts/Estedad-Thin.woff2
    fonts/Estedad-Light.woff2
    fonts/Estedad-Regular.woff2
    fonts/Estedad-Medium.woff2
    fonts/Estedad-SemiBold.woff2
    fonts/Estedad-Bold.woff2
    fonts/Estedad-Black.woff2
    fonts/Vazirmatn-Thin.woff2
    fonts/Vazirmatn-Light.woff2
    fonts/Vazirmatn-Regular.woff2
    fonts/Vazirmatn-Medium.woff2
    fonts/Vazirmatn-SemiBold.woff2
    fonts/Vazirmatn-Bold.woff2
    fonts/Vazirmatn-Black.woff2
)

# -----------------------------------------------------------------------------
# Logging helpers
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
  bash scripts/apply_design_system.sh --plan            # dry run (default)
  bash scripts/apply_design_system.sh --apply-staging   # mutate staging

Required env for --apply-staging:
  export PATH="$HOME/bin:$PATH"
  APP_ENV=staging
  CONFIRM_STAGING_APPLY=YES
  WP_PATH=/home/radmansi/staging.radmansilver.ir
  WP_URL=https://staging.radmansilver.ir
  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman

Design system version: see DESIGN_VERSION constant (printed at top of log).

This script NEVER:
  - touches production/public_html
  - enables payments, SMS, Redis, analytics, or SEO indexing
  - enables LiteSpeed aggressive optimizations (UCSS, Delayed JS, Guest, QUIC.cloud)
  - publishes Draft pages
  - loads external Google Fonts
  - stores credentials
USAGE
}

# -----------------------------------------------------------------------------
# Argument parsing
# -----------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)            MODE="plan";   DRY_RUN=1; shift ;;
        --apply-staging)   MODE="apply";  DRY_RUN=0; shift ;;
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

log "===================================================================="
log "RADMAN SILVER 925 — Design System Apply Runner  v${DESIGN_VERSION}"
log "Mode: ${MODE}    (dry_run=${DRY_RUN})"
log "RADMAN_REPO_ROOT = ${RADMAN_REPO_ROOT}"
log "===================================================================="

# -----------------------------------------------------------------------------
# Required repository files
# -----------------------------------------------------------------------------
for f in \
    theme/blocksy-child/style.css \
    theme/blocksy-child/functions.php \
    theme/blocksy-child/assets/radman-fonts.css \
    theme/blocksy-child/assets/radman-design-system.css \
    assets/branding/${LOGO_HEADER_FILE} \
    assets/branding/${FAVICON_FILE} \
    templates/home-page-gutenberg.html ; do
    [[ -f "$RADMAN_REPO_ROOT/$f" ]] \
        || die "Required repo file missing: ${RADMAN_REPO_ROOT}/${f}"
done
for ff in "${CHILD_THEME_FONTS[@]}"; do
    [[ -f "$RADMAN_REPO_ROOT/theme/blocksy-child/$ff" ]] \
        || die "Required webfont missing: ${RADMAN_REPO_ROOT}/theme/blocksy-child/${ff}"
done

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
[[ -n "$PYTHON_BIN" ]] || die "Python 3 is required but no python3/python was found in PATH."

# -----------------------------------------------------------------------------
# Staging guards (only enforced in apply mode — plan mode works locally)
# -----------------------------------------------------------------------------
if [[ "$MODE" == "apply" ]]; then
    [[ -n "$WP_PATH" ]]            || die "WP_PATH is required in apply mode."
    [[ -n "$WP_URL" ]]             || die "WP_URL is required in apply mode."
    [[ -n "$RADMAN_PRIVATE_DIR" ]] || die "RADMAN_PRIVATE_DIR is required in apply mode."
    [[ "$CONFIRM_STAGING_APPLY" == "YES" ]] \
        || die "CONFIRM_STAGING_APPLY must equal 'YES' for --apply-staging."

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

    command -v wp >/dev/null 2>&1 || die "wp-cli (wp) is required in PATH for apply mode."
fi

# -----------------------------------------------------------------------------
# WP-CLI wrapper (forces --path; never leaks env wholesale)
# -----------------------------------------------------------------------------
wp() {
    command wp --path="$WP_PATH" --no-color "$@"
}
wp_available() {
    [[ "$MODE" == "apply" ]] && command -v wp >/dev/null 2>&1
}

# -----------------------------------------------------------------------------
# Robust active-theme detection (cPanel jailshell + older wp-cli):
#   1. wp option get stylesheet — canonical, single value, no table formatting
#   2. wp theme list --status=active --format=csv (trimmed)
#   3. filesystem check of $WP_PATH/wp-content/themes/blocksy-child
# Falls back to "blocksy-child (detected-by-dir)" when wp-cli returns empty so
# we never hit "Active theme 'unknown'" on hosts where `wp theme list
# --field=name --format=trim` produces an empty string (MizbanFa CloudLinux
# jailshell quirk). All `wp post get` calls use --field=<key> only (never the
# unsupported --format=ids / --format=trim with `wp post get`).
# -----------------------------------------------------------------------------
get_active_theme() {
    local t=""
    if wp_available; then
        t="$(wp option get stylesheet 2>/dev/null | tr -d '[:space:]' || true)"
        if [[ -z "$t" ]]; then
            t="$(wp theme list --status=active --format=csv 2>/dev/null \
                | tail -n +2 | head -n 1 | cut -d',' -f1 | tr -d '[:space:]' || true)"
        fi
    fi
    if [[ -z "$t" && -d "$WP_PATH/wp-content/themes/blocksy-child" ]]; then
        echo "blocksy-child (detected-by-dir)"
        return 0
    fi
    if [[ -z "$t" && -d "$WP_PATH/wp-content/themes/blocksy" ]]; then
        echo "blocksy (detected-by-dir)"
        return 0
    fi
    echo "${t:-unknown}"
}

# -----------------------------------------------------------------------------
# Safe option reader (never hard-fails on missing options)
# -----------------------------------------------------------------------------
wp_opt() {
    local key="$1"
    local val
    val="$(wp option get "$key" 2>/dev/null || true)"
    # wp option get returns exit 0 with empty output when option is missing
    # on some wp-cli versions; normalise to __MISSING__ for empty.
    if [[ -z "$val" ]]; then
        echo "__MISSING__"
    else
        echo "$val"
    fi
}

wp_theme_mod() {
    local key="$1"
    local val
    val="$(wp theme mod get "$key" --format=csv 2>/dev/null | tail -n +2 | head -n 1 | cut -d',' -f2- || true)"
    echo "${val:-__MISSING__}"
}

# -----------------------------------------------------------------------------
# Private dir / lock / backup locations
# -----------------------------------------------------------------------------
LOCK_FD=""
BACKUP_DIR=""
LOCKFILE=""
# Compute backup/lock paths for plan mode as well (for display) so the owner
# can see where backups will land even in --plan output. If RADMAN_PRIVATE_DIR
# is not set (pure local plan), fall back to a clearly-marked placeholder.
if [[ -n "${RADMAN_PRIVATE_DIR:-}" ]]; then
    BACKUP_DIR="$RADMAN_PRIVATE_DIR/backups"
else
    BACKUP_DIR="\$RADMAN_PRIVATE_DIR/backups  (set RADMAN_PRIVATE_DIR to resolve)"
fi

if [[ "$MODE" == "apply" ]]; then
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
    flock -n "$LOCK_FD" || die "Another deployment appears to be running (lock held)."
fi

TS="$(date +%Y%m%d-%H%M%S)"

# -----------------------------------------------------------------------------
# Guard verification / auto-heal (staging identity)
#
# IMPORTANT ROBUSTNESS FIX per PR-18 requirements:
#   `wp option get blog_public` returned empty on some hosts (cPanel/CloudLinux
#   jailshell with older wp-cli); previous scripts hard-failed with
#   "blog_public is '__MISSING__' (expected '0')". This version treats empty/
#   missing/non-zero as "set it to 0" and continues — staging MUST be noindex.
# -----------------------------------------------------------------------------
BLOG_PUBLIC_BEFORE="__PLAN__"
BLOG_PUBLIC_AFTER="__PLAN__"
ACTIVE_THEME="__PLAN__"
HOME_URL="__PLAN__"
SITE_URL="__PLAN__"
LOGO_BEFORE="__PLAN__"
SITE_ICON_BEFORE="__PLAN__"

if [[ "$MODE" == "apply" ]]; then
    log "Verifying staging identity..."

    # blog_public: read robustly; heal if empty/missing/non-zero.
    blog_public_raw="$(wp option get blog_public 2>/dev/null || echo '')"
    if [[ -z "$blog_public_raw" || "$blog_public_raw" == "__MISSING__" || "$blog_public_raw" != "0" ]]; then
        BLOG_PUBLIC_BEFORE="${blog_public_raw:-<empty>}"
        warn "blog_public is '${BLOG_PUBLIC_BEFORE}' (expected 0). Auto-healing: setting blog_public=0 (staging MUST be noindex)."
        wp option update blog_public 0 >/dev/null
        BLOG_PUBLIC_AFTER="$(wp option get blog_public 2>/dev/null || echo 0)"
    else
        BLOG_PUBLIC_BEFORE="$blog_public_raw"
        BLOG_PUBLIC_AFTER="$blog_public_raw"
    fi

    HOME_URL="$(wp option get home 2>/dev/null || echo __MISSING__)"
    SITE_URL="$(wp option get siteurl 2>/dev/null || echo __MISSING__)"
    [[ "$HOME_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WordPress home option is '${HOME_URL}' (expected '${EXPECTED_WP_URL}')."
    [[ "$SITE_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WordPress siteurl option is '${SITE_URL}' (expected '${EXPECTED_WP_URL}')."

    ACTIVE_THEME="$(get_active_theme)"
    # Normalise "(detected-by-dir)" suffix when comparing.
    _active_base="${ACTIVE_THEME%% *}"
    if [[ "$_active_base" != "blocksy-child" && "$_active_base" != "blocksy" ]]; then
        die "Active theme '${ACTIVE_THEME}' is not Blocksy-compatible. Refusing to proceed."
    fi

    LOGO_BEFORE="$(wp theme mod get custom_logo --format=csv 2>/dev/null | tail -n +2 | head -n 1 | cut -d',' -f2- || echo __MISSING__)"
    SITE_ICON_BEFORE="$(wp option get site_icon 2>/dev/null || echo __MISSING__)"
fi

print_guard_section() {
    log ""
    log "=================== ENVIRONMENT GUARDS ==================="
    printf '  %-32s %s\n' "APP_ENV"              "$APP_ENV"
    printf '  %-32s %s\n' "WP_URL"               "$WP_URL"
    printf '  %-32s %s\n' "WP_PATH"              "$WP_PATH"
    printf '  %-32s %s\n' "blog_public (noindex) before" "${BLOG_PUBLIC_BEFORE} (healed to ${BLOG_PUBLIC_AFTER})"
    printf '  %-32s %s\n' "home"                 "$HOME_URL"
    printf '  %-32s %s\n' "siteurl"              "$SITE_URL"
    printf '  %-32s %s\n' "Active theme"         "$ACTIVE_THEME"
    printf '  %-32s %s\n' "custom_logo (before)" "$LOGO_BEFORE"
    printf '  %-32s %s\n' "site_icon (before)"   "$SITE_ICON_BEFORE"
    log "=========================================================="
    log ""
}
print_guard_section

# -----------------------------------------------------------------------------
# Phase 1 — Backups (DB + child theme + homepage) before any mutation
# -----------------------------------------------------------------------------
DB_BACKUP="__PLAN__"
THEME_BACKUP="__PLAN__"
HOMEPAGE_BACKUP_PATH="__PLAN__"
THEME_TARGET="${WP_PATH}/wp-content/themes/blocksy-child"
HOMEPAGE_TEMPLATE="$RADMAN_REPO_ROOT/templates/home-page-gutenberg.html"

backup_all() {
    log ">>>>>>>>>> Phase 1: Pre-mutation backups"
    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[PLAN] Would create timestamped backups under: ${BACKUP_DIR}"
        log "[PLAN]   - DB dump              : wordpress-db-${TS}.sql"
        log "[PLAN]   - Child theme tarball  : blocksy-child-${TS}.tar.gz"
        log "[PLAN]   - Homepage (ID ${HOMEPAGE_ID}) HTML : home-page-${HOMEPAGE_ID}-${TS}.html"
    else
        DB_BACKUP="${BACKUP_DIR}/wordpress-db-${TS}.sql"
        wp db export "$DB_BACKUP" >/dev/null
        chmod 600 "$DB_BACKUP"
        log "[APPLY] DB backup written: ${DB_BACKUP}"

        if [[ -d "$THEME_TARGET" ]]; then
            THEME_BACKUP="${BACKUP_DIR}/blocksy-child-${TS}.tar.gz"
            tar -C "$(dirname "$THEME_TARGET")" -czf "$THEME_BACKUP" "$(basename "$THEME_TARGET")"
            chmod 600 "$THEME_BACKUP"
            log "[APPLY] Existing child theme backed up: ${THEME_BACKUP}"
        fi

        if wp post exists "$HOMEPAGE_ID" >/dev/null 2>&1; then
            HOMEPAGE_BACKUP_PATH="${BACKUP_DIR}/home-page-${HOMEPAGE_ID}-${TS}.html"
            wp post get "$HOMEPAGE_ID" --field=post_content > "$HOMEPAGE_BACKUP_PATH"
            chmod 600 "$HOMEPAGE_BACKUP_PATH"
            log "[APPLY] Homepage (ID ${HOMEPAGE_ID}) content backed up: ${HOMEPAGE_BACKUP_PATH}"
        else
            warn "Homepage ID ${HOMEPAGE_ID} does not yet exist — will be created? Refusing to create outside the storefront batch runner. Aborting before mutation."
            die "Homepage ID ${HOMEPAGE_ID} is missing on this host. Run scripts/build_staging_storefront.sh --check first to verify foundation."
        fi
    fi
    log "<<<<<<<<<< Phase 1 complete"
}
backup_all

# -----------------------------------------------------------------------------
# Phase 2 — Sync child theme (top-level files + assets/ + fonts/)
# -----------------------------------------------------------------------------
sync_child_theme() {
    log ">>>>>>>>>> Phase 2: Child theme + design system assets sync"
    local src_theme_dir="$RADMAN_REPO_ROOT/theme/blocksy-child"
    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[PLAN] Would ensure target dir: ${THEME_TARGET}"
        log "[PLAN] Would install top-level files:"
        for f in "${CHILD_THEME_TOP_FILES[@]}"; do
            log "[PLAN]   - ${f}"
        done
        log "[PLAN] Would install CSS assets:"
        for f in "${CHILD_THEME_ASSETS[@]}"; do
            log "[PLAN]   - ${f}"
        done
        log "[PLAN] Would install local WOFF2 webfonts (Estedad + Vazirmatn):"
        for f in "${CHILD_THEME_FONTS[@]}"; do
            log "[PLAN]   - ${f}"
        done
        log "[PLAN] Would activate blocksy-child if not already active."
    else
        mkdir -p "$THEME_TARGET"
        mkdir -p "$THEME_TARGET/assets"
        mkdir -p "$THEME_TARGET/fonts"

        for f in "${CHILD_THEME_TOP_FILES[@]}"; do
            install -m 644 "$src_theme_dir/$f" "$THEME_TARGET/$f"
        done
        for f in "${CHILD_THEME_ASSETS[@]}"; do
            install -m 644 "$src_theme_dir/$f" "$THEME_TARGET/$f"
        done
        for f in "${CHILD_THEME_FONTS[@]}"; do
            install -m 644 "$src_theme_dir/$f" "$THEME_TARGET/$f"
        done
        log "[APPLY] Child theme files synced (${#CHILD_THEME_TOP_FILES[@]} top + ${#CHILD_THEME_ASSETS[@]} css + ${#CHILD_THEME_FONTS[@]} woff2)."

        # Ensure active (use the robust detector)
        cur_theme="$(get_active_theme)"
        _cur_base="${cur_theme%% *}"
        if [[ "$_cur_base" != "blocksy-child" ]]; then
            wp theme activate blocksy-child >/dev/null
            log "[APPLY] blocksy-child activated (was '${cur_theme}')."
        else
            log "[APPLY] blocksy-child already active (detected: ${cur_theme})."
        fi
    fi
    log "<<<<<<<<<< Phase 2 complete"
}
sync_child_theme

# -----------------------------------------------------------------------------
# Phase 3 — Import logo + favicon, set theme mods
# -----------------------------------------------------------------------------
set_branding() {
    log ">>>>>>>>>> Phase 3: Logo + favicon import & theme_mods"
    local logo_src="$RADMAN_REPO_ROOT/assets/branding/${LOGO_HEADER_FILE}"
    local favicon_src="$RADMAN_REPO_ROOT/assets/branding/${FAVICON_FILE}"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[PLAN] Would check existing custom_logo / site_icon and PRESERVE them if already set."
        log "[PLAN] Would import logo media (only if missing): ${LOGO_HEADER_FILE}"
        log "[PLAN] Would set theme_mod custom_logo → imported attachment ID (only if no existing logo)"
        log "[PLAN] Would import favicon media (only if missing): ${FAVICON_FILE}"
        log "[PLAN] Would set option site_icon → imported attachment ID (only if no existing icon)"
        log "[PLAN] Would apply safe theme_mod defaults:"
        log "[PLAN]   - header background  : #0B0B0E (matte black)"
        log "[PLAN]   - header sticky       : off"
        log "[PLAN]   - logo max-height     : 52 (desktop) / 42 (mobile)"
        log "[PLAN]   (Menu/footer layout left to Customizer — see runbook.)"
    else
        # Helper: import media file by absolute path and return attachment ID.
        import_media() {
            local abs_path="$1"
            local title_slug="$2"
            # wp media import returns a line like "Imported file ... as ID NNN."
            local out
            out="$(wp media import "$abs_path" --title="$title_slug" --porcelain 2>&1 || true)"
            # --porcelain returns just the ID; if something went wrong, fail loud.
            if [[ -z "$out" || ! "$out" =~ ^[0-9]+$ ]]; then
                # May already exist with same filename; try to find by title slug.
                local found
                found="$(wp post list --post_type=attachment --name="$title_slug" --fields=ID --format=ids 2>/dev/null | tr -d '[:space:]' | awk '{print $1}')"
                if [[ -n "$found" ]]; then
                    echo "$found"
                    return 0
                fi
                die "Failed to import media '${abs_path}': ${out}"
            fi
            echo "$out"
        }

        # --- Header logo: PRESERVE existing if already a valid numeric attachment ID ---
        local existing_logo_raw
        existing_logo_raw="$(wp theme mod get custom_logo --format=csv 2>/dev/null | tail -n +2 | head -n 1 | cut -d',' -f2- | tr -d '[:space:]' || true)"
        if [[ "$existing_logo_raw" =~ ^[0-9]+$ ]] && wp post exists "$existing_logo_raw" >/dev/null 2>&1; then
            log "[APPLY] Existing custom logo preserved: attachment ID ${existing_logo_raw}"
        else
            local logo_id
            logo_id="$(import_media "$logo_src" "radman-logo-header-ivory")"
            log "[APPLY] Ivory logo imported / found as attachment ID: ${logo_id}"
            wp theme mod set custom_logo "$logo_id" >/dev/null
            log "[APPLY] theme_mod custom_logo set to ${logo_id} (ivory on dark header)."
        fi

        # --- Site icon (favicon): PRESERVE existing if already a valid numeric attachment ID ---
        local existing_icon_raw
        existing_icon_raw="$(wp option get site_icon 2>/dev/null | tr -d '[:space:]' || true)"
        if [[ "$existing_icon_raw" =~ ^[0-9]+$ ]] && wp post exists "$existing_icon_raw" >/dev/null 2>&1; then
            log "[APPLY] Existing site_icon preserved: attachment ID ${existing_icon_raw}"
        else
            local icon_id
            icon_id="$(import_media "$favicon_src" "radman-site-icon")"
            log "[APPLY] Favicon imported / found as attachment ID: ${icon_id}"
            wp option update site_icon "$icon_id" >/dev/null
            log "[APPLY] option site_icon set to ${icon_id}."
        fi

        # Safe theme_mod defaults for the luxury dark look. Keys are Blocksy's
        # theme_mod names; values chosen to match the design system palette.
        # We use --quiet and ignore failures for unknown keys (older Blocksy
        # may not have them), since the runbook documents remaining UI steps.
        set_theme_mod_quiet() {
            local k="$1" v="$2"
            wp theme mod set "$k" "$v" >/dev/null 2>&1 || true
        }
        set_theme_mod_quiet header_background_color "#0B0B0E"
        set_theme_mod_quiet header_text_color "#FAF7F2"
        set_theme_mod_quiet header_menu_item_color "#FAF7F2"
        set_theme_mod_quiet header_link_hover_color "#BFA67A"
        set_theme_mod_quiet sticky_header_type "none"
        set_theme_mod_quiet logoMaxHeight 52
        set_theme_mod_quiet logoMaxHeightTablet 46
        set_theme_mod_quiet logoMaxHeightMobile 42
        set_theme_mod_quiet buttonMinHeight 48
        set_theme_mod_quiet buttonBorderRadius 0
        set_theme_mod_quiet backgroundColor "#0B0B0E"
        set_theme_mod_quiet content_background_color "#0B0B0E"
        log "[APPLY] Safe theme_mod defaults applied (dark header, sharp corners, gold hover)."
    fi
    log "<<<<<<<<<< Phase 3 complete"
}
set_branding

# -----------------------------------------------------------------------------
# Phase 4 — Refined homepage template (ID 18)
# -----------------------------------------------------------------------------
apply_homepage() {
    log ">>>>>>>>>> Phase 4: Homepage (page ID ${HOMEPAGE_ID}) template update"
    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[PLAN] Would back up current homepage post_content → ${HOMEPAGE_BACKUP_PATH}"
        log "[PLAN] Would update page ${HOMEPAGE_ID} post_content from refined template:"
        log "[PLAN]   ${HOMEPAGE_TEMPLATE}"
        log "[PLAN] Would ensure post_title='خانه', post_status=publish (staging only, noindex via blog_public=0)."
        log "[PLAN] Would enforce show_on_front=page, page_on_front=${HOMEPAGE_ID}."
    else
        wp post update "$HOMEPAGE_ID" \
            --post_title="خانه" \
            --post_name="home" \
            --post_status=publish \
            --post_content="$(cat "$HOMEPAGE_TEMPLATE")" >/dev/null
        log "[APPLY] Page ${HOMEPAGE_ID} updated with refined Gutenberg template."

        wp option update show_on_front page >/dev/null
        wp option update page_on_front "$HOMEPAGE_ID" >/dev/null
        log "[APPLY] show_on_front=page page_on_front=${HOMEPAGE_ID} enforced."

        # Verify the H1 hero marker landed.
        local new_content
        new_content="$(wp post get "$HOMEPAGE_ID" --field=post_content 2>/dev/null || true)"
        if [[ "$new_content" != *"نقره ۹۲۵؛"*"اصالت در جزئیات"* ]]; then
            die "Homepage hero H1 not present after update — aborting."
        fi
        log "[APPLY] Hero H1 verified in updated homepage content."
    fi
    log "<<<<<<<<<< Phase 4 complete"
}
apply_homepage

# -----------------------------------------------------------------------------
# Phase 5 — Cache flush
# -----------------------------------------------------------------------------
flush_caches() {
    log ">>>>>>>>>> Phase 5: Cache flush"
    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "[PLAN] Would run: wp cache flush"
        log "[PLAN] Would run (if available): wp litespeed-purge all"
    else
        wp cache flush >/dev/null 2>&1 || warn "wp cache flush reported an issue (non-fatal)."
        # LiteSpeed purge is best-effort; do NOT enable any LiteSpeed options here.
        if wp litespeed-purge all >/dev/null 2>&1; then
            log "[APPLY] LiteSpeed cache purged."
        else
            log "[APPLY] wp litespeed-purge not available or failed (non-fatal; cache plugin may not be active)."
        fi
    fi
    log "<<<<<<<<<< Phase 5 complete"
}
flush_caches

# -----------------------------------------------------------------------------
# Summary + manual visual-check checklist
# -----------------------------------------------------------------------------
log ""
log "=================== AFTER / SUMMARY ==================="
if [[ "$DRY_RUN" -eq 1 ]]; then
    log "PLAN mode complete. No host changes were made."
    log ""
    log "What WILL happen on --apply-staging:"
    log "  1. DB + child-theme + homepage (ID 18) backups written to:"
    log "       ${BACKUP_DIR}"
    log "  2. Child theme files synced to ${THEME_TARGET}:"
    log "       style.css (v${DESIGN_VERSION}), functions.php (enqueues fonts + design-system)"
    log "       assets/radman-fonts.css  (local @font-face, NO Google Fonts)"
    log "       assets/radman-design-system.css (luxury typography + components)"
    log "       fonts/*.woff2  (Estedad + Vazirmatn, 14 files)"
    log "  3. Logo  (${LOGO_HEADER_FILE}) imported + set as custom_logo ONLY if no valid logo exists."
    log "     Existing custom_logo / site_icon are PRESERVED (not overwritten)."
    log "     Favicon (${FAVICON_FILE}) imported + set as site_icon ONLY if missing."
    log "  4. Safe dark-luxury theme_mods applied (header bg, sticky=off, logo size)."
    log "  5. Homepage (ID 18) updated with refined Gutenberg template (55 blocks, balanced)."
    log "  6. Object + LiteSpeed caches flushed (best-effort)."
else
    log "APPLY complete."
    log "  Backups written to : ${BACKUP_DIR}"
    _post_theme="$(get_active_theme)"
    log "  Active theme       : ${_post_theme}"
    log "  custom_logo (after): $(wp theme mod get custom_logo --format=csv | tail -n +2 | head -n 1 | cut -d',' -f2- || true)"
    log "  site_icon  (after): $(wp option get site_icon 2>/dev/null || echo unknown)"
    log "  blog_public (after): $(wp option get blog_public 2>/dev/null || echo 0)  (staging MUST be 0 = noindex)"
fi
log ""
log "=================== MANUAL VISUAL CHECKLIST ==================="
log "After applying, the owner should open https://staging.radmansilver.ir in a"
log "private/incognito window and verify:"
log "  [ ] Persian Radman logo appears in the header (ivory logo on the dark/matte-black header)."
log "  [ ] Site uses the new local Persian font (Estedad for headings,"
log "      Vazirmatn for body) — NOT the default Blocksy system font."
log "  [ ] Hero H1 ('نقره ۹۲۵؛ اصالت در جزئیات') is large, bold, ivory,"
log "      with gold eyebrow label and two sharp-corner CTA buttons."
log "  [ ] Trust strip sits on ivory with diamond markers and four promises."
log "  [ ] Three category cards (انگشتر / گردنبند / دستبند) appear as dark"
log "      cards on ivory with gold top-border reveal on hover."
log "  [ ] Primary CTA 'ورود به فروشگاه' appears above the brand-intro and"
log "      in the hero."
log "  [ ] Footer is on dark surface with ivory-muted text and gold links."
log "  [ ] Yellow (now dark-tinted gold) staging notice remains at the bottom."
log "  [ ] Hover on header links shows gold underline."
log "  [ ] Buttons across the site (add to cart, checkout, view cart) are"
log "      gold-filled or gold-outlined with zero border-radius."
log "  [ ] Favicon (monogram) appears on the browser tab."
log ""
log "If anything looks off, see docs/DESIGN-SYSTEM-RUNBOOK.md for the minimal"
log "set of Customizer tweaks and a rollback procedure using the backups above."
log "==============================================================="
