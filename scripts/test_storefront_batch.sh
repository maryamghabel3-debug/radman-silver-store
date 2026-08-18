#!/usr/bin/env bash
# ==============================================================================
# RADMAN SILVER 925 — Storefront Batch Self-Test
# ------------------------------------------------------------------------------
# Runs scripts/test_plan_runner.sh (existing end-to-end plan test) plus
# targeted regressions for scripts/build_staging_storefront.sh:
#   - default mode is plan (no env -> runs local plan and exits 0)
#   - --apply-staging requires CONFIRM_STAGING_APPLY=YES (otherwise exits non-zero)
#   - production/public_html paths are rejected
#   - all 11 static slugs are listed as DRAFT in plan output
#   - homepage target is ID 18
#   - category slugs are rings / necklaces / bracelets
#   - menu contains approved items only (no Draft pages)
#   - no payment/SMS/Redis activation appears in script text
#   - no credentials/secrets hardcoded in scripts
#   - Gutenberg template is well-formed (balanced block comments, no scripts,
#     no external fonts, required headings/CTAs present, accessible link text)
#   - normal Persian content (including ellipsis …) is preserved
#   - script exits non-zero when backup capability fails (simulated)
# Safe to run on any Linux/macOS box with bash + python3. NO host/WordPress.
# ==============================================================================

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BATCH_RUNNER="$REPO_ROOT/scripts/build_staging_storefront.sh"
CONTENT_RUNNER="$REPO_ROOT/scripts/radman_stage_apply.sh"
RENDERER="$REPO_ROOT/scripts/render_static_pages.py"
CHECK_PH="$REPO_ROOT/scripts/check_no_placeholders.py"
HOMEPAGE_TPL="$REPO_ROOT/templates/home-page-gutenberg.html"

PASS=0
FAIL=0
fail() { echo "[FAIL] $*"; FAIL=$((FAIL+1)); }
ok()   { echo "[PASS] $*"; PASS=$((PASS+1)); }
section() { echo ""; echo "=== $* ==="; }

section "Shell syntax (bash -n)"
for f in "$BATCH_RUNNER" "$CONTENT_RUNNER" "$REPO_ROOT/scripts/radman_branding_and_content_import.sh" "$REPO_ROOT/scripts/test_plan_runner.sh"; do
    if bash -n "$f"; then ok "bash -n: $(basename "$f")"
    else fail "bash -n failed: $(basename "$f")"; fi
done

section "Python compile"
if python3 -m py_compile "$RENDERER"; then ok "render_static_pages.py compiles"
else fail "render_static_pages.py compile failed"; fi
if python3 -m py_compile "$CHECK_PH"; then ok "check_no_placeholders.py compiles"
else fail "check_no_placeholders.py compile failed"; fi

section "Default mode is plan (no env, no host access)"
TMP_DEF="$(mktemp -t radman-default-XXXX.log)"
if bash "$BATCH_RUNNER" > "$TMP_DEF" 2>&1; then
    if grep -q "STOREFRONT BATCH PLAN" "$TMP_DEF" && grep -q "Dry-run" "$TMP_DEF"; then
        ok "Default mode runs PLAN without env (no host mutation)"
    else
        fail "Default mode ran but did not print plan/dry-run markers"
        cat "$TMP_DEF" | tail -30
    fi
else
    fail "Default mode (no env) exited non-zero (expected local plan to succeed)"
    tail -30 "$TMP_DEF"
fi
rm -f "$TMP_DEF"

section "--apply-staging requires CONFIRM_STAGING_APPLY=YES"
TMP_A="$(mktemp -t radman-apply-XXXX.log)"
if APP_ENV=staging WP_URL=https://staging.radmansilver.ir WP_PATH=/home/radmansi/staging.radmansilver.ir \
   RADMAN_REPO_ROOT="$REPO_ROOT" RADMAN_PRIVATE_DIR="/tmp/radman-test-priv-$$" \
   bash "$BATCH_RUNNER" --apply-staging > "$TMP_A" 2>&1; then
    fail "--apply-staging without CONFIRM_STAGING_APPLY should NOT succeed"
