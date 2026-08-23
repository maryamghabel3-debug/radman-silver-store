#!/usr/bin/env python3
"""Offline acceptance tests for the no-sale luxury pricing hotfix."""

from __future__ import annotations

import re
import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents import agent_excel_product_pipeline as excel  # noqa: E402


EXECUTABLE_PRICING_PATHS = (
    REPO_ROOT / "agents" / "agent_excel_product_pipeline.py",
    REPO_ROOT / "agents" / "agent_original_product_pipeline.py",
    REPO_ROOT / "agents" / "agent_price_engine.py",
    REPO_ROOT / "agents" / "agent_legacy_sync.py",
    REPO_ROOT / "scripts" / "import_products.py",
)


def test_regular_price_always_equals_final() -> None:
    cases = (
        excel.calculate_pricing(
            title="انگشتر",
            excel_price=7_689_000,
            pre_discount_price=8_900_000,
            weight=None,
        ),
        excel.calculate_pricing(
            title="انگشتر",
            excel_price=1_000_000,
            pre_discount_price=9_900_000,
            weight=Decimal("2"),
        ),
        excel.calculate_pricing(
            title="انگشتر نگین درشت",
            excel_price=5_000_000,
            pre_discount_price=8_000_000,
            weight=Decimal("10"),
        ),
    )
    for decision in cases:
        assert decision.regular_price_toman == decision.final_price_toman
        assert not hasattr(decision, "sale_price_toman")
    assert cases[0].regular_price_toman == 7_689_000
    assert cases[0].pricing_mode == "legacy_mirror"
    assert cases[1].regular_price_toman == 1_300_000
    assert cases[2].regular_price_toman == 5_900_000
    fractional = excel.calculate_pricing(
        title="انگشتر",
        excel_price=1_000_000,
        pre_discount_price=None,
        weight=Decimal("2.000001"),
    )
    assert fractional.final_price_toman == 1_300_001
    assert fractional.rounding_policy == "EXACT_NO_CHARM_NO_50000_ROUNDING"
    print("PASS: exact legacy/floor pricing uses whole-Toman ceiling and regular equals final")


def test_no_importer_sets_sale_price() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in EXECUTABLE_PRICING_PATHS)
    assert "set_sale_price" not in combined
    assert not re.search(r"[\"']sale_price[\"']\s*[:=]", combined)
    assert "sale_price_toman" not in combined
    assert "ROUNDING_STEP" not in (REPO_ROOT / "agents" / "agent_excel_product_pipeline.py").read_text(encoding="utf-8")
    assert "round_up_toman" not in (REPO_ROOT / "agents" / "agent_excel_product_pipeline.py").read_text(encoding="utf-8")
    assert "delete_post_meta($id, '_sale_price')" in combined
    assert "update_post_meta($id, '_price', $luxury_regular)" in combined
    assert "delete_post_meta({pid}, '_sale_price')" in combined
    assert "$p->set_price((string)$d['regular_price']);" in combined
    assert "$p->set_price((string) $d['price']);" in combined
    print("PASS: importers/price engine set one regular price and only delete stale sale meta")


def test_report_and_cleanup_command() -> None:
    assert "sale_price_toman" not in excel.REPORT_COLUMNS
    report = (REPO_ROOT / "docs" / "LUXURY-PRICING-HOTFIX.md").read_text(
        encoding="utf-8"
    )
    assert '"posts_per_page" => 20' in report
    assert 'delete_post_meta($id, "_sale_price")' in report
    assert 'update_post_meta($id, "_regular_price", $regular)' in report
    assert 'update_post_meta($id, "_price", $regular)' in report
    assert "regular == price" in report
    print("PASS: report omits sale fields and documents safe 20-Draft cleanup command")


def main() -> int:
    test_regular_price_always_equals_final()
    test_no_importer_sets_sale_price()
    test_report_and_cleanup_command()
    print("ALL LUXURY PRICING HOTFIX TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
