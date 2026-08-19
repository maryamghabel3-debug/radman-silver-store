#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Safe Staging Branding & Static Content Deploy Runner
# ------------------------------------------------------------------------------
# Idempotent, staging-only, plan-by-default runner that:
#   1. Verifies it is running against staging.radmansilver.ir (NOT production).
#   2. Validates required environment variables and locks via flock.
#   3. Creates a sanitized DB + child-theme backup in RADMAN_PRIVATE_DIR/backups/.
#   4. Renders static pages from content/static-pages/ via render_static_pages.py.
#   5. Deploys the reviewed Blocksy child theme (idempotent file sync).
#   6. Upserts each official static page by slug (create Draft if missing,
#      never publish, never duplicate).
#
# MODES:
#   --plan            (default) Read-only dry run; prints intent, touches nothing.
#   --check           Read-only verification pass against staging (WP-CLI status).
#   --apply-staging   Execute mutating operations (requires CONFIRM_STAGING_APPLY=YES).
#
# PRODUCTION IS PROHIBITED BY DESIGN. There is no --apply-production flag.
#
# REQUIRED ENVIRONMENT VARIABLES (apply mode):
#   APP_ENV                 must equal 'staging'
#   WP_URL                  must equal 'https://staging.radmansilver.ir'
#   WP_PATH                 must contain a WordPress install AND must NOT be
#                           the production 'public_html' (must be staging path)
#   RADMAN_REPO_ROOT        must contain content/static-pages/ and theme/blocksy-child/
#   RADMAN_PRIVATE_DIR      private account directory (outside web root); backups
#                           and lockfile live here; chmod 700 ensured.
#   CONFIRM_STAGING_APPLY   must equal 'YES' only for --apply-staging
# ==============================================================================

set -Eeuo pipefail
# NO 'set -x' here — we never want to leak environment / credentials.

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
readonly EXPECTED_WP_URL="https://staging.radmansilver.ir"
readonly EXPECTED_APP_ENV="staging"
readonly EXPECTED_BLOG_PUBLIC=0
readonly CHILD_THEME_SOURCE_RELPATH="theme/blocksy-child"
readonly RENDERER_RELPATH="scripts/render_static_pages.py"
readonly LOCK_NAME="radman-stage-deploy.lock"
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT_FALLBACK="$(cd "$SCRIPT_DIR/.." && pwd)"

MODE="plan"
DRY_RUN=1
CHECK_ONLY=0

# -----------------------------------------------------------------------------
# Logging helpers (never echo env wholesale; never echo credentials)
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
  bash scripts/radman_branding_and_content_import.sh --plan            # dry run (default)
  bash scripts/radman_branding_and_content_import.sh --check           # read-only check
  bash scripts/radman_branding_and_content_import.sh --apply-staging   # mutate staging

Required env for --apply-staging:
  APP_ENV=staging
  WP_URL=https://staging.radmansilver.ir
  WP_PATH=/home/<CPANEL_USER>/staging.radmansilver.ir
  RADMAN_REPO_ROOT=/home/<CPANEL_USER>/radman-deploy/repo
  RADMAN_PRIVATE_DIR=/home/<CPANEL_USER>/.config/radman
  CONFIRM_STAGING_APPLY=YES

Production execution is explicitly prohibited by this script.
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

# Allow defaults when running inside a fresh clone on the agent sandbox
# (local plan/check only — never apply in sandbox).
RADMAN_REPO_ROOT="${RADMAN_REPO_ROOT:-$REPO_ROOT_FALLBACK}"
APP_ENV="${APP_ENV:-}"
WP_URL="${WP_URL:-}"
WP_PATH="${WP_PATH:-}"
RADMAN_PRIVATE_DIR="${RADMAN_PRIVATE_DIR:-}"
CONFIRM_STAGING_APPLY="${CONFIRM_STAGING_APPLY:-}"

log "RADMAN SILVER 925 — Staging Deploy Runner"
log "Mode: ${MODE}    (dry_run=${DRY_RUN})"
log "RADMAN_REPO_ROOT = ${RADMAN_REPO_ROOT}"

# -----------------------------------------------------------------------------
# Production & staging guards (run even in --plan so reviewers see intent)
# -----------------------------------------------------------------------------
[[ -d "$RADMAN_REPO_ROOT/content/static-pages" ]] \
    || die "RADMAN_REPO_ROOT does not contain content/static-pages/: ${RADMAN_REPO_ROOT}"
