#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — On-Host Agent Installer (cPanel / MizbanFa jailshell)
# ------------------------------------------------------------------------------
# Creates the required private directory structure under RADMAN_PRIVATE_DIR
# (~/.config/radman by default), ensures Python 3.11 is available, runs each of
# the three PR-19 agents once in DRY_RUN=1 as a smoke test, and prints the
# exact Cron Job lines the owner must paste into cPanel → Cron Jobs.
#
# MODES:
#   --plan      (default) Print intended actions; do not create dirs or run tests
#   --install   Create dirs + env template + smoke-test agents in DRY_RUN mode
#
# This installer NEVER:
#   - touches production/public_html
#   - enables payments/SMS/Redis/analytics
#   - sends real SMS (agents default to DRY_RUN=1; KAVENEGAR_API_KEY is empty by default)
#   - requires network access
# ==============================================================================

set -Eeuo pipefail
# NO 'set -x' — secrets must never leak.
export PATH="$HOME/bin:$PATH"

readonly EXPECTED_APP_ENV="staging"
readonly EXPECTED_WP_URL="https://staging.radmansilver.ir"
readonly EXPECTED_WP_PATH="/home/radmansi/staging.radmansilver.ir"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly AGENTS_DIR="$REPO_ROOT/agents"

MODE="plan"

log()  { printf '[INFO]  %s\n' "$*"; }
warn() { printf '[WARN]  %s\n' "$*" >&2; }
err()  { printf '[ERROR] %s\n' "$*" >&2; }
die()  { err "$*"; exit 1; }

on_error() {
    local exit_code=$?
    local line=$1
    err "Installer aborted (line ${line}, exit=${exit_code})."
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

usage() {
    cat <<'USAGE'
Usage:
  bash scripts/install_agents.sh --plan       # dry run (default)
  bash scripts/install_agents.sh --install    # create dirs + smoke test

Required env (can be set before running or answered interactively):
  RADMAN_REPO_ROOT    defaults to parent dir of this script
  RADMAN_PRIVATE_DIR  defaults to ~/.config/radman
  WP_PATH             defaults to /home/radmansi/staging.radmansilver.ir
  WP_URL              defaults to https://staging.radmansilver.ir
USAGE
}

# -----------------------------------------------------------------------------
# Print the exact Cron Job lines for the owner
# NOTE: defined EARLY so it is available in both --plan and --install.
# -----------------------------------------------------------------------------
print_cron_lines() {
    local tag="$1"
    local COMMON_ENV="APP_ENV=staging WP_PATH=${WP_PATH} WP_URL=${WP_URL} RADMAN_REPO_ROOT=${RADMAN_REPO_ROOT} RADMAN_PRIVATE_DIR=${RADMAN_PRIVATE_DIR} DRY_RUN=1"
    local PY="$PYTHON_BIN"
    log "==================== CRON JOB LINES (${tag}) ===================="
    log "cPanel → Advanced → Cron Jobs → Add Cron Job.  Set 'Shell: bash' if asked."
    log ""
    log "1) Order Watch — every 5 minutes:"
    log "   Schedule: */5 * * * *"
    log "   Command:"
    log "   ${COMMON_ENV} ${PY} ${RADMAN_REPO_ROOT}/agents/agent_order_watch.py >> ${RADMAN_PRIVATE_DIR}/logs/order_watch.cron.log 2>&1"
    log ""
    log "2) Stock Guard — once per hour (at minute 7):"
    log "   Schedule: 7 * * * *"
    log "   Command:"
    log "   ${COMMON_ENV} ${PY} ${RADMAN_REPO_ROOT}/agents/agent_stock_guard.py >> ${RADMAN_PRIVATE_DIR}/logs/stock_guard.cron.log 2>&1"
    log ""
    log "3) Price Engine — once per day at 09:07 (after owner updates daily rate):"
    log "   Schedule: 7 9 * * *"
    log "   Command (preview only — writes price_preview_*.txt into outbox/):"
    log "   ${COMMON_ENV} ${PY} ${RADMAN_REPO_ROOT}/agents/agent_price_engine.py >> ${RADMAN_PRIVATE_DIR}/logs/price_engine.cron.log 2>&1"
    log ""
    log "To APPLY price changes (after manual owner review of preview):"
    log "   Run manually in SSH, NOT on cron, after confirming the preview:"
    log "   APP_ENV=staging WP_PATH=${WP_PATH} WP_URL=${WP_URL} RADMAN_REPO_ROOT=${RADMAN_REPO_ROOT} RADMAN_PRIVATE_DIR=${RADMAN_PRIVATE_DIR} DRY_RUN=0 ${PY} ${RADMAN_REPO_ROOT}/agents/agent_price_engine.py --apply"
    log ""
    log "To enable real SMS (after you are happy with outbox notifications):"
    log "   Edit ${RADMAN_PRIVATE_DIR}/staging.env, set KAVENEGAR_API_KEY=..., then"
    log "   change DRY_RUN=1 to DRY_RUN=0 in the Cron command line for order_watch."
    log "=================================================================="
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)     MODE="plan";    shift ;;
        --install)  MODE="install"; shift ;;
        -h|--help)  usage; exit 0 ;;
        *)          usage; die "Unknown argument: $1" ;;
    esac
