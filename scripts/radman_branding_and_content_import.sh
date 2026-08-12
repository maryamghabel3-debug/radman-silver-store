#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Branding, Child Theme, and Static Content Import (v2)
# Host Target: MizbanFa Mars Plan Staging (/home/radmansi/staging.radmansilver.ir)
# Scope: RADMAN SILVER ONLY (RIDELIN strictly out of scope)
# Currency Safety Gate: CLOSED (Toman direct input verified as correct)
# ==============================================================================
# MISSION: PR-12 / RADMAN Branding, Child Theme, and Static Content Import (v2)
# ==============================================================================

set -Eeuo pipefail

trap 'echo "[ERROR] Script failed at line $LINENO" >&2' ERR

echo "============================================================================"
echo "Step 1: Fix Persian Language"
echo "============================================================================"
echo "[INFO] Installing and activating Persian language fa_IR..."
wp language core install fa_IR --activate
wp core language update
wp plugin language update --all

echo ""
echo "============================================================================"
echo "Step 2: Create and Activate Blocksy Child Theme (RADMAN SILVER 925)"
echo "============================================================================"
echo "[INFO] Installing Blocksy parent theme if not already installed..."
wp theme install blocksy --activate || true

echo "[INFO] Creating Blocksy child theme directory..."
mkdir -p wp-content/themes/blocksy-child

echo "[INFO] Writing style.css (#0B0B0E background, #FAF7F2 text)..."
cat << 'EOF' > wp-content/themes/blocksy-child/style.css
/*
Theme Name:   Blocksy Child - RADMAN SILVER 925
Theme URI:    https://radmansilver.ir
Description:  Official Blocksy Child Theme for RADMAN SILVER 925 (925 Sterling Silver Maison)
Author:       RADMAN E-Commerce Developer
Author URI:   https://radmansilver.ir
Template:     blocksy
Version:      1.0.0
License:      GNU General Public License v2 or later
Text Domain:  blocksy-child-radman
*/

/* RADMAN SILVER 925 — Official Luxury Palette (#0B0B0E background, #FAF7F2 text) */
:root {
    --radman-bg-dark: #0B0B0E;
    --radman-text-ivory: #FAF7F2;
}

body, .ct-site, .site-content {
    background-color: #0B0B0E !important;
    color: #FAF7F2 !important;
}

h1, h2, h3, h4, h5, h6, .site-title, .entry-title {
    color: #FAF7F2 !important;
}

a, .ct-link {
    color: #FAF7F2;
}
EOF

echo "[INFO] Writing functions.php..."
cat << 'EOF' > wp-content/themes/blocksy-child/functions.php
<?php
/**
 * Blocksy Child - RADMAN SILVER 925
 * Functions and definitions
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('wp_enqueue_scripts', 'radman_blocksy_child_enqueue_styles', 20);
function radman_blocksy_child_enqueue_styles() {
    wp_enqueue_style(
        'radman-blocksy-child-style',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get('Version')
    );
}
EOF

echo "[INFO] Activating Blocksy Child Theme..."
wp theme activate blocksy-child
echo "  - Current active theme: $(wp theme list --status=active --field=name)"

echo ""
echo "============================================================================"
echo "Step 3: Import 11 Static Persian Pages as Drafts"
echo "============================================================================"
echo "[INFO] Creating static pages as Drafts..."

id_about=$(wp post create content/static-pages/about-us.md --post_type=page --post_title="درباره رادمان" --post_status=draft --porcelain)
echo "  - Created 'درباره رادمان' (ID: ${id_about})"

id_contact=$(wp post create content/static-pages/contact-us.md --post_type=page --post_title="تماس با ما" --post_status=draft --porcelain)
echo "  - Created 'تماس با ما' (ID: ${id_contact})"

id_faq=$(wp post create content/static-pages/faq.md --post_type=page --post_title="سؤالات متداول" --post_status=draft --porcelain)
echo "  - Created 'سؤالات متداول' (ID: ${id_faq})"

id_shipping=$(wp post create content/static-pages/shipping-policy.md --post_type=page --post_title="روش‌های ارسال" --post_status=draft --porcelain)
echo "  - Created 'روش‌های ارسال' (ID: ${id_shipping})"

id_returns=$(wp post create content/static-pages/returns-policy.md --post_type=page --post_title="شرایط بازگشت کالا" --post_status=draft --porcelain)
echo "  - Created 'شرایط بازگشت کالا' (ID: ${id_returns})"

id_privacy=$(wp post create content/static-pages/privacy-policy.md --post_type=page --post_title="حریم خصوصی" --post_status=draft --porcelain)
echo "  - Created 'حریم خصوصی' (ID: ${id_privacy})"

id_terms=$(wp post create content/static-pages/terms-of-purchase.md --post_type=page --post_title="قوانین و مقررات" --post_status=draft --porcelain)
echo "  - Created 'قوانین و مقررات' (ID: ${id_terms})"

id_ring=$(wp post create content/static-pages/ring-size-guide.md --post_type=page --post_title="راهنمای سایز انگشتر" --post_status=draft --porcelain)
echo "  - Created 'راهنمای سایز انگشتر' (ID: ${id_ring})"

id_care=$(wp post create content/static-pages/silver-care-guide.md --post_type=page --post_title="راهنمای نگهداری نقره" --post_status=draft --porcelain)
echo "  - Created 'راهنمای نگهداری نقره' (ID: ${id_care})"

id_auth=$(wp post create content/static-pages/silver-925-authenticity.md --post_type=page --post_title="اصالت نقره ۹۲۵" --post_status=draft --porcelain)
echo "  - Created 'اصالت نقره ۹۲۵' (ID: ${id_auth})"

id_gem=$(wp post create content/static-pages/gemstones-guide.md --post_type=page --post_title="راهنمای سنگ‌های زینتی" --post_status=draft --porcelain)
echo "  - Created 'راهنمای سنگ‌های زینتی' (ID: ${id_gem})"

echo ""
echo "============================================================================"
echo "Step 4: Verification Summary"
echo "============================================================================"
wp theme list --status=active
wp post list --post_type=page --post_status=draft --fields=ID,post_title,post_status

echo "============================================================================"
echo "CHILD THEME AND STATIC CONTENT IMPORTED SUCCESSFULLY"
echo "============================================================================"
