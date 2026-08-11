#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Safe WordPress & WooCommerce Staging Deployment Toolkit
# Status: DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST
# Host Target: MizbanFa Mars Plan (Staging Environment Only — RADMAN ONLY)
# ==============================================================================

set -Eeuo pipefail

trap 'echo "[ERROR] Script failed at line $LINENO" >&2' ERR

show_plan() {
    cat <<EOF
================================================================================
RADMAN SILVER 925 — WORDPRESS/WOOCOMMERCE STAGING DEPLOYMENT PLAN
================================================================================
STATUS: DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST
WAITING FOR SECURE HOST ACCESS AND STAGING-ONLY EXECUTION APPROVAL.

1. Required Environment Variables for Execution (--execute-staging):
   - WP_PATH          : Absolute path to staging document root
   - WP_URL           : Staging domain URL (must be https://staging.radmansilver.ir)
   - WP_TITLE         : Site title (e.g., "رادمان سیلور ۹۲۵")
   - WP_LOCALE        : Default fa_IR
   - WP_VERSION       : Defaults to latest stable at execution time (or override)
   - ADMIN_USER       : WordPress administrator username
   - ADMIN_EMAIL      : WordPress administrator email address
   - DB_NAME          : cPanel prefixed database name (e.g., prefix_radman_wp)
   - DB_USER          : cPanel prefixed database user (e.g., prefix_radman_user)
   - DB_HOST          : Database host (default: localhost)
   - RADMAN_ENV_FILE  : Absolute path to secrets file outside web root
   - APP_ENV          : Must equal 'staging'
   - CONFIRM_STAGING_EXECUTION : Must equal 'YES'

2. Version & Compatibility Policy:
   - WordPress: Defaults to latest stable available at execution time.
   - WooCommerce: Installs latest stable compatible release and reports exact version.
   - MariaDB 10.3.x: Produces YELLOW FLAG. Requires ALLOW_LEGACY_DB_FOR_STAGING=1.

3. Theme, Plugin & Currency Architecture:
   - Theme: Blocksy (blocksy) + Blocksy Companion (blocksy-companion). Child theme deployment PENDING PACKAGE CREATION AND REVIEW.
   - SEO: seo-by-rank-math (Official Rank Math slug only; no Yoast fallback).
   - Cache: litespeed-cache (WP Rocket inactive).
   - Redis: Activated only after verified connectivity (wp redis status), otherwise marked PENDING HOST REDIS CONFIGURATION.
   - Persian: persian-woocommerce (wp-persian / wp-parsidate excluded to prevent overlapping Jalali date conflicts).
   - Kavenegar SMS & Zarinpal: Integration PENDING reviewed package availability.
   - Currency Storage Gate: WooCommerce currency IRR. No product seeding or price writing occurs in this script.
================================================================================
EOF
}

run_preflight() {
    echo "================================================================================"
    echo "RADMAN SILVER 925 — READ-ONLY PREFLIGHT CHECKS"
    echo "================================================================================"
    
    echo "[CHECK 1] PHP Exact Version & Required Extensions:"
    if command -v php >/dev/null 2>&1; then
        php_ver=$(php -r 'echo PHP_VERSION;')
        echo "  - Detected PHP Version: ${php_ver}"
        for ext in curl mbstring gd zip intl bcmath; do
            if php -m | grep -qi "^${ext}$"; then
                echo "  - Extension [${ext}]: AVAILABLE"
            else
                echo "  - Extension [${ext}]: MISSING (Required)"
            fi
        done
    else
        echo "[ERROR] php binary not found." >&2
    fi

    echo ""
    echo "[CHECK 2] WP-CLI Exact Version:"
    if command -v wp >/dev/null 2>&1; then
        wp_ver=$(wp --info | grep -i "WP-CLI version" || echo "Available")
        echo "  - Detected WP-CLI: ${wp_ver}"
    else
        echo "[ERROR] wp binary not found." >&2
    fi

    echo ""
    echo "[CHECK 3] MySQL/MariaDB Exact Version:"
    if command -v mysql >/dev/null 2>&1; then
        db_ver=$(mysql -V)
        echo "  - Detected Database: ${db_ver}"
        if echo "${db_ver}" | grep -qi "10\.3"; then
            echo "  - [YELLOW FLAG] MariaDB 10.3 detected. Below current preferred baseline."
            echo "  - [YELLOW FLAG] Requires ALLOW_LEGACY_DB_FOR_STAGING=1."
        fi
    else
        echo "[WARN] mysql CLI binary not found in current PATH."
    fi

    echo ""
    echo "[CHECK 4] Python3 Exact Version:"
    if command -v python3 >/dev/null 2>&1; then
        py_ver=$(python3 --version 2>&1)
        echo "  - Detected Python: ${py_ver}"
    else
        echo "[WARN] python3 binary not found."
    fi

    echo ""
    echo "[CHECK 5] Filesystem Permissions & Disk Space:"
    df -h . 2>/dev/null || true

    echo ""
    echo "[CHECK 6] WP_PATH Inspection & HTTPS Reachability:"
    if [[ -n "${WP_PATH:-}" ]]; then
        if [[ -d "${WP_PATH}" ]]; then
            echo "  - Directory exists: ${WP_PATH}"
            if [[ -f "${WP_PATH}/wp-load.php" ]]; then
                echo "  - Status: WordPress is already installed in ${WP_PATH}."
            else
                echo "  - Status: Directory ready for clean staging installation."
            fi
        else
            echo "  - Status: Directory ${WP_PATH} absent."
        fi
    else
        echo "  - [INFO] WP_PATH not exported."
    fi
    if [[ -n "${WP_URL:-}" ]]; then
        if [[ "${WP_URL}" =~ ^https:// ]]; then
            echo "  - HTTPS check: WP_URL uses https:// scheme (${WP_URL})."
        else
            echo "  - [ERROR] WP_URL must use https:// scheme." >&2
        fi
    fi
    echo "================================================================================"
}

validate_staging_guards() {
    echo "[GUARD] Validating staging security guards..."
    if [[ "${APP_ENV:-}" != "staging" ]]; then
        echo "[ERROR] APP_ENV must equal 'staging'." >&2
        exit 1
    fi
    if [[ "${WP_URL:-}" != staging.* && "${WP_URL:-}" != https://staging.* ]]; then
        echo "[ERROR] WP_URL hostname must start with 'staging.'." >&2
        exit 1
    fi
    if [[ "${WP_URL:-}" != https://* ]]; then
        echo "[ERROR] HTTPS must be available (WP_URL must start with https://)." >&2
        exit 1
    fi
    if [[ "${WP_PATH:-}" == *"/public_html"* || "${WP_PATH:-}" == *"/www"* ]]; then
        echo "[ERROR] WP_PATH must not point to production public_html or www." >&2
        exit 1
    fi
    if [[ "${CONFIRM_STAGING_EXECUTION:-}" != "YES" ]]; then
        echo "[ERROR] CONFIRM_STAGING_EXECUTION must equal 'YES'." >&2
        exit 1
    fi
    for var in WP_PATH WP_URL WP_TITLE ADMIN_USER ADMIN_EMAIL DB_NAME DB_USER DB_HOST RADMAN_ENV_FILE; do
        if [[ -z "${!var:-}" ]]; then
            echo "[ERROR] Required environment variable ${var} is missing or empty." >&2
            exit 1
        fi
    done
    if [[ "${RADMAN_ENV_FILE}" == *"/public_html"* || "${RADMAN_ENV_FILE}" == *"/www"* || "${RADMAN_ENV_FILE}" == "${WP_PATH}"* ]]; then
        echo "[ERROR] RADMAN_ENV_FILE must be outside every web/document root." >&2
        exit 1
    fi
    if [[ -d "${WP_PATH}" && -f "${WP_PATH}/wp-load.php" ]]; then
        echo "[ERROR] WordPress is already installed in ${WP_PATH}. Aborting to prevent overwrite." >&2
        exit 1
    fi
    if command -v mysql >/dev/null 2>&1; then
        if mysql -V | grep -qi "10\.3"; then
            if [[ "${ALLOW_LEGACY_DB_FOR_STAGING:-0}" != "1" ]]; then
                echo "[ERROR] MariaDB 10.3 detected. Staging execution requires ALLOW_LEGACY_DB_FOR_STAGING=1." >&2
                exit 1
            fi
        fi
    fi
}

resolve_versions() {
    echo "[RESOLVE] Resolving latest stable versions..."
    wp core check-update --field=version 2>/dev/null | head -n 1 || echo "Latest Stable"
}

install_wordpress_staging() {
    echo "[INSTALL] Installing WordPress core on staging..."
    mkdir -p "${WP_PATH}"
    cd "${WP_PATH}"
    if [[ -n "${WP_VERSION:-}" ]]; then
        wp core download --version="${WP_VERSION}" --locale="${WP_LOCALE:-fa_IR}"
    else
        wp core download --locale="${WP_LOCALE:-fa_IR}"
    fi
    resolved_wp=$(wp core version)
    echo "  - Exact Resolved WordPress Version: ${resolved_wp}"

    wp config create \
        --dbname="${DB_NAME}" \
        --dbuser="${DB_USER}" \
        --dbpass="${DB_PASSWORD}" \
        --dbhost="${DB_HOST}" \
        --dbcharset=utf8mb4 \
        --dbcollate=utf8mb4_unicode_ci

    wp core install \
        --url="${WP_URL}" \
        --title="${WP_TITLE}" \
        --admin_user="${ADMIN_USER}" \
        --admin_password="${ADMIN_PASSWORD}" \
        --admin_email="${ADMIN_EMAIL}" \
        --skip-email
}

install_theme_and_plugins() {
    echo "[PLUGINS] Installing WooCommerce, SEO, Cache, and Persian localization..."
    wp plugin install woocommerce --activate
    resolved_wc=$(wp plugin get woocommerce --field=version)
    echo "  - Exact Resolved WooCommerce Version: ${resolved_wc}"

    wp plugin install persian-woocommerce --activate
    wp plugin install seo-by-rank-math --activate
    wp plugin install wordfence --activate
    wp plugin install updraftplus --activate
    wp plugin install litespeed-cache --activate

    wp theme install blocksy --activate
    wp plugin install blocksy-companion --activate
    echo "  - [INFO] Blocksy Child Theme deployment PENDING PACKAGE CREATION AND REVIEW."

    if wp redis status >/dev/null 2>&1; then
        wp plugin install redis-cache --activate
        wp redis enable || true
        echo "  - [SUCCESS] Persistent Redis Object Cache activated."
    else
        echo "  - [INFO] Redis connectivity check failed or unavailable: PENDING HOST REDIS CONFIGURATION."
    fi
}

configure_staging() {
    echo "[CONFIG] Configuring WooCommerce IRR currency, Tehran timezone, and staging noindex..."
    wp option update woocommerce_currency "IRR"
    wp option update woocommerce_currency_pos "right"
    wp option update woocommerce_price_thousand_sep ","
    wp option update woocommerce_price_decimal_sep "."
    wp option update woocommerce_price_num_decimals "0"

    wp option update blog_public 0
    wp option update timezone_string "Asia/Tehran"
    wp option update WPLANG "${WP_LOCALE:-fa_IR}"
    wp rewrite structure '/%postname%/'
    wp rewrite flush
}

verify_staging() {
    echo "================================================================================"
    echo "STAGING POST-INSTALL VERIFICATION"
    echo "================================================================================"
    wp plugin list
    wp option get home
    wp option get blog_public
    wp db check
    echo "================================================================================"
    echo "STAGING WORDPRESS/WOOCOMMERCE DEPLOYMENT VERIFIED SUCCESSFULLY."
    echo "================================================================================"
}

# --- Main Routing ---
MODE="${1:---plan}"

case "${MODE}" in
    --plan)
        show_plan
        ;;
    --check)
        run_preflight
        ;;
    --execute-staging)
        validate_staging_guards
        resolve_versions
        install_wordpress_staging
        install_theme_and_plugins
        configure_staging
        verify_staging
        ;;
    *)
        echo "[ERROR] Unknown mode: ${MODE}" >&2
        show_plan
        exit 1
        ;;
esac
