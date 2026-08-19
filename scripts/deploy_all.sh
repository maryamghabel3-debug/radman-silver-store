#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — ONE-COMMAND STAGING DEPLOY
# ------------------------------------------------------------------------------
# Master runner that chains (safe idempotent flow for already-installed staging):
#   1. scripts/build_staging_storefront.sh --check
#        (READ-ONLY verification of existing WordPress/woocommerce/child-theme/
#         pages/categories/menu state. Does NOT re-apply foundation; does NOT
#         overwrite existing static-page content; does NOT reset published
#         pages back to Draft; does NOT recreate menu items or categories.)
#   2. scripts/apply_design_system.sh --apply-staging
#        (PR-18/PR-20 design system: local webfonts, CSS design system,
#         idempotent logo/favicon that PRESERVES an existing owner-configured
#         ivory custom_logo or site_icon, refined homepage template, safe
#         theme_mods, auto-heal blog_public=0.)
#   3. scripts/install_agents.sh --install
#        (PR-19 on-host cron agents: order watcher, price engine, stock
#         guard. Existing staging.env is NEVER overwritten (DB creds/secrets
#         preserved). Only missing directories/files are created. Smoke
#         tests run with DRY_RUN=1. Cron lines are PRINTED ONLY — never
#         auto-registered. No SMS, no price writes, no order-status changes.)
#
# MODES:
#   --plan           (default) dry-run of every stage; prints intent only.
#   --apply-staging  execute mutating staging operations.
#
# REQUIRED ENV (apply mode):
#   APP_ENV=staging
#   CONFIRM_STAGING_APPLY=YES
#   WP_PATH=/home/radmansi/staging.radmansilver.ir
#   WP_URL=https://staging.radmansilver.ir
#   RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo
#   RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman
#
# PRODUCTION IS PROHIBITED BY DESIGN (every sub-script enforces this).
# Payments, SMS, Redis, analytics, SEO-indexing, LiteSpeed aggressive
# optimizations, and Draft-page publication are NEVER enabled by this script.
# ==============================================================================

set -Eeuo pipefail
# NO 'set -x' — secrets must never leak.
export PATH="$HOME/bin:$PATH"

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
readonly EXPECTED_APP_ENV="staging"
readonly EXPECTED_WP_URL="https://staging.radmansilver.ir"
readonly EXPECTED_WP_PATH="/home/radmansi/staging.radmansilver.ir"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MODE="plan"
DRY_RUN=1

