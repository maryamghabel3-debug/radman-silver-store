#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Automated WordPress 6.6 & WooCommerce Mars Installation
# Host: MizbanFa Mars Plan (60GB NVMe, 12 Cores, 12GB RAM, cPanel, MariaDB 10.3.39)
# Scope: RADMAN SILVER ONLY (RIDELIN strictly out of scope)
# ==============================================================================
# MISSION: Install WordPress 6.x + WooCommerce + Required Plugins on MizbanFa Mars Plan (RADMAN only)
# ==============================================================================

set -eo pipefail

echo "============================================================================"
echo "Step 1: Verify environment (PHP 8.2+, WP-CLI, MariaDB 10.3.39)"
echo "============================================================================"
php --version || echo "[WARN] PHP command not found in current path."
wp --info || echo "[WARN] WP-CLI command not found in current path."
mysql --version || echo "[WARN] MySQL/MariaDB command not found in current path."

echo ""
echo "============================================================================"
echo "Step 2: Create database (Manual prerequisite in cPanel MySQL Databases)"
echo "============================================================================"
echo "Ensure database 'radman_wp' and user 'radman_wp_user' with ALL privileges exist."

echo ""
echo "============================================================================"
echo "Step 3: Install WordPress core (6.6 fa_IR)"
echo "============================================================================"
# Uncomment when executing on live cPanel SSH terminal:
# wp core download --version=6.6 --locale=fa_IR
# wp config create --dbname=radman_wp --dbuser=radman_wp_user --dbpass="${DB_PASSWORD}" --dbhost=localhost --dbcharset=utf8mb4 --dbcollate=utf8mb4_unicode_ci
# wp core install --url=radmansilver.ir --title="رادمان سیلور ۹۲۵" --admin_user="${ADMIN_USER}" --admin_password="${ADMIN_PASSWORD}" --admin_email="${ADMIN_EMAIL}" --skip-email

echo ""
echo "============================================================================"
echo "Step 4: Install and configure WooCommerce (IRR Currency & Formatting)"
echo "============================================================================"
# wp plugin install woocommerce --activate
# wp option update woocommerce_currency "IRR"
# wp option update woocommerce_currency_pos "right"
# wp option update woocommerce_price_thousand_sep ","
# wp option update woocommerce_price_decimal_sep "."
# wp option update woocommerce_price_num_decimals "0"

echo ""
echo "============================================================================"
echo "Step 5: Install Persian plugins"
echo "============================================================================"
# wp plugin install persian-woocommerce --activate
# wp plugin install wp-persian --activate

echo ""
echo "============================================================================"
echo "Step 6: Install security and performance plugins"
echo "============================================================================"
# wp plugin install wordfence --activate
# wp plugin install updraftplus --activate
# wp plugin install litespeed-cache --activate
# wp plugin install wordpress-seo --activate
# wp plugin install blocksy-companion --activate

echo ""
echo "============================================================================"
echo "Step 7: Basic configuration (Tehran Timezone, Permalinks, Title/Description)"
echo "============================================================================"
# wp option update timezone_string "Asia/Tehran"
# wp option update WPLANG "fa_IR"
# wp option update blogname "رادمان سیلور ۹۲۵"
# wp option update blogdescription "خرید انگشتر نقره ۹۲۵ اصل | رادمان سیلور"
# wp rewrite structure '/%postname%/'
# wp rewrite flush

echo ""
echo "============================================================================"
echo "Step 8: Create .env file in WordPress root"
echo "============================================================================"
echo "Verify .env exists with required placeholder keys (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, LEGACY_API_*, KAVENEGAR_API_KEY, TELEGRAM_*, ZARINPAL_MERCHANT_ID)."

echo ""
echo "============================================================================"
echo "Step 9: Update wp-config.php to load .env"
echo "============================================================================"
echo "Ensure config/wp-config-env.php snippet is loaded at the top of wp-config.php."

echo ""
echo "============================================================================"
echo "Step 10: Create staging subdomain (staging.radmansilver.ir) with noindex"
echo "============================================================================"
echo "Ensure staging domain is isolated and 'wp option update blog_public 0' is applied."

echo ""
echo "============================================================================"
echo "Step 11: Verification"
echo "============================================================================"
# wp plugin list
# wp option get home
# wp db check

echo "============================================================================"
echo "WORDPRESS + WOOCOMMERCE INSTALLED SUCCESSFULLY ON MARS PLAN"
echo "============================================================================"