done

RADMAN_REPO_ROOT="${RADMAN_REPO_ROOT:-$REPO_ROOT}"
RADMAN_PRIVATE_DIR="${RADMAN_PRIVATE_DIR:-$HOME/.config/radman}"
WP_PATH="${WP_PATH:-$EXPECTED_WP_PATH}"
WP_URL="${WP_URL:-$EXPECTED_WP_URL}"
APP_ENV="${APP_ENV:-staging}"

# -----------------------------------------------------------------------------
# Guards
# -----------------------------------------------------------------------------
[[ -d "$RADMAN_REPO_ROOT/agents/lib" ]] \
    || die "Agents directory not found under RADMAN_REPO_ROOT: ${RADMAN_REPO_ROOT}/agents"
[[ "$APP_ENV" == "$EXPECTED_APP_ENV" ]] \
    || die "APP_ENV must equal '${EXPECTED_APP_ENV}' (got '${APP_ENV}')."
[[ "$WP_URL" == "$EXPECTED_WP_URL" ]] \
    || die "WP_URL must equal '${EXPECTED_WP_URL}' (got '${WP_URL}')."
[[ "$WP_PATH" != *"public_html"* ]] \
    || die "WP_PATH contains 'public_html' — production path PROHIBITED."

log "===================================================================="
log "RADMAN SILVER 925 — On-Host Agent Installer"
log "Mode: ${MODE}"
log "RADMAN_REPO_ROOT    = ${RADMAN_REPO_ROOT}"
log "RADMAN_PRIVATE_DIR  = ${RADMAN_PRIVATE_DIR}"
log "WP_PATH             = ${WP_PATH}"
log "WP_URL              = ${WP_URL}"
log "===================================================================="

# -----------------------------------------------------------------------------
# Python discovery
# -----------------------------------------------------------------------------
PYTHON_BIN=""
for cand in python3.11 /opt/alt/python311/bin/python3.11 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        PYTHON_BIN="$cand"
        break
    fi
done
if [[ -z "$PYTHON_BIN" ]]; then
    die "Python 3.11+ is required but no python3/python3.11 was found in PATH."
fi
PY_VER="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
log "Python binary: ${PYTHON_BIN} (${PY_VER})"

# -----------------------------------------------------------------------------
# Paths to create
# -----------------------------------------------------------------------------
PRIVATE_SUBDIRS=( state outbox logs backups locks )

if [[ "$MODE" == "plan" ]]; then
    log ""
    log "[PLAN] Would create directory structure under ${RADMAN_PRIVATE_DIR}:"
    for d in "${PRIVATE_SUBDIRS[@]}"; do
        log "  - ${RADMAN_PRIVATE_DIR}/${d}/   (chmod 700)"
    done
    ENV_TARGET="${RADMAN_PRIVATE_DIR}/staging.env"
    log "[PLAN] Would install (if missing) env template at: ${ENV_TARGET}"
    log "[PLAN] Would smoke-test all 3 agents in DRY_RUN=1:"
    log "  1. ${RADMAN_REPO_ROOT}/agents/agent_order_watch.py --dry-run"
    log "  2. ${RADMAN_REPO_ROOT}/agents/agent_price_engine.py --dry-run"
    log "  3. ${RADMAN_REPO_ROOT}/agents/agent_stock_guard.py"
    log ""
    print_cron_lines "PLAN"
    log ""
    log "Re-run with --install to execute the above."
    exit 0
fi