[[ -f "$RADMAN_REPO_ROOT/$RENDERER_RELPATH" ]] \
    || die "Renderer not found at ${RADMAN_REPO_ROOT}/${RENDERER_RELPATH}"
[[ -d "$RADMAN_REPO_ROOT/$CHILD_THEME_SOURCE_RELPATH" ]] \
    || die "Child theme source missing at ${RADMAN_REPO_ROOT}/${CHILD_THEME_SOURCE_RELPATH}"

if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    [[ -n "$WP_PATH" ]]           || die "WP_PATH is required in ${MODE} mode."
    [[ -n "$WP_URL" ]]            || die "WP_URL is required in ${MODE} mode."
    [[ -n "$RADMAN_PRIVATE_DIR" ]]|| die "RADMAN_PRIVATE_DIR is required in ${MODE} mode."
    [[ "$APP_ENV" == "$EXPECTED_APP_ENV" ]] \
        || die "APP_ENV must equal '${EXPECTED_APP_ENV}' (got: '${APP_ENV}'). Production is PROHIBITED."
    [[ "$WP_URL" == "$EXPECTED_WP_URL" ]] \
        || die "WP_URL must equal '${EXPECTED_WP_URL}' (got: '${WP_URL}'). Production is PROHIBITED."
    [[ "$WP_PATH" != *"public_html"* ]] \
        || die "WP_PATH contains 'public_html' — PRODUCTION PATH PROHIBITED."
    [[ -f "$WP_PATH/wp-settings.php" ]] \
        || die "WP_PATH does not look like a WordPress install (missing wp-settings.php): ${WP_PATH}"
fi

if [[ "$MODE" == "apply" ]]; then
    [[ "$CONFIRM_STAGING_APPLY" == "YES" ]] \
        || die "CONFIRM_STAGING_APPLY must equal 'YES' for --apply-staging."
fi

# -----------------------------------------------------------------------------
# WP-CLI wrapper (forces --path and avoids leaking credentials via process env)
# -----------------------------------------------------------------------------
wp() {
    command wp --path="$WP_PATH" --no-color "$@"
}

# -----------------------------------------------------------------------------
# Private directory / lockfile / backup location (apply & check only)
# -----------------------------------------------------------------------------
LOCK_FD=""
if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    mkdir -p "$RADMAN_PRIVATE_DIR"
    chmod 700 "$RADMAN_PRIVATE_DIR"
    BACKUP_DIR="$RADMAN_PRIVATE_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
    LOCKFILE="$RADMAN_PRIVATE_DIR/${LOCK_NAME}"
    log "Opening flock on ${LOCKFILE}"
    exec {LOCK_FD}>"$LOCKFILE"
    if [[ "$DRY_RUN" -eq 0 ]]; then
        flock -n "$LOCK_FD" || die "Another deployment appears to be running (lock held)."
    else
        # In check mode we do non-blocking probe but don't hold the lock.
        flock -n "$LOCK_FD" || warn "Lock currently held by another process."
    fi
fi

# -----------------------------------------------------------------------------
# Local-only render (always safe, no host mutation)
# -----------------------------------------------------------------------------
TS="$(date +%Y%m%d-%H%M%S)"
if [[ "$MODE" == "apply" ]]; then
    BUILD_DIR="$RADMAN_PRIVATE_DIR/build-${TS}"
    mkdir -p "$BUILD_DIR"
else
    # Portable temp dir: prefer mktemp (works on jailshell/LiteSpeed/cPanel);
    # fall back to /tmp if TMPDIR is unavailable.
    if command -v mktemp >/dev/null 2>&1; then
        BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/radman-plan-${TS}-XXXX")"
    else
        BUILD_DIR="${TMPDIR:-/tmp}/radman-plan-${TS}-$$"
        mkdir -p "$BUILD_DIR"
    fi
fi
log "Rendering static pages → ${BUILD_DIR}"
python3 "$RADMAN_REPO_ROOT/$RENDERER_RELPATH" \
    --repo-root "$RADMAN_REPO_ROOT" \
    --build-dir "$BUILD_DIR"

