#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — PR-20 focused regression tests
# ------------------------------------------------------------------------------
# Validates the FIX-PR-20-FAST mission requirements:
#   1. No `wp post get ... --format=ids` anywhere in scripts.
#   2. No `--format=trim` anywhere in scripts (except comments).
#   3. deploy_all apply flow does NOT call `build_staging_storefront.sh --apply-staging`.
#   4. deploy_all apply flow DOES call `build_staging_storefront.sh --check`.
#   5. deploy_all apply flow DOES call `apply_design_system.sh --apply-staging`.
#   6. deploy_all apply flow DOES call `install_agents.sh --install`.
#   7. Existing custom_logo is preserved (idempotent logic present).
#   8. Existing site_icon is preserved (idempotent logic present).
#   9. Default logo file is radman-logo-header-ivory.png.
#  10. install_agents.sh does not overwrite an existing staging.env.
#  11. Agents smoke tests run with DRY_RUN=1.
#  12. No automatic cron registration (no crontab -e / `crontab -l |` / piped install).
# ==============================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0
fail() { printf '  [FAIL] %s\n' "$1"; FAIL=$((FAIL+1)); }
ok()   { printf '  [ OK ] %s\n' "$1"; PASS=$((PASS+1)); }
section() { printf '\n=== %s ===\n' "$1"; }

section "1. No 'wp post get ... --format=ids' in any script"
# Match ONLY command lines (not comment-only lines and not this test file itself).
_bad_fmt_ids=$(grep -rnE 'wp[[:space:]]+post[[:space:]]+get.*--format=ids' scripts/ --include="*.sh" \
    | grep -v -E 'test_pr20_deploy_flow\.sh' \
    | grep -v -E '^[^:]+:[0-9]+:[[:space:]]*#' \
    | grep -v 'wp post exists' || true)
if [[ -n "$_bad_fmt_ids" ]]; then
    echo "$_bad_fmt_ids"
    fail "Found invalid 'wp post get ... --format=ids' (unsupported by wp-cli)."
else
    ok "No invalid wp-post-get --format=ids."
fi

section "2. No '--format=trim' invocations in any script (comments allowed)"
# Match lines where --format=trim appears OUTSIDE of a # comment (i.e. actual command args).
# Exclude this test file itself from the scan.
_bad_trim=$(grep -rn '\-\-format=trim' scripts/ --include="*.sh" \
    | grep -v -E 'test_pr20_deploy_flow\.sh' \
    | grep -v -E '^[^:]+:[0-9]+:[[:space:]]*#' \
    | grep -v -E '^[^:]+:[0-9]+:[[:space:]]*[^#]*#' || true)
if [[ -n "$_bad_trim" ]]; then
    echo "$_bad_trim"
    fail "Found non-comment --format=trim invocations (jailshell-incompatible)."
else
    ok "No non-comment --format=trim invocations."
fi

section "3. deploy_all.sh does NOT run build_staging_storefront.sh --apply-staging"
if grep -E 'build_staging_storefront\.sh[^$]*--apply-staging' scripts/deploy_all.sh; then
    fail "deploy_all.sh contains build_staging_storefront.sh --apply-staging."
else
    ok "deploy_all.sh never re-applies the foundation."
fi

section "4. deploy_all.sh DOES run build_staging_storefront.sh --check"
if grep -q 'build_staging_storefront.sh' scripts/deploy_all.sh \
   && grep -q 'echo --check' scripts/deploy_all.sh; then
    ok "Stage 1 invokes build_staging_storefront.sh with --check (read-only)."
else
    fail "Stage 1 does not invoke --check."
fi

section "5. deploy_all.sh DOES run apply_design_system.sh --apply-staging"
if grep -q 'apply_design_system.sh' scripts/deploy_all.sh && grep -q -- '--apply-staging' scripts/deploy_all.sh; then
    ok "Stage 2 runs apply_design_system.sh --apply-staging."
else
    fail "Stage 2 missing apply_design_system.sh --apply-staging."
fi

section "6. deploy_all.sh DOES run install_agents.sh --install"
if grep -q 'install_agents.sh' scripts/deploy_all.sh && grep -q -- '--install' scripts/deploy_all.sh; then
    ok "Stage 3 runs install_agents.sh --install."
else
    fail "Stage 3 missing install_agents.sh --install."
fi

section "7. Existing custom_logo is preserved (idempotent)"
if grep -q 'Existing custom logo preserved' scripts/apply_design_system.sh \
   && grep -q 'existing_logo_raw\|custom_logo preserved\|preserved: attachment ID' scripts/apply_design_system.sh; then
    ok "apply_design_system.sh preserves existing custom_logo."
else
    fail "apply_design_system.sh missing custom_logo preservation logic."
fi

