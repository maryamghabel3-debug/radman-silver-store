#!/bin/sh
# RADMAN PR-35 — staging-only child-theme UI deploy and rollback.
# Presentation files only: functions.php enqueue + assets/radman-product-ui.css.
set -eu

EXPECTED_APP_ENV='staging'
EXPECTED_WP_URL='https://staging.radmansilver.ir'
EXPECTED_WP_PATH='/home/radmansi/staging.radmansilver.ir'
MODE=''

usage() {
    cat <<'USAGE'
Usage:
  sh theme/blocksy-child/deploy-luxury-product-ui.sh --apply
  sh theme/blocksy-child/deploy-luxury-product-ui.sh --rollback-latest

Required environment:
  APP_ENV=staging
  WP_URL=https://staging.radmansilver.ir
  WP_PATH=/home/radmansi/staging.radmansilver.ir
  RADMAN_PRIVATE_DIR=/home/radmansi/.config/radman
  CONFIRM_STAGING_APPLY=YES
USAGE
}

fail() {
    printf '[ERROR] %s\n' "$*" >&2
    exit 2
}

log() {
    printf '%s\n' "$*"
}

[ "$#" -eq 1 ] || { usage >&2; exit 2; }
case "$1" in
    --apply) MODE='apply' ;;
    --rollback-latest) MODE='rollback' ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

: "${APP_ENV:=}"
: "${WP_URL:=}"
: "${WP_PATH:=}"
: "${RADMAN_PRIVATE_DIR:=}"
: "${CONFIRM_STAGING_APPLY:=}"

[ "$APP_ENV" = "$EXPECTED_APP_ENV" ] || fail 'APP_ENV must equal staging'
[ "$WP_URL" = "$EXPECTED_WP_URL" ] || fail "WP_URL must equal $EXPECTED_WP_URL"
[ "$WP_PATH" = "$EXPECTED_WP_PATH" ] || fail "WP_PATH must equal $EXPECTED_WP_PATH"
[ "$CONFIRM_STAGING_APPLY" = 'YES' ] || fail 'CONFIRM_STAGING_APPLY must equal YES'
case "$WP_PATH" in
    *public_html*) fail 'public_html is prohibited' ;;
