#!/usr/bin/env bash
# ==============================================================================
# Local self-test for the RADMAN staging plan runner.
# ------------------------------------------------------------------------------
# Runs scripts/radman_stage_apply.sh --plan against the real repo content
# (without any host/WordPress), asserts:
#   - exit code is 0
#   - the DEPLOY PLAN banner and table are printed (non-empty)
#   - all 11 slugs appear in the plan output
#   - rendered HTML contains NO placeholder markers ("[...]", bracketed
#     owner-fill tokens, or the radman-placeholder CSS class). A normal
#     Persian ellipsis "..." (U+2026) on its own IS allowed in prose and
#     does NOT fail the gate.
#   - no host/WordPress invocation is made (no 'wp ' binary path required)
# Additionally runs targeted regression tests for the placeholder detector:
#   - a fixture file containing ONLY a normal "..." ellipsis -> PASS
#   - a fixture file containing the literal "[...]" sentinel -> FAIL
#   - a fixture file containing the radman-placeholder CSS class -> FAIL
# Safe to run on any Linux/macOS box with bash + python3.
# ==============================================================================

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PLAN_LOG="$(mktemp -t radman-plan-log.XXXXXX)"
BUILD_PARENT="$(mktemp -d -t radman-plan-build.XXXXXX)"
REGRESSION_DIR="$(mktemp -d -t radman-regression.XXXXXX)"

cleanup() {
    rm -f "$PLAN_LOG"
    rm -rf "$BUILD_PARENT"
    rm -rf "$REGRESSION_DIR"
}
trap cleanup EXIT

echo "[TEST] repo root      : ${REPO_ROOT}"
echo "[TEST] log file       : ${PLAN_LOG}"
echo "[TEST] build parent   : ${BUILD_PARENT}"
echo "[TEST] regression dir : ${REGRESSION_DIR}"

# -----------------------------------------------------------------------------
# PART A: Plan-runner end-to-end against real repo content
# -----------------------------------------------------------------------------
echo
echo "=== PART A: plan runner end-to-end ==="

# Run the runner in --plan mode. Note: the runner's local (non-host) branch works
# without WP_* variables because it never reaches the wp()/host-access blocks.
# We point TMPDIR at our temp parent so we know exactly where the build lands.
TMPDIR="$BUILD_PARENT" \
RADMAN_REPO_ROOT="$REPO_ROOT" \
bash "${REPO_ROOT}/scripts/radman_stage_apply.sh" --plan > "$PLAN_LOG" 2>&1 \
    || { echo "[FAIL] plan runner exited non-zero; tail of log:"; tail -60 "$PLAN_LOG"; exit 1; }

echo "---------------------------------------------------------------------"
tail -40 "$PLAN_LOG"
echo "---------------------------------------------------------------------"

# 1) DEPLOY PLAN banner present
grep -q "DEPLOY PLAN" "$PLAN_LOG" || { echo "[FAIL] DEPLOY PLAN banner not found"; exit 1; }

# 2) All 11 official slugs must appear in the printed plan
for slug in about-us contact-us faq shipping returns privacy-policy-radman terms \
            ring-size-guide silver-care silver-925-authenticity gemstones; do
    grep -q "$slug" "$PLAN_LOG" || { echo "[FAIL] slug ${slug} missing from plan"; exit 1; }
done

# 3) Find the build directory printed by the runner and assert all 11 HTML
#    files exist and contain no placeholders via the real check_no_placeholders.py.
BUILD_DIR="$(grep -oE "/[^ ]+/radman-plan-[^ ]+" "$PLAN_LOG" | head -n1 || true)"
if [[ -z "$BUILD_DIR" || ! -d "$BUILD_DIR" ]]; then
    # Fall back to scanning BUILD_PARENT (runner uses mktemp under TMPDIR now)
    BUILD_DIR="$(find "$BUILD_PARENT" -maxdepth 2 -type d -name 'radman-plan-*' | head -n1)"
fi
[[ -d "$BUILD_DIR" ]] || { echo "[FAIL] could not locate build dir under ${BUILD_PARENT}"; exit 1; }
echo "[TEST] build dir      : ${BUILD_DIR}"
for slug in about-us contact-us faq shipping returns privacy-policy-radman terms \
            ring-size-guide silver-care silver-925-authenticity gemstones; do
    f="${BUILD_DIR}/${slug}.html"
    [[ -s "$f" ]] || { echo "[FAIL] missing or empty rendered file: $f"; exit 1; }
done
# Use the real gate (which correctly allows bare "..."):
python3 "${REPO_ROOT}/scripts/check_no_placeholders.py" "$BUILD_DIR"

# 4) Dry-run must explicitly say no changes
grep -q "No WordPress content was modified" "$PLAN_LOG" \
    || { echo "[FAIL] expected 'No WordPress content was modified' message"; exit 1; }

# -----------------------------------------------------------------------------
# PART B: Ellipsis / placeholder-detector regression fixtures
# -----------------------------------------------------------------------------
echo
echo "=== PART B: placeholder-detector regressions ==="

FIXTURE_CONTENT="$REGRESSION_DIR/content"
FIXTURE_BUILD="$REGRESSION_DIR/build"
mkdir -p "$FIXTURE_CONTENT" "$FIXTURE_BUILD"

