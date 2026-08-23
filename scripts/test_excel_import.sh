#!/usr/bin/env bash
# Offline PR-34 exact-pricing and Draft-only SEO publication gates.
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$REPO_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  agents/agent_excel_product_pipeline.py \
  agents/agent_product_seo.py \
  agents/agent_product_seo_qa.py \
  agents/lib/product_identity.py \
  agents/test_excel_product_pipeline.py \
  agents/test_product_identity.py \
  agents/test_product_seo.py \
  agents/test_product_seo_qa.py \
  scripts/analyze_excel_catalog.py \
  scripts/test_catalog_analysis.py \
  scripts/test_luxury_pricing.py
bash -n scripts/run_excel_import.sh
bash --posix -n scripts/run_excel_import.sh
bash -n scripts/test_excel_import.sh

if grep -nE '(^|[[:space:]])local([[:space:]]|$)|<\(|/dev/fd' scripts/run_excel_import.sh; then
  echo '[FAIL] jailshell-incompatible shell construct found' >&2
  exit 1
fi

if grep -nE 'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY' \
  agents/agent_excel_product_pipeline.py \
  agents/agent_product_seo.py \
  agents/agent_product_seo_qa.py \
  agents/lib/product_identity.py \
  agents/test_excel_product_pipeline.py \
  agents/test_product_identity.py \
  agents/test_product_seo.py \
  agents/test_product_seo_qa.py \
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
  agents/agent_excel_product_pipeline.py agents/agent_product_seo.py \
  agents/agent_product_seo_qa.py scripts/run_excel_import.sh; then
  echo '[FAIL] auto-publish path found' >&2
  exit 1
fi

if grep -niE 'wp_delete_post|post[[:space:]]+delete|product[[:space:]]+delete' \
  agents/agent_excel_product_pipeline.py scripts/run_excel_import.sh; then
  echo '[FAIL] product deletion path found' >&2
  exit 1
fi

if grep -n -- '--api-probe' scripts/run_excel_import.sh; then
  echo '[FAIL] API probe must remain deferred in the PR-34 owner runner' >&2
  exit 1
fi

REJECTED_PUBLIC_DISCLAIMER='اطلاعات فوق فقط از مشخصات فنی صفحه همان محصول استخراج شده است'
REJECTED_PUBLIC_DISCLAIMER="$REJECTED_PUBLIC_DISCLAIMER."
if grep -nF "$REJECTED_PUBLIC_DISCLAIMER" \
  agents/agent_excel_product_pipeline.py README.md docs/HTML-SPEC-ENRICHMENT-RUNBOOK.md; then
  echo '[FAIL] internal extraction disclaimer found in public-description sources' >&2
  exit 1
fi

if grep -nE 'ROUNDING_STEP|round_up_toman|rounding_step_toman' \
  agents/agent_excel_product_pipeline.py agents/lib/legacy_pricing.py \
  agents/agent_original_product_pipeline.py; then
  echo '[FAIL] obsolete 50000-Toman rounding path found' >&2
  exit 1
fi

if grep -nE 'set_sale_price|update_meta_data\([^,]*sale_price' \
  agents/agent_excel_product_pipeline.py agents/agent_product_seo.py; then
  echo '[FAIL] sale-price setter found' >&2
  exit 1
fi

if grep -nE 'final_price[^\n]*(%[[:space:]]*10|endswith\([^)]*9)' \
  agents/agent_excel_product_pipeline.py; then
  echo '[FAIL] charm/9-ending pricing manipulation found' >&2
  exit 1
fi

if grep -nE 'amount[[:space:]]*//[[:space:]]*10|price[[:space:]]*\*[[:space:]]*10|price[[:space:]]*/[[:space:]]*10' \
  agents/agent_excel_product_pipeline.py; then
  echo '[FAIL] Rial/Toman conversion path found' >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python3 agents/test_product_identity.py
PYTHONDONTWRITEBYTECODE=1 python3 agents/test_excel_product_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 agents/test_product_seo.py
PYTHONDONTWRITEBYTECODE=1 python3 agents/test_product_seo_qa.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_catalog_analysis.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_luxury_pricing.py
sh scripts/test_original_product_pipeline.sh

echo 'ALL EXCEL IMPORT ACCEPTANCE GATES PASSED'
