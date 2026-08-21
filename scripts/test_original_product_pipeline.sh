#!/bin/sh
# Offline acceptance gates for PR-25. No network, host, or WordPress mutation.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$REPO_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  agents/agent_legacy_catalog_pilot.py \
  agents/agent_gemstone_classifier.py \
  agents/agent_original_image_processor.py \
  agents/agent_original_product_pipeline.py \
  agents/lib/legacy_identity.py \
  agents/lib/legacy_pricing.py \
  agents/test_original_product_pipeline.py

sh -n scripts/run_original_product_import.sh
sh -n scripts/test_original_product_pipeline.sh
if command -v dash >/dev/null 2>&1; then
  dash -n scripts/run_original_product_import.sh
  dash -n scripts/test_original_product_pipeline.sh
fi
if command -v bash >/dev/null 2>&1; then
  bash --posix -n scripts/run_original_product_import.sh
fi

if grep -nE '(^|[[:space:]])local([[:space:]]|$)|<\(|/dev/fd' scripts/run_original_product_import.sh; then
  echo "[FAIL] jailshell-incompatible shell construct found" >&2
  exit 1
fi

# Approved processor must not import/invoke background or generative model families.
if grep -niE 'rembg|bria|birefnet|diffusers|stable[_ -]?diffusion|generate_image' \
  agents/agent_original_image_processor.py agents/agent_original_product_pipeline.py; then
  echo "[FAIL] prohibited media-model invocation found" >&2
  exit 1
fi

# No publish action is permitted anywhere in the PR-25 executable path.
if grep -niE "set_status\([^)]*publish|post_status[^a-z]+publish|--post_status=publish" \
  agents/agent_original_product_pipeline.py scripts/run_original_product_import.sh; then
  echo "[FAIL] auto-publish path found" >&2
  exit 1
fi

# Basic committed-secret patterns. Placeholders are not credentials.
if grep -nE 'gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' \
  agents/agent_gemstone_classifier.py \
  agents/agent_original_image_processor.py \
  agents/agent_original_product_pipeline.py \
  agents/lib/legacy_identity.py \
  agents/lib/legacy_pricing.py \
  scripts/run_original_product_import.sh; then
  echo "[FAIL] possible committed credential found" >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python3 agents/test_original_product_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 agents/test_product_media_pilot.py

echo "ALL ORIGINAL-PRODUCT PIPELINE ACCEPTANCE GATES PASSED"