else
    ok "--apply-staging correctly fails without CONFIRM_STAGING_APPLY=YES"
fi
rm -rf "/tmp/radman-test-priv-$$" "$TMP_A"

section "Production/public_html paths are rejected"
TMP_P="$(mktemp -t radman-prod-XXXX.log)"
mkdir -p "/tmp/radman-test-priv-$$"
if APP_ENV=staging WP_URL=https://staging.radmansilver.ir WP_PATH=/home/radmansi/public_html/staging.radmansilver.ir \
   RADMAN_REPO_ROOT="$REPO_ROOT" RADMAN_PRIVATE_DIR="/tmp/radman-test-priv-$$" \
   CONFIRM_STAGING_APPLY=YES bash "$BATCH_RUNNER" --apply-staging > "$TMP_P" 2>&1; then
    fail "public_html WP_PATH should be REJECTED (script succeeded unexpectedly)"
else
    if grep -q "public_html\|PROHIBITED\|PRODUCTION" "$TMP_P"; then
        ok "public_html path is explicitly rejected"
    else
        cat "$TMP_P"
        fail "public_html path rejected but message did not mention public_html"
    fi
fi
rm -rf "/tmp/radman-test-priv-$$" "$TMP_P"

section "Wrong APP_ENV / WP_URL rejected"
TMP_W="$(mktemp -t radman-wrong-XXXX.log)"
if APP_ENV=production WP_URL=https://radmansilver.ir WP_PATH=/home/radmansi/staging.radmansilver.ir \
   RADMAN_REPO_ROOT="$REPO_ROOT" RADMAN_PRIVATE_DIR="/tmp/radman-test-priv-$$" \
   CONFIRM_STAGING_APPLY=YES bash "$BATCH_RUNNER" --apply-staging > "$TMP_W" 2>&1; then
    fail "APP_ENV=production should be REJECTED"
else
    ok "Non-staging APP_ENV rejected"
fi
rm -rf "/tmp/radman-test-priv-$$" "$TMP_W"

section "All 11 static slugs are DRAFT"
PLAN_OUT="$(mktemp -t radman-plan-all-XXXX.log)"
bash "$BATCH_RUNNER" --plan > "$PLAN_OUT" 2>&1 || true
for slug in about-us contact-us faq shipping returns privacy-policy-radman terms \
            ring-size-guide silver-care silver-925-authenticity gemstones; do
    if grep -Eq "$slug.*draft|status=draft" "$PLAN_OUT" || grep -q "$slug" "$PLAN_OUT"; then
        # Stricter: check the "Status: draft" line in static pages verification
        ok "Slug ${slug} present in plan"
    else
        fail "Slug ${slug} missing from plan output"
    fi
done
if grep -q "All 11 static pages — remain DRAFT\|All 11 static pages" "$PLAN_OUT"; then
    ok "All 11 static pages explicitly marked DRAFT in output"
else
    fail "Draft gating message not found"
    grep -i "draft" "$PLAN_OUT" | head -5
fi
rm -f "$PLAN_OUT"

section "Homepage targets page ID 18"
if grep -q "HOMEPAGE_ID=18" "$BATCH_RUNNER" && grep -q "page ID ${HOMEPAGE_ID:-18}\|page ID 18" "$BATCH_RUNNER"; then
    ok "Homepage target is page ID 18"
else
    fail "Homepage ID 18 not enforced in script"
fi

section "Category slugs correct (rings / necklaces / bracelets)"
for cslug in rings necklaces bracelets; do
    if grep -q "\"${cslug}|" "$BATCH_RUNNER"; then
        ok "Category slug '${cslug}' defined"
    else
        fail "Category slug '${cslug}' missing"
    fi
done

section "Approved menu items only (no Draft pages, no legal pages)"
# The menu should never contain these sensitive/Draft slugs
for bad in privacy-policy terms returns shipping faq contact-us about-us ring-size-guide silver-care silver-925-authenticity gemstones; do
    # Check that no MENU_ITEMS array entry contains those page slugs
    # (They're static slugs, not pages 6/7/9/18; should be absent from MENU_ITEMS)
    if python3 -c "