# -----------------------------------------------------------------------------
# Install mode
# -----------------------------------------------------------------------------
log ""
log "[INSTALL] Creating private directories (chmod 700)..."
mkdir -p "$RADMAN_PRIVATE_DIR"
chmod 700 "$RADMAN_PRIVATE_DIR"
for d in "${PRIVATE_SUBDIRS[@]}"; do
    mkdir -p "${RADMAN_PRIVATE_DIR}/${d}"
    chmod 700 "${RADMAN_PRIVATE_DIR}/${d}"
done

# Seed state/daily_rate.txt with a placeholder if absent
RATE_FILE="${RADMAN_PRIVATE_DIR}/state/daily_rate.txt"
if [[ ! -s "$RATE_FILE" ]]; then
    echo "# Write a single integer = Toman per gram (e.g. 85000). Remove this comment line." > "$RATE_FILE"
    chmod 600 "$RATE_FILE"
    log "[INSTALL] Created rate placeholder (with comment): ${RATE_FILE}"
fi

# Seed env template (chmod 600). DO NOT overwrite existing values.
ENV_TARGET="${RADMAN_PRIVATE_DIR}/staging.env"
if [[ ! -f "$ENV_TARGET" ]]; then
    cat > "$ENV_TARGET" <<'EOF'
# RADMAN SILVER 925 — staging environment for on-host agents
# chmod 600; DO NOT commit.
APP_ENV=staging
WP_PATH=/home/radmansi/staging.radmansilver.ir
WP_URL=https://staging.radmansilver.ir
RADMAN_REPO_ROOT=/home/radmansi/radman-deploy/repo
RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman

# DRY_RUN=1 means all agents write to outbox/*.txt and NEVER send SMS or mutate
# prices. Set DRY_RUN=0 ONLY after you've reviewed outbox outputs and filled in
# KAVENEGAR_API_KEY + OWNER_MOBILE.
DRY_RUN=1

# Kavenegar SMS (required for real SMS when DRY_RUN=0). Leave blank in dry mode.
KAVENEGAR_API_KEY=
OWNER_MOBILE=
KAVENEGAR_SENDER=10008445
EOF
    chmod 600 "$ENV_TARGET"
    log "[INSTALL] Wrote env template: ${ENV_TARGET} (chmod 600; please edit OWNER_MOBILE / API key when ready)."
else
    log "[INSTALL] Env file already exists, leaving untouched: ${ENV_TARGET}"
fi

# -----------------------------------------------------------------------------
# Smoke tests (DRY_RUN=1 always here so nothing is sent/changed)
# -----------------------------------------------------------------------------
log ""
log "[INSTALL] Smoke-testing agents in DRY_RUN mode..."

run_smoke() {
    local label="$1"; shift
    log "  -> ${label}"
    (
        cd "$RADMAN_REPO_ROOT"
        DRY_RUN=1 \
        APP_ENV=staging \
        WP_PATH="$WP_PATH" \
        WP_URL="$WP_URL" \
        RADMAN_REPO_ROOT="$RADMAN_REPO_ROOT" \
        RADMAN_PRIVATE_DIR="$RADMAN_PRIVATE_DIR" \
        "$PYTHON_BIN" "$@" 2>&1 | sed 's/^/       /'
    ) || warn "Smoke test '${label}' exited non-zero (expected if WP is not reachable from the current shell)."
}

run_smoke "Order Watch (dry run)" \
    "$AGENTS_DIR/agent_order_watch.py" --dry-run
run_smoke "Price Engine (dry run)" \
    "$AGENTS_DIR/agent_price_engine.py" --dry-run
run_smoke "Stock Guard (read-only)" \
    "$AGENTS_DIR/agent_stock_guard.py"

log ""
log "[INSTALL] Smoke tests completed. Outbox files should appear under:"
log "         ${RADMAN_PRIVATE_DIR}/outbox/"
log ""
print_cron_lines "INSTALL"
log ""
log "Next steps:"
log "  1. Edit ${RADMAN_PRIVATE_DIR}/staging.env and fill OWNER_MOBILE."
log "  2. Write today's silver rate into ${RADMAN_PRIVATE_DIR}/state/daily_rate.txt"
log "     (one integer = Toman per gram, e.g. 85000 — remove the # comment line)."
log "  3. Add the Cron Job lines printed above via cPanel → Advanced → Cron Jobs."
log "  4. After verifying outbox/*.txt for a day or two, set DRY_RUN=0 and fill"
log "     KAVENEGAR_API_KEY to enable real SMS."
log ""
log "All agents are DRY_RUN=1 by default. No SMS will be sent and no prices"
log "will be changed until you explicitly flip DRY_RUN=0 + set the API key."
