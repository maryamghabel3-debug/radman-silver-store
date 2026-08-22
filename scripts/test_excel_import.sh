#!/usr/bin/env bash
# Offline PR-28 acceptance gates. No host, network, image download, or WP mutation.
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$REPO_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  agents/agent_excel_product_pipeline.py \
  agents/test_excel_product_pipeline.py \
  scripts/analyze_excel_catalog.py \
  scripts/test_catalog_analysis.py
bash -n scripts/run_excel_import.sh
bash --posix -n scripts/run_excel_import.sh
bash -n scripts/test_excel_import.sh

if grep -nE '(^|[[:space:]])local([[:space:]]|$)|<\(|/dev/fd' scripts/run_excel_import.sh; then
  echo '[FAIL] jailshell-incompatible shell construct found' >&2
  exit 1
fi

if grep -nE 'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY' \
  agents/agent_excel_product_pipeline.py \
  agents/test_excel_product_pipeline.py \
  scripts/run_excel_import.sh; then
  echo '[FAIL] possible credential found' >&2
  exit 1
fi

if grep -niE 'rembg|bria|birefnet|diffusers|stable[_ -]?diffusion|generate_image' \
  agents/agent_excel_product_pipeline.py scripts/run_excel_import.sh; then
  echo '[FAIL] prohibited media-model path found' >&2
  exit 1
fi

if grep -niE "set_status\([^)]*publish|post_status[^a-z]+publish|--post_status=publish" \
  agents/agent_excel_product_pipeline.py scripts/run_excel_import.sh; then
  echo '[FAIL] auto-publish path found' >&2
  exit 1
fi

if grep -nE 'amount[[:space:]]*//[[:space:]]*10|price[[:space:]]*\*[[:space:]]*10|price[[:space:]]*/[[:space:]]*10' \
  agents/agent_excel_product_pipeline.py; then
  echo '[FAIL] Rial/Toman conversion path found' >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python3 agents/test_excel_product_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_catalog_analysis.py

echo 'ALL EXCEL IMPORT ACCEPTANCE GATES PASSED'