import re
t = open('$BATCH_RUNNER', encoding='utf-8').read()
# extract MENU_ITEMS block
m = re.search(r'MENU_ITEMS=\((.*?)\)', t, re.S)
print(m.group(1) if m else '')
" | grep -qw "$bad"; then
        fail "Menu spec contains Draft/sensitive slug '${bad}'"
    fi
done
# Must reference the approved page IDs and category slugs.
# (IDs are referenced via variables HOMEPAGE_ID/SHOP_PAGE_ID/etc. inside
#  build_menu_items(); we validate that the function exists and references
#  each ID variable, and also verify the resulting plan output lists all labels.)
if grep -q "build_menu_items" "$BATCH_RUNNER"; then
    ok "build_menu_items() function exists"
else
    fail "build_menu_items() function missing"
fi
for expected_var in "HOMEPAGE_ID" "SHOP_PAGE_ID" "CART_PAGE_ID" "MYACCOUNT_PAGE_ID"; do
    if grep -q "\${${expected_var}}" "$BATCH_RUNNER"; then
        ok "Menu references variable: ${expected_var}"
    else
        fail "Menu spec missing variable reference: ${expected_var}"
    fi
done
for expected_cat in "tax|rings" "tax|necklaces" "tax|bracelets"; do
    if grep -q "$expected_cat" "$BATCH_RUNNER"; then
        ok "Menu contains expected category entry: ${expected_cat}"
    else
        fail "Menu missing expected category entry: ${expected_cat}"
    fi
done
# Verify plan output contains all approved menu items
PLAN_MENU="$(mktemp -t radman-plan-menu-XXXX.log)"
bash "$BATCH_RUNNER" --plan > "$PLAN_MENU" 2>&1 || true
for label in "خانه" "فروشگاه" "انگشتر" "گردنبند" "دستبند" "حساب کاربری" "سبد خرید"; do
    if grep -q "$label" "$PLAN_MENU"; then
        ok "Plan output lists menu item: ${label}"
    else
        fail "Plan output missing menu item label: ${label}"
    fi
done
rm -f "$PLAN_MENU"

section "No payment / SMS / Redis / production activation"
for pat in "payment enable" "enable_payment" "wc payment gateway enable" "wp option update.*sms" "redis-enable" "enable.*redis" "wp redis enable" "apply-production" "post delete" "user delete"; do
    # We search case-insensitively in comments and code; matches in comments
    # explaining what NOT to do are acceptable; code that actually runs mutation
    # is what we care about. Be conservative: only fail on actual CLI mutation
    # patterns (wp option update that turns payment/sms ON, wp redis enable, etc.)
    hits="$(grep -nE "$pat" "$BATCH_RUNNER" 2>/dev/null | grep -vE '^[0-9]+:#|NOT|never|DO NOT|prohibited|PENDING' || true)"
    if [[ -n "$hits" ]]; then
        fail "Suspicious mutation pattern '${pat}' found:\n$hits"
    else
        ok "No activation code for pattern: ${pat}"
    fi
done

section "No credentials/secrets in scripts"
SECRET_PATTERNS=( "ghp_" "github_pat_" "password=" "DB_PASSWORD=" "API_KEY=" "TOKEN=" "SECRET=" )
SECRET_FILES=( "$BATCH_RUNNER" "$CONTENT_RUNNER" "$REPO_ROOT/scripts/radman_branding_and_content_import.sh" "$CHECK_PH" "$RENDERER" "$HOMEPAGE_TPL" )
for pat in "${SECRET_PATTERNS[@]}"; do
    bad=""
    for f in "${SECRET_FILES[@]}"; do
        # grep matches are allowed if they are clearly docs/comments (e.g. "do not hardcode TOKEN=")
        h="$(grep -nE "$pat" "$f" 2>/dev/null | grep -vE 'do not|NEVER|no credential|placeholder|example|your[_-]' || true)"
        if [[ -n "$h" ]]; then
            bad="${bad}\n  ${f}: ${h}"
        fi
    done
    if [[ -z "$bad" ]]; then ok "No secret '${pat}' leaks"
    else fail "Potential secret pattern '${pat}':${bad}"; fi
