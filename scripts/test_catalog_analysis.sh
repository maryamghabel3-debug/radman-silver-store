#!/usr/bin/env bash
# Offline acceptance gates for PR-28A. No host, network, media, or WP mutation.
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$REPO_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  scripts/analyze_excel_catalog.py \
  scripts/test_catalog_analysis.py
bash -n scripts/run_catalog_analysis.sh
bash -n scripts/test_catalog_analysis.sh

if grep -nE 'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY' \
  scripts/analyze_excel_catalog.py \
  scripts/run_catalog_analysis.sh \
  scripts/test_catalog_analysis.py; then
  echo '[FAIL] possible credential found' >&2
  exit 1
fi

if grep -niE 'wc_get_|wp-cli|(^|[^a-z])wp[[:space:]]+(post|wc|eval|media|db)|media[[:space:]]+import|requests\.|urllib\.|https?://' \
  scripts/analyze_excel_catalog.py \
  scripts/run_catalog_analysis.sh; then
  echo '[FAIL] network, WordPress, or media mutation capability found' >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_catalog_analysis.py

echo 'ALL CATALOG ANALYSIS ACCEPTANCE GATES PASSED'