log()  { printf '[INFO]  %s\n' "$*"; }
warn() { printf '[WARN]  %s\n' "$*" >&2; }
err()  { printf '[ERROR] %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

on_error() {
    local exit_code=$?
    local line=$1
    err "deploy_all aborted (line ${line}, exit=${exit_code})."
    err "Check logs under RADMAN_PRIVATE_DIR/logs/ and per-script output above."
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

usage() {
    cat <<'USAGE'
Usage:
  bash scripts/deploy_all.sh --plan            # dry run (default)
  bash scripts/deploy_all.sh --apply-staging   # mutate staging

Required env for --apply-staging:
  export PATH="$HOME/bin:$PATH"
  APP_ENV=staging
  CONFIRM_STAGING_APPLY=YES
  WP_PATH=/home/radmansi/staging.radmansilver.ir
  WP_URL=https://staging.radmansilver.ir
  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman

Stages (safe idempotent order — does NOT re-apply the foundation on already-installed staging):
  1. build_staging_storefront.sh --check  — Foundation verification (READ-ONLY)
  2. apply_design_system.sh --apply-staging — Design system (fonts/CSS/logo/homepage polish)
  3. install_agents.sh --install           — PR-19 agents (DRY_RUN=1; cron lines PRINTED only, never registered)
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

# Inherit env from caller; apply safe defaults for plan mode.
APP_ENV="${APP_ENV:-$EXPECTED_APP_ENV}"
WP_PATH="${WP_PATH:-$EXPECTED_WP_PATH}"
WP_URL="${WP_URL:-$EXPECTED_WP_URL}"
RADMAN_REPO_ROOT="${RADMAN_REPO_ROOT:-$REPO_ROOT}"
RADMAN_PRIVATE_DIR="${RADMAN_PRIVATE_DIR:-$HOME/.config/radman}"
CONFIRM_STAGING_APPLY="${CONFIRM_STAGING_APPLY:-NO}"

log "===================================================================="
log "RADMAN SILVER 925 — ONE-COMMAND STAGING DEPLOY"
log "Mode: ${MODE}    (dry_run=${DRY_RUN})"
log "RADMAN_REPO_ROOT   = ${RADMAN_REPO_ROOT}"
log "RADMAN_PRIVATE_DIR = ${RADMAN_PRIVATE_DIR}"
log "WP_PATH            = ${WP_PATH}"
log "WP_URL             = ${WP_URL}"
log "===================================================================="

# -----------------------------------------------------------------------------
# Common environment to propagate to sub-scripts
# -----------------------------------------------------------------------------
COMMON_ENV=(
    "PATH=$PATH"
    "APP_ENV=$APP_ENV"
    "WP_PATH=$WP_PATH"
    "WP_URL=$WP_URL"
    "RADMAN_REPO_ROOT=$RADMAN_REPO_ROOT"
    "RADMAN_PRIVATE_DIR=$RADMAN_PRIVATE_DIR"
)
if [[ "$DRY_RUN" -eq 0 ]]; then
    COMMON_ENV+=("CONFIRM_STAGING_APPLY=YES")
fi

# -----------------------------------------------------------------------------
# Staging guards (apply mode)
# -----------------------------------------------------------------------------
if [[ "$MODE" == "apply" ]]; then
    [[ "$CONFIRM_STAGING_APPLY" == "YES" ]] \
        || die "CONFIRM_STAGING_APPLY must equal 'YES' for --apply-staging."
    [[ "$APP_ENV" == "$EXPECTED_APP_ENV" ]] \
        || die "APP_ENV must equal '${EXPECTED_APP_ENV}' (got '${APP_ENV}')."
    [[ "$WP_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WP_URL must equal '${EXPECTED_WP_URL}' (got '${WP_URL}')."
    [[ "$WP_PATH" == "$EXPECTED_WP_PATH" ]] \
        || die "WP_PATH must equal '${EXPECTED_WP_PATH}' (got '${WP_PATH}')."
    [[ "$WP_PATH" != *"public_html"* ]] \
        || die "WP_PATH contains 'public_html' — PRODUCTION PATH PROHIBITED."
    [[ -f "$WP_PATH/wp-settings.php" ]] \
        || die "WP_PATH does not look like WordPress (missing wp-settings.php): ${WP_PATH}"
    command -v wp >/dev/null 2>&1 || die "wp-cli (wp) is required in PATH."
fi

# -----------------------------------------------------------------------------
# Stage runner
# -----------------------------------------------------------------------------
run_stage() {
    local label="$1"
    local script="$2"
    local flag="$3"     # --plan or --apply-staging / --install

    log ""
    log "==================== STAGE: ${label} ===================="
    if [[ ! -f "$RADMAN_REPO_ROOT/$script" ]]; then
        die "Stage script missing: ${RADMAN_REPO_ROOT}/${script}"
    fi

    if [[ "$DRY_RUN" -eq 1 && "$flag" == "--install" ]]; then
        # install_agents.sh defaults to plan behaviour without --install.
        env "${COMMON_ENV[@]}" bash "$RADMAN_REPO_ROOT/$script" --plan
    elif [[ "$DRY_RUN" -eq 1 ]]; then
        env "${COMMON_ENV[@]}" bash "$RADMAN_REPO_ROOT/$script" --plan
    else
        env "${COMMON_ENV[@]}" bash "$RADMAN_REPO_ROOT/$script" "$flag"
    fi
    log "<<<<<<<<<< Stage '${label}' completed."
}

log ""
log "[IMPORTANT] Stage 1 runs in READ-ONLY verification mode."
log "[IMPORTANT] The storefront foundation (pages/menu/categories/home content) is NOT re-applied."
log "[IMPORTANT] Existing static-page publication statuses are preserved."
log "[IMPORTANT] Existing ivory custom_logo and site_icon are preserved by Stage 2."
log "[IMPORTANT] Existing staging.env is NEVER overwritten; agents stay DRY_RUN=1."
log "[IMPORTANT] Cron lines are PRINTED for the owner and are NOT auto-registered."
log ""

run_stage "Foundation verification — read-only" \
    "scripts/build_staging_storefront.sh" \
    "$( [[ "$DRY_RUN" -eq 1 ]] && echo --check || echo --check )"

run_stage "Design system (fonts/CSS/logo/favicon/theme_mods)" \
    "scripts/apply_design_system.sh" \
    "$( [[ "$DRY_RUN" -eq 1 ]] && echo --plan || echo --apply-staging )"

run_stage "On-host cron agents (installer; DRY_RUN=1, cron lines printed only)" \
    "scripts/install_agents.sh" \
    "$( [[ "$DRY_RUN" -eq 1 ]] && echo --plan || echo --install )"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
log ""
log "===================================================================="
if [[ "$DRY_RUN" -eq 1 ]]; then
    log "PLAN MODE COMPLETE. No host changes were made."
    log ""
    log "To apply for real, run:"
    log "  export PATH=\"\$HOME/bin:\$PATH\""
    log "  APP_ENV=staging CONFIRM_STAGING_APPLY=YES \\"
    log "  WP_PATH=/home/radmansi/staging.radmansilver.ir \\"
    log "  WP_URL=https://staging.radmansilver.ir \\"
    log "  RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo \\"
    log "  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman \\"
    log "  bash /home/radmansi/radman-deploy/repo/scripts/deploy_all.sh --apply-staging"
else
    log "APPLY COMPLETE. Review logs in ${RADMAN_PRIVATE_DIR}/logs/."
    log ""
    log "Next manual steps:"
    log "  1. Open https://staging.radmansilver.ir in an incognito window and verify"
    log "     logo, fonts, hero, category cards, footer, staging notice."
    log "  2. Edit ${RADMAN_PRIVATE_DIR}/staging.env to set OWNER_MOBILE and"
    log "     (later) KAVENEGAR_API_KEY; keep DRY_RUN=1 until you are happy with"
    log "     outbox/*.txt notifications."
    log "  3. Write the daily silver rate into ${RADMAN_PRIVATE_DIR}/state/daily_rate.txt"
    log "     (single integer, Toman per gram) before enabling the price engine apply."
    log "  4. Add the three cron lines printed by install_agents.sh via cPanel."
    log ""
    log "All 11 static pages remain DRAFT. Payments/SMS/Redis/analytics/SEO indexing"
    log "and LiteSpeed aggressive optimizations are NOT enabled."
fi
log "===================================================================="