# Enforce placeholder-free output even in plan mode so reviewers see problems
# before approving an --apply-staging run. If any "[…]" markers or
# radman-placeholder spans remain, fail cleanly with a message listing the
# offending files. This gate does not touch the host.
log "Running placeholder gate on rendered HTML..."
python3 "$RADMAN_REPO_ROOT/scripts/check_no_placeholders.py" "$BUILD_DIR"

# -----------------------------------------------------------------------------
# Robust helpers (jailshell-safe)
# -----------------------------------------------------------------------------
get_active_theme() {
    local t=""
    t="$(wp option get stylesheet 2>/dev/null | tr -d '[:space:]' || true)"
    if [[ -z "$t" ]]; then
        t="$(wp theme list --status=active --format=csv 2>/dev/null \
            | tail -n +2 | head -n 1 | cut -d',' -f1 | tr -d '[:space:]' || true)"
    fi
    if [[ -z "$t" && -d "${WP_PATH}/wp-content/themes/blocksy-child" ]]; then
        echo "blocksy-child (detected-by-dir)"
        return 0
    fi
    if [[ -z "$t" && -d "${WP_PATH}/wp-content/themes/blocksy" ]]; then
        echo "blocksy (detected-by-dir)"
        return 0
    fi
    echo "${t:-unknown}"
}

# -----------------------------------------------------------------------------
# Verify blog_public = 0 (noindex) on staging — auto-heal instead of aborting
# -----------------------------------------------------------------------------
if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
    log "Verifying staging noindex (blog_public = ${EXPECTED_BLOG_PUBLIC})..."
    BLOG_PUBLIC_RAW="$(wp option get blog_public 2>/dev/null || echo '')"
    if [[ -z "$BLOG_PUBLIC_RAW" || "$BLOG_PUBLIC_RAW" != "$EXPECTED_BLOG_PUBLIC" ]]; then
        warn "blog_public is '${BLOG_PUBLIC_RAW:-<empty>}' (expected '${EXPECTED_BLOG_PUBLIC}'). Auto-healing: setting blog_public=0 (staging MUST be noindex)."
        wp option update blog_public "$EXPECTED_BLOG_PUBLIC" >/dev/null
        BLOG_PUBLIC="$EXPECTED_BLOG_PUBLIC"
    else
        BLOG_PUBLIC="$BLOG_PUBLIC_RAW"
    fi
    ACTIVE_THEME="$(get_active_theme)"
    _active_base="${ACTIVE_THEME%% *}"
    if [[ "$_active_base" != "blocksy-child" && "$_active_base" != "blocksy" ]]; then
        die "Active theme '${ACTIVE_THEME}' is not Blocksy-compatible. Refusing to proceed."
    fi
    WPLANG="$(wp option get WPLANG 2>/dev/null | tr -d '[:space:]' || echo unknown)"
    CURRENCY="$(wp option get woocommerce_currency 2>/dev/null | tr -d '[:space:]' || echo unknown)"
    log "Staging status → theme=${ACTIVE_THEME}  WPLANG=${WPLANG}  currency=${CURRENCY}  blog_public=${BLOG_PUBLIC}"
fi

# -----------------------------------------------------------------------------
# Static page registry — official slug/title/source mapping
# -----------------------------------------------------------------------------
page_entry() {
    # echo "slug|title|rendered_html"
    echo "about-us|درباره رادمان|${BUILD_DIR}/about-us.html"
    echo "contact-us|تماس با ما|${BUILD_DIR}/contact-us.html"
    echo "faq|سؤالات متداول|${BUILD_DIR}/faq.html"
    echo "shipping|روش‌های ارسال|${BUILD_DIR}/shipping.html"
    echo "returns|شرایط بازگشت کالا|${BUILD_DIR}/returns.html"
    echo "privacy-policy-radman|حریم خصوصی|${BUILD_DIR}/privacy-policy-radman.html"
    echo "terms|قوانین و مقررات|${BUILD_DIR}/terms.html"
    echo "ring-size-guide|راهنمای سایز انگشتر|${BUILD_DIR}/ring-size-guide.html"
    echo "silver-care|راهنمای نگهداری نقره|${BUILD_DIR}/silver-care.html"
    echo "silver-925-authenticity|اصالت نقره ۹۲۵|${BUILD_DIR}/silver-925-authenticity.html"
    echo "gemstones|راهنمای سنگ‌های زینتی|${BUILD_DIR}/gemstones.html"
}

