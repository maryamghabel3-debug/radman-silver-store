#!/usr/bin/env bash
# ==============================================================================
# Local self-test for the RADMAN staging plan runner.
# ------------------------------------------------------------------------------
# Runs scripts/radman_stage_apply.sh --plan against the real repo content
# (without any host/WordPress), asserts:
#   - exit code is 0
#   - the DEPLOY PLAN banner and table are printed (non-empty)
#   - all 11 slugs appear in the plan output
#   - rendered HTML contains NO placeholder markers ("[…]"/radman-placeholder)
#   - no host/WordPress invocation is made (no 'wp ' binary path required)
# Safe to run on any Linux/macOS box with bash + python3.
# ==============================================================================

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PLAN_LOG="$(mktemp -t radman-plan-log.XXXXXX)"
BUILD_PARENT="$(mktemp -d -t radman-plan-build.XXXXXX)"

cleanup() {
    rm -f "$PLAN_LOG"
    rm -rf "$BUILD_PARENT"
}
trap cleanup EXIT

echo "[TEST] repo root   : ${REPO_ROOT}"
echo "[TEST] log file    : ${PLAN_LOG}"
echo "[TEST] build parent: ${BUILD_PARENT}"

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
#    files exist and contain no placeholders.
BUILD_DIR="$(grep -oE "/[^ ]+/radman-plan-[^ ]+" "$PLAN_LOG" | head -n1 || true)"
if [[ -z "$BUILD_DIR" || ! -d "$BUILD_DIR" ]]; then
    # Fall back to scanning BUILD_PARENT (runner uses mktemp under TMPDIR now)
    BUILD_DIR="$(find "$BUILD_PARENT" -maxdepth 2 -type d -name 'radman-plan-*' | head -n1)"
fi
[[ -d "$BUILD_DIR" ]] || { echo "[FAIL] could not locate build dir under ${BUILD_PARENT}"; exit 1; }
echo "[TEST] build dir   : ${BUILD_DIR}"
for slug in about-us contact-us faq shipping returns privacy-policy-radman terms \
            ring-size-guide silver-care silver-925-authenticity gemstones; do
    f="${BUILD_DIR}/${slug}.html"
    [[ -s "$f" ]] || { echo "[FAIL] missing or empty rendered file: $f"; exit 1; }
    if grep -q -E $'\u2026|radman-placeholder' "$f"; then
        echo "[FAIL] placeholder marker found in $f"
        grep -n $'\u2026|radman-placeholder' "$f" || true
        exit 1
    fi
done

# 4) Dry-run must explicitly say no changes
grep -q "No WordPress content was modified" "$PLAN_LOG" \
    || { echo "[FAIL] expected 'No WordPress content was modified' message"; exit 1; }

echo
echo "[PASS] plan runner self-test succeeded."
echo "  - DEPLOY PLAN printed"
echo "  - all 11 slugs listed"
echo "  - all 11 HTML fragments rendered and non-empty"
echo "  - 0 placeholder markers in rendered output"
echo "  - dry-run confirmed (no WordPress mutation)"