esac
case "$RADMAN_PRIVATE_DIR" in
    /*) ;;
    *) fail 'RADMAN_PRIVATE_DIR must be an absolute private path' ;;
esac
case "$RADMAN_PRIVATE_DIR" in
    *public_html*) fail 'RADMAN_PRIVATE_DIR cannot be under public_html' ;;
esac

for command_name in wp tar cp chmod mkdir mv cmp grep sed date dirname basename; do
    command -v "$command_name" >/dev/null 2>&1 || fail "required command missing: $command_name"
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE_FUNCTIONS="$SCRIPT_DIR/functions.php"
SOURCE_PRODUCT_CSS="$SCRIPT_DIR/assets/radman-product-ui.css"
THEME_PARENT="$WP_PATH/wp-content/themes"
THEME_TARGET="$THEME_PARENT/blocksy-child"
TARGET_FUNCTIONS="$THEME_TARGET/functions.php"
TARGET_PRODUCT_CSS="$THEME_TARGET/assets/radman-product-ui.css"
BACKUP_DIR="$RADMAN_PRIVATE_DIR/backups"
LATEST_POINTER="$BACKUP_DIR/blocksy-child-luxury-ui.latest"
TS=$(date -u +%Y%m%dT%H%M%SZ)

[ -s "$SOURCE_FUNCTIONS" ] || fail "source functions.php missing: $SOURCE_FUNCTIONS"
[ -s "$SOURCE_PRODUCT_CSS" ] || fail "source product UI CSS missing: $SOURCE_PRODUCT_CSS"
[ -d "$THEME_TARGET" ] || fail "existing child theme missing: $THEME_TARGET"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

ACTIVE_THEME=$(wp --path="$WP_PATH" --no-color option get stylesheet 2>/dev/null || true)
[ "$ACTIVE_THEME" = 'blocksy-child' ] || fail "active stylesheet is '$ACTIVE_THEME', expected blocksy-child"

flush_caches() {
    wp --path="$WP_PATH" --no-color cache flush >/dev/null 2>&1 \
        || log '[WARN] Object-cache flush reported an issue.'
    wp --path="$WP_PATH" --no-color litespeed-purge all >/dev/null 2>&1 \
        || log '[INFO] LiteSpeed purge unavailable or non-fatal.'
}

backup_theme() {
    label=$1
    archive="$BACKUP_DIR/blocksy-child-$label-$TS.tar.gz"
    if [ -e "$archive" ]; then
        archive="$BACKUP_DIR/blocksy-child-$label-$TS-$$.tar.gz"
    fi
    tar -C "$THEME_PARENT" -czf "$archive" "$(basename "$THEME_TARGET")"
    chmod 600 "$archive"
    printf '%s\n' "$archive"
}

if [ "$MODE" = 'apply' ]; then
    BACKUP_ARCHIVE=$(backup_theme 'pre-luxury-ui')
    printf '%s\n' "$BACKUP_ARCHIVE" > "$LATEST_POINTER"
    chmod 600 "$LATEST_POINTER"
    log "[BACKUP] $BACKUP_ARCHIVE"

    mkdir -p "$THEME_TARGET/assets"
    cp "$SOURCE_FUNCTIONS" "$TARGET_FUNCTIONS.tmp"
    cp "$SOURCE_PRODUCT_CSS" "$TARGET_PRODUCT_CSS.tmp"
    chmod 644 "$TARGET_FUNCTIONS.tmp" "$TARGET_PRODUCT_CSS.tmp"
    mv "$TARGET_FUNCTIONS.tmp" "$TARGET_FUNCTIONS"
    mv "$TARGET_PRODUCT_CSS.tmp" "$TARGET_PRODUCT_CSS"

    cmp -s "$SOURCE_FUNCTIONS" "$TARGET_FUNCTIONS" \
        || fail 'functions.php verification failed after copy'
    cmp -s "$SOURCE_PRODUCT_CSS" "$TARGET_PRODUCT_CSS" \
        || fail 'product UI CSS verification failed after copy'
    grep -q "'radman-product-ui'" "$TARGET_FUNCTIONS" \
        || fail 'product UI enqueue handle missing after deploy'

    flush_caches

    cat <<CHECKLIST
======================================================================
 RADMAN LUXURY PRODUCT UI — STAGING APPLY COMPLETE
 Backup: $BACKUP_ARCHIVE
 ---------------------------------------------------------------------
 Visual verification checklist:
 [ ] Shop/category cards: 3 desktop, 2 tablet, 1 mobile
 [ ] Card hover: subtle gold border and image zoom
 [ ] Single product: framed gallery, ivory title, gold single price
 [ ] Mobile add-to-cart: full width and sticky within product summary
 [ ] Trust strip: 925 / expert confirmation / size guide
 [ ] Description/spec rows and tabs: dark with gold active state
 [ ] Cart and mini-cart: dark/ivory/gold, checkout flow unchanged
 [ ] Keyboard focus ring visible; RTL spacing correct
 [ ] No product, price, stock, category, media, or status data changed
======================================================================
CHECKLIST
    exit 0
fi

[ -s "$LATEST_POINTER" ] || fail "latest backup pointer missing: $LATEST_POINTER"
BACKUP_ARCHIVE=$(sed -n '1p' "$LATEST_POINTER")
case "$BACKUP_ARCHIVE" in
    "$BACKUP_DIR"/*) ;;
    *) fail 'backup pointer resolves outside RADMAN_PRIVATE_DIR/backups' ;;
esac
[ -f "$BACKUP_ARCHIVE" ] || fail "backup archive missing: $BACKUP_ARCHIVE"

PRE_ROLLBACK_ARCHIVE=$(backup_theme 'pre-rollback')
MOVED_THEME="$BACKUP_DIR/blocksy-child-replaced-$TS"
if [ -e "$MOVED_THEME" ]; then
    MOVED_THEME="$BACKUP_DIR/blocksy-child-replaced-$TS-$$"
fi
mv "$THEME_TARGET" "$MOVED_THEME"
if ! tar -C "$THEME_PARENT" -xzf "$BACKUP_ARCHIVE"; then
    mv "$MOVED_THEME" "$THEME_TARGET"
    fail 'rollback extraction failed; pre-rollback theme restored'
fi
[ -s "$THEME_TARGET/functions.php" ] || {
    mv "$THEME_TARGET" "$BACKUP_DIR/blocksy-child-invalid-restore-$TS"
    mv "$MOVED_THEME" "$THEME_TARGET"
    fail 'restored archive did not contain a valid child theme'
}

flush_caches

cat <<ROLLBACK
======================================================================
 RADMAN LUXURY PRODUCT UI — ROLLBACK COMPLETE
 Restored: $BACKUP_ARCHIVE
 Pre-rollback archive: $PRE_ROLLBACK_ARCHIVE
 Replaced theme retained privately: $MOVED_THEME
 ---------------------------------------------------------------------
 [ ] Confirm blocksy-child remains active
 [ ] Open shop, one product and cart in an incognito window
 [ ] Confirm prior visual state is restored
======================================================================
ROLLBACK