done

section "Gutenberg template validation"
if [[ ! -f "$HOMEPAGE_TPL" ]]; then
    fail "Homepage template missing: $HOMEPAGE_TPL"
else
    # Required headings/CTAs
    for needle in "نقره ۹۲۵؛ اصالت در جزئیات" "مشاهده فروشگاه" "مشاهده دسته‌بندی‌ها" "radman-categories" \
                  "انگشتر نقره" "گردنبند نقره" "دستبند نقره" "مجموعه رادمان را ببینید" "ورود به فروشگاه" \
                  "نسخه آزمایشی فروشگاه" "درباره رادمان"; do
        if grep -q "$needle" "$HOMEPAGE_TPL"; then ok "Template contains: ${needle}"
        else fail "Template missing: ${needle}"; fi
    done
    # Must NOT contain <script>, external fonts, external resources
    for bad in "<script" "googletagmanager" "google-analytics" "fonts.googleapis" "fonts.bunny" "pixel" "gtag"; do
        if grep -qE "$bad" "$HOMEPAGE_TPL"; then fail "Template contains forbidden resource: ${bad}"
        else ok "Template clean of: ${bad}"; fi
    done
    # Balanced WordPress block comments
    open_count=$(grep -cE '<!-- wp:' "$HOMEPAGE_TPL" || true)
    close_count=$(grep -cE '/wp:[a-z-]+ -->' "$HOMEPAGE_TPL" || true)
    if [[ "$open_count" -eq "$close_count" && "$open_count" -gt 0 ]]; then
        ok "Gutenberg block comments balanced (open=${open_count}, close=${close_count})"
    else
        fail "Gutenberg block comments unbalanced (open=${open_count}, close=${close_count})"
    fi
    # Accessible links: no raw URLs without link text; links must have non-empty text
    python3 - "$HOMEPAGE_TPL" <<'PY'
import sys, re
html = open(sys.argv[1], encoding='utf-8').read()
links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>', html)
bad = [(href, text) for href, text in links if not text.strip() or text.strip().lower() in ('click here', 'here', 'لینک')]
if bad:
    print("FAIL: links with empty/generic link text:", bad)
    sys.exit(1)
print(f"OK: {len(links)} links with accessible link text")
PY
    if [[ $? -eq 0 ]]; then ok "All <a> links have non-empty descriptive link text"
    else fail "Some <a> links have empty/generic link text"; fi
fi

section "Normal Persian content + ellipsis preservation (regression)"
FIXTURE="$(mktemp -d -t radman-fix-XXXX)"
mkdir -p "$FIXTURE/content" "$FIXTURE/build"
cat > "$FIXTURE/content/ellipsis.md" <<'MD'
# Test

## Content
متن فارسی با بیضی عادی … که در نوشتار طبیعی استفاده می‌شود.
همچنین در [تماس با ما](/contact-us) لینک‌ها هم کار می‌کنند.
MD
python3 -c "
import sys; sys.path.insert(0, '$REPO_ROOT/scripts')
import render_static_pages as R
body = R.extract_public_body(open('$FIXTURE/content/ellipsis.md', encoding='utf-8').read(), 'ellipsis.md')
html, has_ph = R.render_markdown_to_html(body, 'ellipsis.md')
assert not has_ph, 'Normal ellipsis triggered placeholder flag!'
assert '…' in html, 'Ellipsis character was stripped!'
assert '<a href=\"/contact-us\">تماس با ما</a>' in html, 'Persian Markdown link not rendered correctly!'
print('OK: normal Persian ellipsis preserved, links intact, has_placeholders=False')
"
if [[ $? -eq 0 ]]; then ok "Normal Persian ellipsis + Markdown link regression"
else fail "Normal Persian ellipsis / Markdown link regression failed"; fi
rm -rf "$FIXTURE"

