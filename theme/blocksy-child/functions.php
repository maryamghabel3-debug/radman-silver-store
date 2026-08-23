<?php
/**
 * Blocksy Child — RADMAN SILVER 925
 *
 * Minimal child theme functions. Intentionally does NOT hard-enqueue the
 * parent stylesheet by hand: Blocksy's parent theme registers and enqueues
 * its own styles via its own asset pipeline. We register the child
 * stylesheet with the parent style as a dependency so that:
 *   - the child stylesheet loads AFTER the parent,
 *   - we avoid double-loading the parent stylesheet,
 *   - we do NOT introduce external Google Fonts, tracking, or credentials.
 *
 * The Radman design system CSS and local webfont CSS are enqueued AFTER the
 * parent + child style.css so they can reliably override Blocksy defaults.
 *
 * Activation / correct ordering is verified by the staging deploy runner
 * (wp theme list + active-theme check), not by a static claim here.
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('wp_enqueue_scripts', 'radman_blocksy_child_enqueue_styles', 20);
function radman_blocksy_child_enqueue_styles() {
    // Use the parent handle registered by Blocksy if present; fall back gracefully.
    $parent_handle = 'blocksy-style';
    if (!wp_style_is($parent_handle, 'registered')) {
        // Parent handle missing (theme renamed / older Blocksy); enqueue child standalone.
        $parent_handle = array();
    }

    // 1) Base child stylesheet (palette tokens, homepage tweaks)
    wp_enqueue_style(
        'radman-blocksy-child-style',
        get_stylesheet_uri(),
        (array) $parent_handle,
        wp_get_theme()->get('Version')
    );

    // 2) Local webfonts @font-face declarations (Estedad + Vazirmatn, NO remote fonts)
    wp_enqueue_style(
        'radman-local-fonts',
        get_stylesheet_directory_uri() . '/assets/radman-fonts.css',
        array('radman-blocksy-child-style'),
        wp_get_theme()->get('Version')
    );

    // 3) Design system (typography scale, components, responsive polish)
    wp_enqueue_style(
        'radman-design-system',
        get_stylesheet_directory_uri() . '/assets/radman-design-system.css',
        array('radman-local-fonts'),
        wp_get_theme()->get('Version')
    );

    // 4) Product UI layer (shop, product, cart; presentation only)
    $product_ui_path = get_stylesheet_directory() . '/assets/radman-product-ui.css';
    wp_enqueue_style(
        'radman-product-ui',
        get_stylesheet_directory_uri() . '/assets/radman-product-ui.css',
        array('radman-design-system'),
        file_exists($product_ui_path) ? (string) filemtime($product_ui_path) : wp_get_theme()->get('Version')
    );
}