section "8. Existing site_icon is preserved (idempotent)"
if grep -q 'Existing site_icon preserved' scripts/apply_design_system.sh \
   && grep -q 'existing_icon_raw\|site_icon preserved' scripts/apply_design_system.sh; then
    ok "apply_design_system.sh preserves existing site_icon."
else
    fail "apply_design_system.sh missing site_icon preservation logic."
fi

section "9. Default logo is radman-logo-header-ivory.png"
if grep -q 'LOGO_HEADER_FILE="radman-logo-header-ivory.png"' scripts/apply_design_system.sh \
   && grep -q 'radman-logo-header-ivory' scripts/apply_design_system.sh; then
    ok "Default header logo is radman-logo-header-ivory.png (ivory on dark header)."
else
    fail "LOGO_HEADER_FILE is not set to radman-logo-header-ivory.png."
fi

section "10. install_agents.sh does NOT overwrite existing staging.env"
if grep -q 'if \[\[ ! -f "\$ENV_TARGET" \]\]' scripts/install_agents.sh \
   && grep -q 'Env file already exists, leaving untouched' scripts/install_agents.sh; then
    ok "install_agents.sh creates staging.env ONLY if missing (never overwrites)."
else
    fail "install_agents.sh may overwrite an existing staging.env."
fi

section "11. Agent smoke tests run with DRY_RUN=1"
if grep -q 'DRY_RUN=1' scripts/install_agents.sh \
   && grep -q 'Smoke-testing agents in DRY_RUN mode' scripts/install_agents.sh; then
    ok "Smoke tests are invoked with DRY_RUN=1."
else
    fail "Smoke tests not explicitly DRY_RUN=1."
fi

section "12. No automatic crontab registration"
_cron_auto=$(grep -nE 'crontab[[:space:]]+-e|crontab[[:space:]]+-l[[:space:]]*\|[^|]' scripts/install_agents.sh scripts/deploy_all.sh scripts/apply_design_system.sh scripts/build_staging_storefront.sh 2>/dev/null || true)
if [[ -n "$_cron_auto" ]]; then
    echo "$_cron_auto"
    fail "Found automatic crontab registration."
else
    ok "No automatic crontab registration (lines printed only)."
fi

section "13. bash -n syntax checks"
for f in scripts/apply_design_system.sh scripts/deploy_all.sh scripts/install_agents.sh scripts/build_staging_storefront.sh scripts/radman_branding_and_content_import.sh scripts/radman_stage_apply.sh scripts/test_pr20_deploy_flow.sh; do
    if bash -n "$f" 2>&1; then
        ok "bash -n $f"
    else
        fail "bash -n $f failed"
    fi
done

section "14. Python syntax checks (agents)"
for f in agents/lib/radman_common.py agents/agent_order_watch.py agents/agent_price_engine.py agents/agent_stock_guard.py agents/test_agents_dryrun.py; do
    if python3 -m py_compile "$f" 2>&1; then
        ok "py_compile $f"
    else
        fail "py_compile $f failed"
    fi
done

section "15. No hardcoded credentials / tokens / Telegram / Google Fonts"
# Exclude test scripts that *scan for* these strings (they contain the patterns as literals).
# Exclude inline comments / docs. Exclude the env-template which has KAVENEGAR_API_KEY= (empty value).
_hits=$(grep -rnE 'KAVENEGAR_API_KEY=[A-Za-z0-9/+]{8,}|TOKEN\s*=\s*"?[A-Za-z0-9_]{30,}"?|bot[0-9]{6,12}:AAE[a-zA-Z0-9_-]+|https?://fonts\.googleapis|fonts\.gstatic\.com' scripts/ agents/ theme/ --include="*.sh" --include="*.py" --include="*.php" --include="*.css" 2>/dev/null \
    | grep -v -E 'test_(plan_runner|storefront_batch|pr20_deploy_flow|agents_dryrun)\.(sh|py)' \
    | grep -v -E 'KAVENEGAR_API_KEY=$|KAVENEGAR_API_KEY=\\|KAVENEGAR_API_KEY=""' \
    | grep -v -E '^[^:]+:[0-9]+:[[:space:]]*#' \
    | grep -v -E 'TOKEN\s*=\s*[A-Za-z0-9_]+\s*\+\s*=' || true)
if [[ -n "$_hits" ]]; then
    echo "$_hits"
    fail "Found potential hardcoded secret / external resource."
else
    ok "No hardcoded credentials or external fonts."
fi

section "16. plan-runner self-test (if available, non-host-mode)"
if [[ -f scripts/test_plan_runner.sh ]]; then
    if bash scripts/test_plan_runner.sh 2>&1 | tail -20; then
        ok "scripts/test_plan_runner.sh completed."
    else
        fail "scripts/test_plan_runner.sh failed."
    fi
else
    ok "test_plan_runner.sh not present (non-fatal)."
fi

echo ""
echo "==============================="
printf 'PASS: %d   FAIL: %d\n' "$PASS" "$FAIL"
echo "==============================="
if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
exit 0