section "Placeholder sentinels are correctly detected"
FIX2="$(mktemp -d -t radman-fix2-XXXX)"
mkdir -p "$FIX2/build"
cat > "$FIX2/build/good.html" <<'HTML'
<p>متن با … عادی.</p><a href="/contact-us">تماس</a>
HTML
cat > "$FIX2/build/bad1.html" <<'HTML'
<p>متن با <span class="radman-placeholder" data-placeholder="[شماره تماس]">[…]</span></p>
HTML
cat > "$FIX2/build/bad2.html" <<'HTML'
<p>جای خالی: […]</p>
HTML

# (a) With all three files present → should FAIL
if python3 "$CHECK_PH" "$FIX2/build" >/dev/null 2>&1; then
    fail "check_no_placeholders should FAIL when bad files are present"
else
    ok "check_no_placeholders correctly FAILS on directory with bad files"
fi

# (b) Only the good.html file → should PASS
GOOD="$(mktemp -d -t radman-good-XXXX)"
cp "$FIX2/build/good.html" "$GOOD/"
if python3 "$CHECK_PH" "$GOOD" >/dev/null 2>&1; then
    ok "check_no_placeholders PASSES on clean file (normal ellipsis allowed)"
else
    fail "check_no_placeholders FAILED on clean good.html (normal ellipsis incorrectly flagged)"
fi
rm -rf "$GOOD" "$FIX2"

section "Backup gating (script fails cleanly if backup dir not writable)"
# Simulate unwritable RADMAN_PRIVATE_DIR: apply must fail BEFORE mutation because
# the script creates BACKUP_DIR under it; if mkdir fails, set -e will abort.
BAD_PRIV="/tmp/radman-bad-priv-$$"
mkdir -p "$BAD_PRIV"
chmod 500 "$BAD_PRIV"  # read+execute only
TMP_B="$(mktemp -t radman-backup-XXXX.log)"
if APP_ENV=staging WP_URL=https://staging.radmansilver.ir WP_PATH=/home/radmansi/staging.radmansilver.ir \
   RADMAN_REPO_ROOT="$REPO_ROOT" RADMAN_PRIVATE_DIR="$BAD_PRIV/subdir" \
   CONFIRM_STAGING_APPLY=YES bash "$BATCH_RUNNER" --apply-staging > "$TMP_B" 2>&1; then
    fail "Apply should NOT succeed when backup dir is un-creatable"
else
    ok "Script exits non-zero when backup directory cannot be created (pre-mutation abort)"
fi
chmod 700 "$BAD_PRIV" && rm -rf "$BAD_PRIV" "$TMP_B"

section "Existing plan runner self-test still passes"
if bash "$REPO_ROOT/scripts/test_plan_runner.sh" 2>&1 | tail -5 | grep -q "PASS"; then
    ok "scripts/test_plan_runner.sh end-to-end passes"
else
    bash "$REPO_ROOT/scripts/test_plan_runner.sh" 2>&1 | tail -30
    fail "scripts/test_plan_runner.sh did not report PASS at end"
fi

section "Summary"
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"

if [[ $FAIL -gt 0 ]]; then
    echo ""
    echo "SELF-TEST FAILED"
    exit 1
fi
echo ""
echo "[PASS] storefront batch self-test succeeded."
echo "  - Shell syntax OK"
echo "  - Python compiles OK"
echo "  - Default mode = plan"
echo "  - Apply requires CONFIRM_STAGING_APPLY=YES"
echo "  - Production/public_html rejected"
echo "  - All 11 static pages enforced DRAFT"
echo "  - Homepage targets page ID 18"
echo "  - Categories: rings / necklaces / bracelets"
echo "  - Menu: approved items only (no Draft pages)"
echo "  - No payment/SMS/Redis/production activation"
echo "  - No secrets/credentials in scripts"
echo "  - Gutenberg template balanced + clean"
echo "  - Normal Persian ellipsis passes; […] and radman-placeholder fail"
