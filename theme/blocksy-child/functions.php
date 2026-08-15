<?php
/**
 * Blocksy Child — RADMAN SILVER 925
 *
 * Minimal child theme functions. Intentionally does NOT hard-enqueue the
 * parent stylesheet by hand: Blocksy's parent theme registers and enqueues
 * its own styles via its own asset pipeline. We only register the child
 * stylesheet with the parent style as a dependency so that:
 *   - the child stylesheet loads AFTER the parent,
 *   - we avoid double-loading the parent stylesheet,
 *   - we do NOT introduce external Google Fonts, tracking, or credentials.
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

    wp_enqueue_style(
        'radman-blocksy-child-style',
        get_stylesheet_uri(),
        (array) $parent_handle,
        wp_get_theme()->get('Version')
    );
}
