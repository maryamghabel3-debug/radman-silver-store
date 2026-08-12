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