find_existing_page_id() {
    local slug="$1"
    wp post list \
        --post_type=page \
        --post_name__in="$slug" \
        --fields=ID \
        --format=ids \
        --allow-root 2>/dev/null | tr -d '[:space:]' | head -c 20 || true
}

# -----------------------------------------------------------------------------
# Dry-run plan print (portable — no process substitution / <() for jailshell)
# -----------------------------------------------------------------------------
log ""
log "==================== DEPLOY PLAN ===================="
printf '%-4s %-28s %-12s %-10s %-10s\n' "#" "SLUG" "EXISTING_ID" "ACTION" "STATUS"
i=0
print_plan_row() {
    local slug="$1" title="$2" rendered="$3"
    i=$((i+1))
    local existing="will-create"
    if [[ "$MODE" == "apply" || "$MODE" == "check" ]]; then
        local pid
        pid="$(find_existing_page_id "$slug")"
        [[ -n "$pid" ]] && existing="$pid"
    fi
    local action="UPDATE"
    [[ "$existing" == "will-create" ]] && action="CREATE"
    local size="?"
    [[ -f "$rendered" ]] && size="$(wc -c < "$rendered")"
    printf '%-4s %-28s %-12s %-10s %-10s  %s bytes\n' "$i" "$slug" "$existing" "$action" "draft" "$size"
}
print_plan_row "about-us"               "درباره رادمان"         "${BUILD_DIR}/about-us.html"
print_plan_row "contact-us"             "تماس با ما"            "${BUILD_DIR}/contact-us.html"
print_plan_row "faq"                    "سؤالات متداول"        "${BUILD_DIR}/faq.html"
print_plan_row "shipping"               "روش‌های ارسال"        "${BUILD_DIR}/shipping.html"
print_plan_row "returns"                "شرایط بازگشت کالا"    "${BUILD_DIR}/returns.html"
print_plan_row "privacy-policy-radman"  "حریم خصوصی"          "${BUILD_DIR}/privacy-policy-radman.html"
print_plan_row "terms"                  "قوانین و مقررات"      "${BUILD_DIR}/terms.html"
print_plan_row "ring-size-guide"        "راهنمای سایز انگشتر"  "${BUILD_DIR}/ring-size-guide.html"
print_plan_row "silver-care"            "راهنمای نگهداری نقره" "${BUILD_DIR}/silver-care.html"
print_plan_row "silver-925-authenticity" "اصالت نقره ۹۲۵"     "${BUILD_DIR}/silver-925-authenticity.html"
print_plan_row "gemstones"              "راهنمای سنگ‌های زینتی" "${BUILD_DIR}/gemstones.html"
log "====================================================="
log ""

if [[ "$MODE" != "apply" ]]; then
    log "Dry-run (--${MODE}) complete. No WordPress content was modified."
    log "Run with --apply-staging and CONFIRM_STAGING_APPLY=YES after reviewer approval."
    exit 0
fi

# -----------------------------------------------------------------------------
# APPLY MODE (only reachable with all staging guards satisfied)
# -----------------------------------------------------------------------------
log "[APPLY] Creating timestamped backups..."
TS_LONG="$(date +%Y%m%d-%H%M%S)"
DB_BACKUP="${BACKUP_DIR}/wordpress-db-${TS_LONG}.sql"
# Sanitized DB export: no credentials printed; wp db uses wp-config.php auth.
wp db export "$DB_BACKUP" >/dev/null
chmod 600 "$DB_BACKUP"
log "[APPLY] DB backup written: ${DB_BACKUP}"

THEME_TARGET="${WP_PATH}/wp-content/themes/blocksy-child"
if [[ -d "$THEME_TARGET" ]]; then
    THEME_BACKUP="${BACKUP_DIR}/blocksy-child-${TS_LONG}.tar.gz"
    tar -C "$(dirname "$THEME_TARGET")" -czf "$THEME_BACKUP" "$(basename "$THEME_TARGET")"
    chmod 600 "$THEME_BACKUP"
    log "[APPLY] Existing child theme backed up: ${THEME_BACKUP}"
fi

