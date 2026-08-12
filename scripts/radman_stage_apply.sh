#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — One-Command Staging Apply (Owner Runner)
# ------------------------------------------------------------------------------
# Thin, reviewed wrapper over scripts/radman_branding_and_content_import.sh
# that:
#   - Defaults to plan mode (--plan).
#   - Adds a final explicit CONFIRM banner for --apply-staging.
#   - Enforces staging-only rules (no production flag exists by design).
#   - Never echoes secrets, never accepts credentials on the command line.
#   - Performs NO destructive actions against products, orders, users, or
#     core settings; does NOT publish pages; does NOT activate payments/SMS.
#
# Plan only:
#   APP_ENV=staging \
#   WP_PATH=/home/<CPANEL_USER>/staging.radmansilver.ir \
#   WP_URL=https://staging.radmansilver.ir \
#   RADMAN_REPO_ROOT=/home/<CPANEL_USER>/radman-deploy/repo \
#   RADMAN_PRIVATE_DIR=/home/<CPANEL_USER>/.config/radman \
#   bash scripts/radman_stage_apply.sh --plan
#
# Apply after reviewer approval:
#   APP_ENV=staging \
#   CONFIRM_STAGING_APPLY=YES \
#   WP_PATH=/home/<CPANEL_USER>/staging.radmansilver.ir \
#   WP_URL=https://staging.radmansilver.ir \
#   RADMAN_REPO_ROOT=/home/<CPANEL_USER>/radman-deploy/repo \
#   RADMAN_PRIVATE_DIR=/home/<CPANEL_USER>/.config/radman \
#   bash scripts/radman_stage_apply.sh --apply-staging
# ==============================================================================

set -Eeuo pipefail
# NO 'set -x'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="${SCRIPT_DIR}/radman_branding_and_content_import.sh"
MODE="--plan"

usage() {
    cat <<'USAGE'
Usage: bash scripts/radman_stage_apply.sh [--plan|--check|--apply-staging]

This runner is staging-only. There is no production flag and no --publish flag.
All static pages remain Draft after apply. Payments / SMS / agents are NOT activated.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)            MODE="--plan"; shift ;;
        --check)           MODE="--check"; shift ;;
        --apply-staging)   MODE="--apply-staging"; shift ;;
        -h|--help)         usage; exit 0 ;;
        *)                 usage; exit 2 ;;
    esac
done

[[ -f "$RUNNER" ]] || { echo "[FATAL] Missing runner: $RUNNER" >&2; exit 2; }

if [[ "$MODE" == "--apply-staging" ]]; then
    cat <<'BANNER'
======================================================================
 RADMAN SILVER 925 — STAGING APPLY (NON-PRODUCTION)
 --------------------------------------------------------------------
 - Target: https://staging.radmansilver.ir (blog_public=0 noindex)
 - Action: sync reviewed child theme + idempotent Draft-page upsert
 - Backup: timestamped DB + child-theme export in RADMAN_PRIVATE_DIR/backups
 - NOT touched: products, orders, users, payments, SMS, agents, menus, home page
 - NOT published: static pages will remain Draft
 - Production (public_html) is PROHIBITED by the lower-level runner
======================================================================
BANNER
fi

# Delegate to the fully-guarded runner.
exec bash "$RUNNER" "$MODE"
