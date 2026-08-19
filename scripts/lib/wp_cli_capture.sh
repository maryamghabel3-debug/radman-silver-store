#!/usr/bin/env bash
# RADMAN SILVER 925 — jailshell-safe WP-CLI read helpers.
#
# This file is sourced by host runners after they define a `wp()` wrapper.
# It avoids fragile `VALUE="$(wp ... 2>/dev/null)"` captures by writing WP-CLI
# output to a regular temporary file, retrying once with stderr visible, and
# then using an independent `wp eval` fallback for critical reads.
#
# Requirements: Bash, mktemp, a caller-provided wp() function. No process
# substitution and no /dev/fd paths are used.

radman_wp_warn() {
    if declare -F warn >/dev/null 2>&1; then
        warn "$*"
    else
        printf '[WARN]  %s\n' "$*" >&2
    fi
}

radman_wp_trim_value() {
    local __radman_out_var="$1"
    local value="$2"
    value="${value//$'\r'/}"
    # Command substitution already strips trailing newlines. Remove leading and
    # trailing horizontal whitespace without external tools.
    value="${value#"${value%%[!$' \t']*}"}"
    value="${value%"${value##*[!$' \t']}"}"
    printf -v "$__radman_out_var" '%s' "$value"
}

# Usage: wp_capture_to_var OUT_VAR wp-subcommand [args...]
# Returns 0 only when non-empty stdout was captured.
wp_capture_to_var() {
    local __radman_out_var="$1"
    shift
    local tmp_out tmp_err captured rc
    tmp_out="$(mktemp "${TMPDIR:-/tmp}/radman-wp-out.XXXXXX")" || return 1
    tmp_err="$(mktemp "${TMPDIR:-/tmp}/radman-wp-err.XXXXXX")" || {
        rm -f "$tmp_out"
        return 1
    }
    chmod 600 "$tmp_out" "$tmp_err" 2>/dev/null || true

    rc=0
    wp "$@" >"$tmp_out" 2>"$tmp_err" || rc=$?
    captured="$(cat "$tmp_out")"
    radman_wp_trim_value captured "$captured"

    if [[ -z "$captured" ]]; then
        # CloudLinux/jailshell has returned empty output for otherwise valid
        # reads when stderr was redirected. Retry without redirecting stderr.
        : >"$tmp_out"
        rc=0
        wp "$@" >"$tmp_out" || rc=$?
        captured="$(cat "$tmp_out")"
        radman_wp_trim_value captured "$captured"
    fi

    rm -f "$tmp_out" "$tmp_err"
    printf -v "$__radman_out_var" '%s' "$captured"
    [[ "$rc" -eq 0 && -n "$captured" ]]
}

radman_wp_validate_key() {
    [[ "$1" =~ ^[A-Za-z0-9_.:-]+$ ]]
}

# Read a scalar WordPress option. Fallback is direct get_option() through
# wp eval, which is independent of `wp option get` formatter/output behavior.
wp_read_option() {
    local __radman_out_var="$1"
    local key="$2"
    local option_value="" php_code
    radman_wp_validate_key "$key" || return 2

    if wp_capture_to_var option_value option get "$key"; then
        printf -v "$__radman_out_var" '%s' "$option_value"
        return 0
    fi

    php_code="\$v=get_option('${key}', null); if (is_bool(\$v)) { echo \$v ? '1' : '0'; } elseif (is_scalar(\$v)) { echo (string) \$v; }"
    if wp_capture_to_var option_value eval "$php_code"; then
        radman_wp_warn "wp option get '${key}' was empty; recovered via wp eval fallback."
        printf -v "$__radman_out_var" '%s' "$option_value"
        return 0
    fi

    printf -v "$__radman_out_var" '%s' ''
    return 1
}

# Read an option as JSON (for array options such as gateway settings).
wp_read_option_json() {
    local __radman_out_var="$1"
    local key="$2"
    local json_value="" php_code
    radman_wp_validate_key "$key" || return 2

    if wp_capture_to_var json_value option get "$key" --format=json; then
        printf -v "$__radman_out_var" '%s' "$json_value"
        return 0
    fi

    php_code="\$sentinel='__RADMAN_MISSING__'; \$v=get_option('${key}', \$sentinel); if (\$v !== \$sentinel) { echo wp_json_encode(\$v); }"
    if wp_capture_to_var json_value eval "$php_code"; then
        radman_wp_warn "JSON read for option '${key}' recovered via wp eval fallback."
        printf -v "$__radman_out_var" '%s' "$json_value"
        return 0
    fi

    printf -v "$__radman_out_var" '%s' ''
    return 1
}

# Active-theme detection in the required order:
#   1) stylesheet option
#   2) wp theme list --status=active --field=name
#   3) blocksy-child directory presence
# Sets OUT_VAR and SOURCE_VAR (option|theme-list|directory|none).
wp_detect_active_theme() {
    local __radman_out_var="$1"
    local __radman_source_var="$2"
    local value="" first_line=""

    if wp_read_option value stylesheet && [[ -n "$value" ]]; then
        first_line="${value%%$'\n'*}"
        radman_wp_trim_value first_line "$first_line"
        printf -v "$__radman_out_var" '%s' "$first_line"
        printf -v "$__radman_source_var" '%s' 'option'
        return 0
    fi

    value=""
    if wp_capture_to_var value theme list --status=active --field=name; then
        first_line="${value%%$'\n'*}"
        radman_wp_trim_value first_line "$first_line"
        if [[ -n "$first_line" ]]; then
            printf -v "$__radman_out_var" '%s' "$first_line"
            printf -v "$__radman_source_var" '%s' 'theme-list'
            return 0
        fi
    fi

    if [[ -n "${WP_PATH:-}" && -d "$WP_PATH/wp-content/themes/blocksy-child" ]]; then
        printf -v "$__radman_out_var" '%s' 'blocksy-child'
        printf -v "$__radman_source_var" '%s' 'directory'
        return 0
    fi

    printf -v "$__radman_out_var" '%s' 'unknown'
    printf -v "$__radman_source_var" '%s' 'none'
    return 1
}

wp_read_theme_mod() {
    local __radman_out_var="$1"
    local key="$2"
    local value="" php_code
    radman_wp_validate_key "$key" || return 2

    if wp_capture_to_var value theme mod get "$key"; then
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    php_code="\$v=get_theme_mod('${key}', ''); if (is_scalar(\$v)) { echo (string) \$v; }"
    if wp_capture_to_var value eval "$php_code"; then
        radman_wp_warn "Theme mod '${key}' recovered via wp eval fallback."
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    printf -v "$__radman_out_var" '%s' ''
    return 1
}

wp_post_exists() {
    local __radman_out_var="$1"
    local __radman_post_id="$2"
    local value="" php_code
    [[ "$__radman_post_id" =~ ^[0-9]+$ ]] || return 2

    if wp_capture_to_var value post get "$__radman_post_id" --field=ID; then
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    php_code="\$p=get_post(${__radman_post_id}); if (\$p) { echo (string) \$p->ID; }"
    if wp_capture_to_var value eval "$php_code"; then
        radman_wp_warn "Post ${__radman_post_id} existence recovered via wp eval fallback."
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    printf -v "$__radman_out_var" '%s' ''
    return 1
}

wp_read_post_field() {
    local __radman_out_var="$1"
    local __radman_post_id="$2"
    local field="$3"
    local value="" php_code
    [[ "$__radman_post_id" =~ ^[0-9]+$ ]] || return 2
    [[ "$field" =~ ^[A-Za-z0-9_]+$ ]] || return 2

    if wp_capture_to_var value post get "$__radman_post_id" --field="$field"; then
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    php_code="\$p=get_post(${__radman_post_id}); if (\$p && isset(\$p->${field}) && is_scalar(\$p->${field})) { echo (string) \$p->${field}; }"
    if wp_capture_to_var value eval "$php_code"; then
        radman_wp_warn "Post ${__radman_post_id} field '${field}' recovered via wp eval fallback."
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    printf -v "$__radman_out_var" '%s' ''
    return 1
}

wp_find_post_id_by_slug() {
    local __radman_out_var="$1"
    local post_type="$2"
    local slug="$3"
    local value="" slug_b64 php_code
    [[ "$post_type" =~ ^[A-Za-z0-9_-]+$ ]] || return 2

    if wp_capture_to_var value post list --post_type="$post_type" --name="$slug" --field=ID; then
        value="${value%%$'\n'*}"
        radman_wp_trim_value value "$value"
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi

    slug_b64="$(printf '%s' "$slug" | base64 | tr -d '\n')"
    php_code="\$p=get_page_by_path(base64_decode('${slug_b64}'), OBJECT, '${post_type}'); if (\$p) { echo (string) \$p->ID; }"
    if wp_capture_to_var value eval "$php_code"; then
        radman_wp_warn "Post lookup '${post_type}/${slug}' recovered via wp eval fallback."
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    printf -v "$__radman_out_var" '%s' ''
    return 1
}

wp_find_term_id_by_slug() {
    local __radman_out_var="$1"
    local taxonomy="$2"
    local slug="$3"
    local value="" slug_b64 php_code
    [[ "$taxonomy" =~ ^[A-Za-z0-9_-]+$ ]] || return 2

    if wp_capture_to_var value term list "$taxonomy" --slug="$slug" --field=term_id; then
        value="${value%%$'\n'*}"
        radman_wp_trim_value value "$value"
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi

    slug_b64="$(printf '%s' "$slug" | base64 | tr -d '\n')"
    php_code="\$t=get_term_by('slug', base64_decode('${slug_b64}'), '${taxonomy}'); if (\$t && !is_wp_error(\$t)) { echo (string) \$t->term_id; }"
    if wp_capture_to_var value eval "$php_code"; then
        radman_wp_warn "Term lookup '${taxonomy}/${slug}' recovered via wp eval fallback."
        printf -v "$__radman_out_var" '%s' "$value"
        return 0
    fi
    printf -v "$__radman_out_var" '%s' ''
    return 1
}
