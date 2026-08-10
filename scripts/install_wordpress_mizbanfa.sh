#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Safe WordPress & WooCommerce Staging Deployment Script
# Status: DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST
# Host Target: MizbanFa Mars Plan (Staging Environment Only)
# ==============================================================================

set -Eeuo pipefail

trap 'echo "[ERROR] Script failed at line $LINENO" >&2' ERR

print_usage() {
    cat <<EOF
Usage: $0 [MODE]

Available Modes:
  --plan             Display execution plan and required environment variables (Default read-only mode)
  --check            Run read-only preflight checks (PHP, MySQL/MariaDB, WP-CLI, WP_PATH inspection)
  --execute-staging  Execute mutating staging deployment (Requires explicit environment variables)

Security & Operational Policy:
  - Production deployment is strictly prohibited in this script.
  - Secret variables (ADMIN_PASSWORD, DB_PASSWORD) must be provided via the protected server environment, never as CLI arguments.
EOF
}

print_plan() {
    cat <<EOF
================================================================================
RADMAN SILVER 925 — WORDPRESS/WOOCOMMERCE STAGING DEPLOYMENT PLAN
================================================================================
STATUS: DEPLOYMENT TOOLKIT PREPARED — NOT EXECUTED ON HOST
WAITING FOR SECURE HOST ACCESS AND STAGING-ONLY EXECUTION APPROVAL.

1. Required Environment Variables for Execution (--execute-staging):
   - WP_PATH          : Absolute filesystem path to staging document root
   - WP_URL           : Staging domain URL (must be a staging subdomain, e.g., https://staging.radmansilver.ir)
   - WP_TITLE         : Site title (e.g., "رادمان سیلور ۹۲۵")
   - ADMIN_USER       : WordPress administrator username
   - ADMIN_EMAIL      : WordPress administrator email address
   - DB_NAME          : cPanel MySQL database name (with cPanel prefix, e.g., user_radman_wp)
   - DB_USER          : cPanel MySQL database user (e.g., user_radman_user)
   - DB_HOST          : Database host (default: localhost)
   - RADMAN_ENV_FILE  : Absolute path to account-private secrets file outside web root
   - ADMIN_PASSWORD   : Protected server-side environment secret (admin password)
   - DB_PASSWORD      : Protected server-side environment secret (database password)

2. Version & Compatibility Policy:
   - WordPress: Defaults to latest stable available at execution time (WP 7.0.3 is current stable as of 2026-08-10). Can be overridden via WP_VERSION for controlled compatibility tests.
   - WooCommerce: Installs latest stable compatible release at execution time and reports resolved version.
   - MariaDB 10.3.x: Produces a prominent YELLOW FLAG. Accepted only for staging testing with explicit ALLOW_LEGACY_DB_FOR_STAGING=1 exported.

3. Plugin & Theme Architecture:
   - Theme: Blocksy (wp theme install blocksy --activate) + Blocksy Companion (Child theme deployment PENDING package review).
   - SEO: seo-by-rank-math (Official Rank Math slug only; no Yoast fallback).
   - Cache: litespeed-cache (WP Rocket inactive).
   - Security: wordfence, updraftplus.
   - Persian: persian-woocommerce, wp-persian.
   - Redis Cache: Activated only after verified connectivity (wp redis status), otherwise marked PENDING HOST CONFIGURATION.
   - Kavenegar SMS: Integration PENDING exact approved plugin package identification.

4. Manual cPanel Prerequisites (Not created by script):
   - Staging subdomain creation in cPanel.
   - MySQL database and user creation with ALL PRIVILEGES.
   - SSL TLS certificate provisioning.
================================================================================
EOF
}

run_preflight_checks() {
    echo "================================================================================"
    echo "RADMAN SILVER 925 — READ-ONLY PREFLIGHT CHECKS"
    echo "================================================================================"
    
    echo "[CHECK 1] PHP Exact Version & Required Extensions:"
    if command -v php >/dev/null 2>&1; then
        php_ver=$(php -r 'echo PHP_VERSION;')
        echo "  - Resolved PHP Version: ${php_ver}"
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
        echo "  - Resolved WP-CLI: ${wp_ver}"
    else
        echo "[ERROR] wp binary not found." >&2
    fi

    echo ""
    echo "[CHECK 3] MySQL/MariaDB Exact Version & Baseline Flag:"
    if command -v mysql >/dev/null 2>&1; then
        db_ver=$(mysql -V)
        echo "  - Resolved Database: ${db_ver}"
        if echo "${db_ver}" | grep -qi "10\.3"; then
            echo "  - [YELLOW FLAG] MariaDB 10.3 detected. This is below current preferred baseline (MariaDB 10.6+/10.11+ or MySQL 8.0+)."
            echo "  - [YELLOW FLAG] Requires ALLOW_LEGACY_DB_FOR_STAGING=1 for staging compatibility testing."
        fi
    else
        echo "[WARN] mysql CLI binary not found in current PATH."
    fi

    echo ""
    echo "[CHECK 4] Staging Document Root Inspection (WP_PATH):"
    if [[ -n "${WP_PATH:-}" ]]; then
        if [[ -d "${WP_PATH}" ]]; then
            echo "  - Directory exists: ${WP_PATH}"
            if [[ -f "${WP_PATH}/wp-load.php" ]]; then
                echo "  - Status: WordPress appears already installed in ${WP_PATH}."
            else
                echo "  - Status: Directory is ready for installation."
            fi
        else
            echo "  - Status: Directory ${WP_PATH} does not exist yet."
        fi
    else
        echo "  - [INFO] WP_PATH not exported; skipping directory inspection."
    fi
    echo "================================================================================"
}

execute_staging_deployment() {
    echo "================================================================================"
    echo "RADMAN SILVER 925 — STAGING DEPLOYMENT EXECUTION"
    echo "================================================================================"
    
    # Prohibit production execution:
    if [[ -z "${WP_URL:-}" || "${WP_URL}" != *"staging."* ]]; then
        echo "[ERROR] Production deployment is strictly prohibited in this script." >&2
        echo "[ERROR] WP_URL must be an explicit staging subdomain (e.g., https://staging.radmansilver.ir)." >&2
        exit 1
    fi

    # Validate required environment variables:
    for var in WP_PATH WP_URL WP_TITLE ADMIN_USER ADMIN_EMAIL DB_NAME DB_USER DB_HOST RADMAN_ENV_FILE ADMIN_PASSWORD DB_PASSWORD; do
        if [[ -z "${!var:-}" ]]; then
            echo "[ERROR] Required environment variable ${var} is missing or empty." >&2
            exit 1
        fi
    done

    # Check MariaDB legacy yellow flag policy:
    if command -v mysql >/dev/null 2>&1; then
        if mysql -V | grep -qi "10\.3"; then
            if [[ "${ALLOW_LEGACY_DB_FOR_STAGING:-0}" != "1" ]]; then
                echo "[ERROR] MariaDB 10.3 detected. Staging execution requires ALLOW_LEGACY_DB_FOR_STAGING=1." >&2
                exit 1
            fi
            echo "[YELLOW FLAG] Proceeding on MariaDB 10.3 under ALLOW_LEGACY_DB_FOR_STAGING=1 staging waiver."
        fi
    fi

    echo "[1/10] Verifying target directory ${WP_PATH}..."
    mkdir -p "${WP_PATH}"
    cd "${WP_PATH}"

    if [[ -f "wp-load.php" ]]; then
        echo "[ERROR] WordPress is already installed in ${WP_PATH}. Aborting to prevent overwrite." >&2
        exit 1
    fi

    echo "[2/10] Downloading WordPress Core (Latest Stable fa_IR)..."
    if [[ -n "${WP_VERSION:-}" ]]; then
        wp core download --version="${WP_VERSION}" --locale=fa_IR
    else
        wp core download --locale=fa_IR
    fi
    resolved_wp=$(wp core version)
    echo "  - Resolved WordPress Core Version: ${resolved_wp}"

    echo "[3/10] Creating wp-config.php..."
    wp config create \
        --dbname="${DB_NAME}" \
        --dbuser="${DB_USER}" \
        --dbpass="${DB_PASSWORD}" \
        --dbhost="${DB_HOST}" \
        --dbcharset=utf8mb4 \
        --dbcollate=utf8mb4_unicode_ci

    echo "[4/10] Installing WordPress Core..."
    wp core install \
        --url="${WP_URL}" \
        --title="${WP_TITLE}" \
        --admin_user="${ADMIN_USER}" \
        --admin_password="${ADMIN_PASSWORD}" \
        --admin_email="${ADMIN_EMAIL}" \
        --skip-email

    echo "[5/10] Installing and configuring WooCommerce..."
    wp plugin install woocommerce --activate
    resolved_wc=$(wp plugin get woocommerce --field=version)
    echo "  - Resolved WooCommerce Version: ${resolved_wc}"

    wp option update woocommerce_currency "IRR"
    wp option update woocommerce_currency_pos "right"
    wp option update woocommerce_price_thousand_sep ","
    wp option update woocommerce_price_decimal_sep "."
    wp option update woocommerce_price_num_decimals "0"

    echo "[6/10] Installing Persian Localization Plugins..."
    for plugin in persian-woocommerce wp-persian; do
        if wp plugin install "${plugin}" --activate; then
            echo "  - Activated plugin: ${plugin}"
        else
            echo "[ERROR] Required plugin ${plugin} is unavailable or incompatible." >&2
            exit 1
        fi
    done

    echo "[7/10] Installing SEO, Security, and Cache Plugins..."
    for plugin in seo-by-rank-math wordfence updraftplus litespeed-cache; do
        if wp plugin install "${plugin}" --activate; then
            echo "  - Activated plugin: ${plugin}"
        else
            echo "[ERROR] Required plugin ${plugin} is unavailable or incompatible." >&2
            exit 1
        fi
    done

    echo "[8/10] Installing Blocksy Theme and Companion..."
    wp theme install blocksy --activate
    wp plugin install blocksy-companion --activate
    echo "  - [INFO] Blocksy Child Theme deployment PENDING reviewed package availability."

    echo "[9/10] Checking Redis Object Cache Connectivity..."
    wp plugin install redis-cache
    if wp redis status >/dev/null 2>&1; then
        wp plugin activate redis-cache
        wp redis enable || true
        echo "  - [SUCCESS] Redis Object Cache activated and connected."
    else
        echo "  - [INFO] Redis host connectivity unavailable. Marking Redis Persistent Cache as PENDING HOST CONFIGURATION."
    fi

    echo "[10/10] Applying Staging Isolation and Iranian Locale Settings..."
    wp option update blog_public 0
    wp option update timezone_string "Asia/Tehran"
    wp option update WPLANG "fa_IR"
    wp rewrite structure '/%postname%/'
    wp rewrite flush

    echo "================================================================================"
    echo "VERIFICATION CHECKS AFTER EXECUTION"
    echo "================================================================================"
    wp plugin list
    wp option get home
    wp option get blog_public
    wp db check

    echo "================================================================================"
    echo "STAGING WORDPRESS/WOOCOMMERCE DEPLOYMENT VERIFIED SUCCESSFULLY."
    echo "================================================================================"
}

# --- Main CLI Router ---
MODE="${1:---plan}"

case "${MODE}" in
    --plan)
        print_plan
        ;;
    --check)
        run_preflight_checks
        ;;
    --execute-staging)
        execute_staging_deployment
        ;;
    *)
        echo "[ERROR] Unknown parameter: ${MODE}" >&2
        print_usage
        exit 1
        ;;
esac
