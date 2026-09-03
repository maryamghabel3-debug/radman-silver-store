"""
Tests for RADMAN SEO Advisory Pilot (Phase 2 — Verified Snapshot)
==================================================================
Validates schema recommendations, character length bounds, keyword density,
unverified claim rejection, exact price matching from snapshot, and report generation.

Runnable via:
  pytest tests/test_seo_advisory_pilot.py
  python tests/test_seo_advisory_pilot.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.platform.business_rules import RadmanBusinessRules
from agents.platform.run_seo_advisory import run_seo_advisory_pipeline
from agents.platform.seo_advisory import SEOAdvisoryAdvisor, SEOAdvisoryReport


class TestSEOAdvisoryPilot(unittest.TestCase):
    def setUp(self) -> None:
        self.advisor = SEOAdvisoryAdvisor()
        self.pilot_ids = [390, 275, 232, 205, 137]
        self.expected_prices = {
            390: 12564000,
            275: 5901000,
            232: 6633000,
            205: 8871000,
            137: 5929000,
        }
        self.expected_weights = {
            390: 13,
            275: 8,
            232: 8,
            205: 8,
            137: 8,
        }

    def test_all_five_products_analyzed_with_verified_snapshot_prices(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        self.assertEqual(len(reports), 5)
        for rep in reports:
            self.assertEqual(rep.price_toman, self.expected_prices[rep.product_id])
            self.assertEqual(rep.weight_g, self.expected_weights[rep.product_id])
            self.assertEqual(rep.qa_verdict, "PASS")

    def test_wrong_prices_purged(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        wrong_prices = [9425000, 5720000, 7800000, 8580000, 6825000]
        for rep in reports:
            self.assertNotIn(rep.price_toman, wrong_prices)

    def test_title_character_length_limits(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            title_len = len(rep.suggested_seo_title)
            self.assertLessEqual(
                title_len,
                60,
                f"Product {rep.product_id} title exceeds 60 chars ({title_len}): '{rep.suggested_seo_title}'",
            )
            self.assertGreater(title_len, 20)

    def test_meta_description_character_length_limits(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            meta_len = len(rep.suggested_meta_description)
            self.assertGreaterEqual(
                meta_len,
                120,
                f"Product {rep.product_id} meta description too short ({meta_len} < 120): '{rep.suggested_meta_description}'",
            )
            self.assertLessEqual(
                meta_len,
                155,
                f"Product {rep.product_id} meta description too long ({meta_len} > 155): '{rep.suggested_meta_description}'",
            )

    def test_unverified_claims_strictly_rejected(self) -> None:
        bad_texts = [
            "خرید انگشتر دست‌ساز نقره ۹۲۵ فاخر",
            "همراه با شناسنامه اصالت معتبر کالا",
            "ارسال در بسته‌بندی هدیه نفیس و شیک",
            "دارای گارانتی و ضمانت همیشگی اصالت",
            "خرید با نرخ مصوب نقره و عرضه مستقیم",
            "سنگ عقیق آبدار سه پوست کلکسیونی",
        ]
        for txt in bad_texts:
            res = RadmanBusinessRules.validate_content(txt)
            self.assertFalse(res.is_valid, f"Failed to block unverified text: {txt}")
            self.assertGreater(len(res.detected_patterns), 0)

    def test_weight_rule_validation(self) -> None:
        # Verified weight present -> mentions allowed
        self.assertTrue(RadmanBusinessRules.validate_weight_rule("انگشتر به وزن ۱۳ گرم", 13))
        # Empty weight -> weight claims rejected
        self.assertFalse(RadmanBusinessRules.validate_weight_rule("انگشتر به وزن ۱۳ گرم", None))
        self.assertTrue(RadmanBusinessRules.validate_weight_rule("انگشتر نقره عقیق بدون ذکر وزن", None))

    def test_schema_validity_and_no_sale_price(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            schema = rep.schema_recommendations
            self.assertEqual(schema.get("@context"), "https://schema.org")
            self.assertEqual(schema.get("@type"), "Product")
            self.assertEqual(schema.get("name"), rep.suggested_seo_title)

            offers = schema.get("offers", {})
            self.assertEqual(offers.get("@type"), "Offer")
            self.assertEqual(offers.get("priceCurrency"), "IRT")
            self.assertEqual(offers.get("price"), self.expected_prices[rep.product_id])

            # Strictly verify NO sale_price in schema or report serialization
            schema_str = json.dumps(schema)
            self.assertNotIn("sale_price", schema_str.lower())
            self.assertNotIn("saleprice", schema_str.lower())
            self.assertNotIn("discount", schema_str.lower())

            rep_dict_str = json.dumps(rep.to_dict())
            self.assertNotIn("sale_price", rep_dict_str.lower())

    def test_pipeline_runner_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            res = run_seo_advisory_pipeline(self.pilot_ids, Path(tmpdir), dry_run=True)
            self.assertEqual(res, 0)


if __name__ == "__main__":
    unittest.main()