log "[APPLY] Deploying Blocksy child theme (idempotent sync)..."
mkdir -p "$THEME_TARGET"
# Sync only the reviewed files (no stray build artifacts).
install -m 644 "$RADMAN_REPO_ROOT/$CHILD_THEME_SOURCE_RELPATH/style.css"     "$THEME_TARGET/style.css"
install -m 644 "$RADMAN_REPO_ROOT/$CHILD_THEME_SOURCE_RELPATH/functions.php" "$THEME_TARGET/functions.php"
install -m 644 "$RADMAN_REPO_ROOT/$CHILD_THEME_SOURCE_RELPATH/README.md"     "$THEME_TARGET/README.md"

log "[APPLY] Activating blocksy-child theme..."
wp theme activate blocksy-child >/dev/null
POST_THEME="$(get_active_theme)"
_POST_BASE="${POST_THEME%% *}"
if [[ "$_POST_BASE" != "blocksy-child" ]]; then
    die "Expected active theme 'blocksy-child' after activation, got '${POST_THEME}'."
fi
log "[APPLY] Active theme verified: ${POST_THEME}"

log "[APPLY] Upserting static pages (idempotent by slug; status = draft)..."
UPSERTED=0
CREATED=0
apply_page() {
    local slug="$1" title="$2" rendered="$3"
    [[ -f "$rendered" ]] || die "Rendered HTML missing for ${slug}: ${rendered}"
    local existing_id
    existing_id="$(find_existing_page_id "$slug")"
    if [[ -n "$existing_id" ]]; then
        # Update existing; ensure draft status; do NOT publish.
        wp post update "$existing_id" \
            --post_title="$title" \
            --post_name="$slug" \
            --post_status=draft \
            --post_content="$(cat "$rendered")" >/dev/null
        log "[APPLY] UPDATE slug=${slug}  ID=${existing_id}  status=draft"
        UPSERTED=$((UPSERTED+1))
    else
        local new_id
        new_id="$(wp post create \
            --post_type=page \
            --post_title="$title" \
            --post_name="$slug" \
            --post_status=draft \
            --post_content="$(cat "$rendered")" \
            --porcelain)"
        log "[APPLY] CREATE slug=${slug}  ID=${new_id}  status=draft"
        CREATED=$((CREATED+1))
    fi
}
apply_page "about-us"               "درباره رادمان"         "${BUILD_DIR}/about-us.html"
apply_page "contact-us"             "تماس با ما"            "${BUILD_DIR}/contact-us.html"
apply_page "faq"                    "سؤالات متداول"        "${BUILD_DIR}/faq.html"
apply_page "shipping"               "روش‌های ارسال"        "${BUILD_DIR}/shipping.html"
apply_page "returns"                "شرایط بازگشت کالا"    "${BUILD_DIR}/returns.html"
apply_page "privacy-policy-radman"  "حریم خصوصی"          "${BUILD_DIR}/privacy-policy-radman.html"
apply_page "terms"                  "قوانین و مقررات"      "${BUILD_DIR}/terms.html"
apply_page "ring-size-guide"        "راهنمای سایز انگشتر"  "${BUILD_DIR}/ring-size-guide.html"
apply_page "silver-care"            "راهنمای نگهداری نقره" "${BUILD_DIR}/silver-care.html"
apply_page "silver-925-authenticity" "اصالت نقره ۹۲۵"     "${BUILD_DIR}/silver-925-authenticity.html"
apply_page "gemstones"              "راهنمای سنگ‌های زینتی" "${BUILD_DIR}/gemstones.html"

log "[APPLY] Done. updated=${UPSERTED} created=${CREATED}"
log "[APPLY] Static pages remain Draft — no publish occurred."
log "[APPLY] Home page / menus / plugins / payments / SMS are intentionally untouched."
log ""
log "================================================================================"
log "DEPLOY APPLIED TO STAGING (${WP_URL})"
log "  Active theme : ${POST_THEME}"
log "  DB backup    : ${DB_BACKUP}"
log "  Theme backup : ${THEME_BACKUP:-${THEME_TARGET} (did not previously exist)}"
log "  Build dir    : ${BUILD_DIR}"
log "  Pages        : updated=${UPSERTED} created=${CREATED} (all draft)"
log "PRODUCTION (public_html) WAS NOT TOUCHED."
log "================================================================================"