# We render directly via render_static_pages.py against a tiny synthetic
# content dir using the same slug->file contract, by symlinking in place of
# the source and pointing --repo-root at our fixture. To keep the test
# minimal we instead:
#   (a) write a tiny Markdown fixture directly,
#   (b) invoke render_static_pages.py via a lightweight harness that points
#       at our fixture, OR simply feed HTML snippets directly to
#       check_no_placeholders.py (which only scans *.html in a dir).
# We take the direct approach for check_no_placeholders.py, since PART A
# already exercises the renderer end-to-end.

# ---- B1: Normal standalone "..." ellipsis must PASS ----
cat > "$FIXTURE_BUILD/ellipsis-pass.html" <<'HTML'
<article><p>متن فارسی با بیضی عادی … که در نوشتار طبیعی استفاده می‌شود.</p></article>
HTML
if python3 "${REPO_ROOT}/scripts/check_no_placeholders.py" "$FIXTURE_BUILD" >/dev/null 2>&1; then
    echo "[PASS] B1: normal ellipsis '…' passes the placeholder gate."
else
    echo "[FAIL] B1: normal ellipsis '…' should PASS but was flagged."
    exit 1
fi
rm "$FIXTURE_BUILD/ellipsis-pass.html"

# ---- B2: Literal "[...]" bracketed-ellipsis sentinel must FAIL ----
cat > "$FIXTURE_BUILD/bracketed-ellipsis-fail.html" <<'HTML'
<article><p>این یک [؟] است و یک <span>[…]</span> جا مانده.</p></article>
HTML
if python3 "${REPO_ROOT}/scripts/check_no_placeholders.py" "$FIXTURE_BUILD" >/dev/null 2>&1; then
    echo "[FAIL] B2: literal '[…]' sentinel should FAIL but passed."
    exit 1
else
    echo "[PASS] B2: literal '[…]' sentinel correctly fails the gate."
fi
rm "$FIXTURE_BUILD/bracketed-ellipsis-fail.html"

# ---- B3: radman-placeholder CSS class must FAIL ----
cat > "$FIXTURE_BUILD/placeholder-class-fail.html" <<'HTML'
<article><p>متن با <span class="radman-placeholder" data-placeholder="[شماره تماس]">[…]</span> در خود.</p></article>
HTML
if python3 "${REPO_ROOT}/scripts/check_no_placeholders.py" "$FIXTURE_BUILD" >/dev/null 2>&1; then
    echo "[FAIL] B3: radman-placeholder class should FAIL but passed."
    exit 1
else
    echo "[PASS] B3: radman-placeholder CSS class correctly fails the gate."
fi
rm "$FIXTURE_BUILD/placeholder-class-fail.html"

# ---- B4: Markdown link with Persian text should NOT produce placeholders ----
# Run the renderer on a tiny fixture page via a dedicated one-off source dir.
FIXTURE_PAGES="$REGRESSION_DIR/fixture-pages"
FIXTURE_OUT="$REGRESSION_DIR/fixture-out"
mkdir -p "$FIXTURE_PAGES" "$FIXTURE_OUT"
cat > "$FIXTURE_PAGES/test-link.md" <<'MD'
# Test

## Content
برای اطلاعات بیشتر به صفحه [تماس با ما](/contact-us) یا [راهنمای سایز](/ring-size-guide) مراجعه کنید.
همچنین می‌توانید به [لینک خارجی](https://example.com) بروید.
متن عادی با بیضی … در وسط جمله.
MD
# Render just this one file using a tiny Python harness
python3 - "$FIXTURE_PAGES" "$FIXTURE_OUT" "$REPO_ROOT/scripts" <<'PY'
import sys, pathlib
scripts_dir = sys.argv[3]
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
import render_static_pages as rsp
src_dir = pathlib.Path(sys.argv[1])
out_dir = pathlib.Path(sys.argv[2])
md_text = (src_dir / "test-link.md").read_text(encoding="utf-8")
body = rsp.extract_public_body(md_text, "test-link.md")
html_out, has_ph = rsp.render_markdown_to_html(body, "test-link.md")
(out_dir / "test-link.html").write_text(
    "<article>" + html_out + "</article>", encoding="utf-8"
)
print(f"has_placeholders={has_ph}")
print(html_out)
PY
if python3 "${REPO_ROOT}/scripts/check_no_placeholders.py" "$FIXTURE_OUT" >/dev/null 2>&1; then
    echo "[PASS] B4: Persian Markdown links and normal ellipsis produce no placeholders."
else
    echo "[FAIL] B4: Persian Markdown links / normal ellipsis were incorrectly flagged."
    python3 "${REPO_ROOT}/scripts/check_no_placeholders.py" "$FIXTURE_OUT" || true
    exit 1
fi

# -----------------------------------------------------------------------------
echo
echo "[PASS] plan runner self-test succeeded."
echo "  - DEPLOY PLAN printed"
echo "  - all 11 slugs listed"
echo "  - all 11 HTML fragments rendered and non-empty"
echo "  - 0 placeholder markers in rendered output"
echo "  - dry-run confirmed (no WordPress mutation)"
echo "  - normal ellipsis '…' regressions PASSED"
echo "  - '[…]' sentinel / radman-placeholder regressions PASSED"
echo "  - Persian Markdown links do NOT trigger placeholder detector"
