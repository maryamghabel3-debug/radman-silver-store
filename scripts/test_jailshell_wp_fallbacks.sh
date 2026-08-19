#!/usr/bin/env bash
# Local regression tests for CloudLinux/jailshell WP-CLI capture fallbacks.
# Uses a mocked wp() function only. Never contacts a host or WordPress.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=scripts/lib/wp_cli_capture.sh
source "$SCRIPT_DIR/lib/wp_cli_capture.sh"

PASS=0
FAIL=0
ok() { printf '[PASS] %s\n' "$*"; PASS=$((PASS+1)); }
fail() { printf '[FAIL] %s\n' "$*" >&2; FAIL=$((FAIL+1)); }
warn() { printf '[MOCK-WARN] %s\n' "$*" >&2; }

MOCK_CASE=""
WP_PATH=""
wp() {
    case "$MOCK_CASE:$*" in
        option-eval:"option get blog_public") return 0 ;;
        option-eval:"eval "*) printf '0\n'; return 0 ;;

        theme-list:"option get stylesheet") return 0 ;;
        theme-list:"eval "*) return 0 ;;
        theme-list:"theme list --status=active --field=name") printf 'blocksy-child\n'; return 0 ;;

        directory:"option get stylesheet") return 0 ;;
        directory:"eval "*) return 0 ;;
        directory:"theme list --status=active --field=name") return 0 ;;

        post-eval:"post get 18 --field=ID") return 0 ;;
        post-eval:"eval "*) printf '18\n'; return 0 ;;
    esac
    return 1
}

MOCK_CASE="option-eval"
value=""
if wp_read_option value blog_public && [[ "$value" == "0" ]]; then
    ok "empty option capture recovers through wp eval"
else
    fail "option fallback returned '${value}'"
fi

MOCK_CASE="theme-list"
theme=""; source_name=""
if wp_detect_active_theme theme source_name \
   && [[ "$theme" == "blocksy-child" && "$source_name" == "theme-list" ]]; then
    ok "active theme falls back from empty stylesheet option to theme list"
else
    fail "theme-list fallback returned theme='${theme}' source='${source_name}'"
fi

fixture="$(mktemp -d "${TMPDIR:-/tmp}/radman-theme-fixture.XXXXXX")"
trap 'rm -rf "$fixture"' EXIT
mkdir -p "$fixture/wp-content/themes/blocksy-child"
WP_PATH="$fixture"
MOCK_CASE="directory"
theme=""; source_name=""
if wp_detect_active_theme theme source_name \
   && [[ "$theme" == "blocksy-child" && "$source_name" == "directory" ]]; then
    ok "empty WP-CLI theme reads accept existing blocksy-child directory"
else
    fail "directory fallback returned theme='${theme}' source='${source_name}'"
fi

MOCK_CASE="post-eval"
post_id=""
if wp_post_exists post_id 18 && [[ "$post_id" == "18" ]]; then
    ok "post existence falls back without invalid post-get format flags"
else
    fail "post fallback returned '${post_id}'"
fi

# Static audit: invalid formatter forms and direct stderr-suppressed WP captures
# must not return to host scripts. Ignore comments deliberately.
if grep -RInE '^[[:space:]]*[^#[:space:]].*--format=(trim|ids)' "$SCRIPT_DIR" --include='*.sh' --exclude='test_jailshell_wp_fallbacks.sh' >/tmp/radman-invalid-formats.$$ 2>/dev/null; then
    cat /tmp/radman-invalid-formats.$$ >&2
    fail "invalid --format=trim/ids form found in shell scripts"
else
    ok "no invalid --format=trim/ids form in shell scripts"
fi
rm -f /tmp/radman-invalid-formats.$$

if grep -RInE '^[[:space:]]*[^#[:space:]].*wp .*2>/dev/null' "$SCRIPT_DIR" --include='*.sh' --exclude='test_jailshell_wp_fallbacks.sh' >/tmp/radman-fragile-captures.$$ 2>/dev/null; then
    cat /tmp/radman-fragile-captures.$$ >&2
    fail "direct wp ... 2>/dev/null pattern found"
else
    ok "no direct wp ... 2>/dev/null pattern remains"
fi
rm -f /tmp/radman-fragile-captures.$$

printf '\nResult: %d passed, %d failed.\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
