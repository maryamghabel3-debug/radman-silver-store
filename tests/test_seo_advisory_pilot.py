"""
Tests for RADMAN SEO Advisory Pilot (Phase 2)
==============================================
Validates schema recommendations, character length bounds, keyword density,
forbidden claim detection, absence of sale_price, and report generation.

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

from agents.platform.seo_advisory import SEOAdvisoryAdvisor, SEOAdvisoryReport
from agents.platform.run_seo_advisory import run_seo_advisory_pipeline


class TestSEOAdvisoryPilot(unittest.TestCase):
    def setUp(self) -> None:
        self.advisor = SEOAdvisoryAdvisor()
        self.pilot_ids = [390, 275, 232, 205, 137]

    def test_all_five_products_analyzed(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        self.assertEqual(len(reports), 5)
        analyzed_ids = [r.product_id for r in reports]
        self.assertEqual(analyzed_ids, self.pilot_ids)

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

    def test_focus_keyword_repetition_in_meta(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            kw = rep.suggested_focus_keyword
            meta = rep.suggested_meta_description
            count = meta.count(kw)
            self.assertLessEqual(
                count,
                2,
                f"Product {rep.product_id} focus keyword repeated {count} times (>2) in meta description.",
            )
            self.assertIn(rep.keyword_stuffing_risk, ["LOW", "MEDIUM"])

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
            self.assertGreater(offers.get("price", 0), 0)

            # Strictly verify NO sale_price in schema or report serialization
            schema_str = json.dumps(schema)
            self.assertNotIn("sale_price", schema_str.lower())
            self.assertNotIn("saleprice", schema_str.lower())
            self.assertNotIn("discount", schema_str.lower())

            rep_dict_str = json.dumps(rep.to_dict())
            self.assertNotIn("sale_price", rep_dict_str.lower())

    def test_secondary_keywords_and_internal_links(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            self.assertEqual(len(rep.secondary_keywords), 3)
            self.assertEqual(len(rep.internal_link_suggestions), 2)
            for link in rep.internal_link_suggestions:
                self.assertIn(link.target_product_id, self.pilot_ids)
                self.assertNotEqual(link.target_product_id, rep.product_id)
                self.assertTrue(bool(link.suggested_anchor_text))

    def test_forbidden_claims_absence(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            self.assertEqual(rep.forbidden_claims_found, [])
            self.assertEqual(rep.qa_verdict, "PASS")

    def test_report_export_and_files_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)
            reports = self.advisor.analyze_batch(self.pilot_ids)
            files = self.advisor.export_reports(reports, out_path)

            # Check 5 JSON files
            for pid in self.pilot_ids:
                fname = f"seo-advisory-{pid}.json"
                self.assertIn(fname, files)
                fpath = out_path / fname
                self.assertTrue(fpath.exists())
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                    self.assertEqual(data["product_id"], pid)
                    self.assertEqual(data["status"], "draft")

            # Check Markdown summary
            md_path = out_path / "seo-advisory-summary.md"
            self.assertTrue(md_path.exists())
            content = md_path.read_text(encoding="utf-8")
            self.assertIn("گزارش نتایج پایلوت مشاوره‌ای سئو رادمان", content)
            self.assertIn("13204540", content)

            # Check CSV summary
            csv_path = out_path / "seo-advisory-summary.csv"
            self.assertTrue(csv_path.exists())

    def test_pipeline_runner_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            res = run_seo_advisory_pipeline(self.pilot_ids, Path(tmpdir), dry_run=True)
            self.assertEqual(res, 0)


if __name__ == "__main__":
    unittest.main()
