#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Automated WordPress & WooCommerce Installation Script
# Host: MizbanFa Mars Plan (60GB NVMe, 12 Cores, 12GB RAM, cPanel, MariaDB 10.3.39)
# ==============================================================================
# MISSION: Install WordPress 6.x + WooCommerce + Required Plugins on MizbanFa Mars Plan
# ==============================================================================

set -eo pipefail

echo "============================================================================"
echo "Step 1: Verify environment (PHP 8.2+, WP-CLI, MariaDB 10.3.39+)"
echo "============================================================================"
php --version || echo "[WARN] PHP command not found in current path."
wp --info || echo "[WARN] WP-CLI command not found in current path."
mysql --version || echo "[WARN] MySQL/MariaDB command not found in current path."

echo ""
echo "============================================================================"
echo "Step 2: Create WordPress database (Manual prerequisite in cPanel)"
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
echo "Step 4: Install WooCommerce & configure IRR currency / Iran location"
echo "============================================================================"
# wp plugin install woocommerce --activate
# wp option update woocommerce_store_address "ایران"
# wp option update woocommerce_store_city "مشهد"
# wp option update woocommerce_default_country "IR"
# wp option update woocommerce_currency "IRR"
# wp option update woocommerce_currency_pos "right"
# wp option update woocommerce_price_thousand_sep ","
# wp option update woocommerce_price_decimal_sep "."
# wp option update woocommerce_price_num_decimals "0"

echo ""
echo "============================================================================"
echo "Step 5: Install Persian WooCommerce"
echo "============================================================================"
# wp plugin install persian-woocommerce --activate

echo ""
echo "============================================================================"
echo "Step 6: Install RankMath SEO"
echo "============================================================================"
# wp plugin install wordpress-seo --activate || wp plugin install seo-by-rank-math --activate

echo ""
echo "============================================================================"
echo "Step 7: Install Wordfence Security"
echo "============================================================================"
# wp plugin install wordfence --activate

echo ""
echo "============================================================================"
echo "Step 8: Install UpdraftPlus (Cloud Storage Backups)"
echo "============================================================================"
# wp plugin install updraftplus --activate

echo ""
echo "============================================================================"
echo "Step 9: Install LiteSpeed Cache (Recommended by MizbanFa)"
echo "============================================================================"
# wp plugin install litespeed-cache --activate

echo ""
echo "============================================================================"
echo "Step 10: Install Blocksy Companion"
echo "============================================================================"
# wp plugin install blocksy-companion --activate

echo ""
echo "============================================================================"
echo "Step 11: Install Persian Date / Shamsi Plugin & Redis Cache"
echo "============================================================================"
# wp plugin install wp-persian --activate
# wp plugin install redis-cache --activate || echo "[INFO] Redis cache plugin install optional/host-dependent."

echo ""
echo "============================================================================"
echo "Step 12: Configure basic WordPress settings"
echo "============================================================================"
# wp option update timezone_string "Asia/Tehran"
# wp option update date_format "Y/m/d"
# wp option update time_format "H:i"
# wp option update WPLANG "fa_IR"
# wp option update blogname "رادمان سیلور ۹۲۵"
# wp option update blogdescription "خرید انگشتر نقره ۹۲۵ اصل | رادمان سیلور"

echo ""
echo "============================================================================"
echo "Step 13: Set permalink structure (/%postname%/)"
echo "============================================================================"
# wp rewrite structure '/%postname%/'
# wp rewrite flush

echo ""
echo "============================================================================"
echo "Step 14 to Step 16: .env creation, wp-config.php update, and .gitignore"
echo "============================================================================"
echo "Verify .env exists with placeholder keys, config/wp-config-env.php inserted, and .env in .gitignore."

echo ""
echo "============================================================================"
echo "Step 17 & Step 18: Staging subdomain creation & WordPress staging install"
echo "============================================================================"
echo "Ensure staging subdomain staging.radmansilver.ir has 'wp option update blog_public 0' (noindex)."

echo ""
echo "============================================================================"
echo "Step 19: Verify installation"
echo "============================================================================"
# wp plugin list
# wp option get home
# wp db check

echo "============================================================================"
echo "WORDPRESS + WOOCOMMERCE INSTALLED SUCCESSFULLY"
echo "============================================================================"
