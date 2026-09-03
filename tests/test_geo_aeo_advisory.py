"""
Unit and Integration Tests for RADMAN GEO & AEO Advisory Engine
===============================================================
Validates Generative Engine Optimization (GEO) and Answer Engine Optimization (AEO)
capabilities, Schema.org FAQPage generation, citation readiness, business rules,
and verified snapshot provenance.

Runnable via:
  pytest tests/test_geo_aeo_advisory.py
  python tests/test_geo_aeo_advisory.py
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

from agents.platform.aeo_advisory import AEOAdvisor, AEOAdvisoryReport
from agents.platform.business_rules import RadmanBusinessRules
from agents.platform.geo_advisory import GEOAdvisor, GEOAdvisoryReport
from agents.platform.registry import AgentRegistry
from agents.platform.run_geo_aeo_advisory import run_geo_aeo_pipeline


class TestGEOAEOAdvisory(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.geo_advisor = GEOAdvisor()
        self.aeo_advisor = AEOAdvisor()
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

    def test_registry_contains_geo_and_aeo_skills(self) -> None:
        skills = self.registry.list_skills()
        self.assertIn("radman-geo-agent", skills)
        self.assertIn("radman-aeo-agent", skills)
        self.assertTrue(self.registry.validate_registry())

    def test_task_routing_for_geo_and_aeo(self) -> None:
        self.assertEqual(
            self.registry.route_task("Audit citation readiness for Google AI overviews"),
            "radman-geo-agent",
        )
        self.assertEqual(
            self.registry.route_task("Generate FAQ schema and ChatGPT search direct answers"),
            "radman-aeo-agent",
        )

    def test_geo_analysis_for_all_five_products(self) -> None:
        reports = self.geo_advisor.analyze_batch(self.pilot_ids)
        self.assertEqual(len(reports), 5)

        for rep in reports:
            self.assertIn(rep.product_id, self.pilot_ids)
            self.assertEqual(rep.price_toman, self.expected_prices[rep.product_id])
            self.assertEqual(rep.weight_g, self.expected_weights[rep.product_id])
            self.assertGreaterEqual(rep.geo_readiness_score, 80)
            self.assertLessEqual(rep.geo_readiness_score, 100)
            self.assertEqual(rep.citation_ready, "YES")
            self.assertEqual(rep.entity_clarity, "YES")
            self.assertGreater(len(rep.schema_gaps), 0)
            self.assertGreater(len(rep.content_suggestions), 0)
            self.assertGreater(len(rep.supporting_content_needed), 0)
            self.assertEqual(rep.qa_verdict, "PASS")
            self.assertEqual(rep.status, "draft")

    def test_aeo_analysis_and_faq_schema(self) -> None:
        reports = self.aeo_advisor.analyze_batch(self.pilot_ids)
        self.assertEqual(len(reports), 5)

        for rep in reports:
            self.assertIn(rep.product_id, self.pilot_ids)
            self.assertEqual(rep.price_toman, self.expected_prices[rep.product_id])
            self.assertEqual(rep.weight_g, self.expected_weights[rep.product_id])
            self.assertGreaterEqual(rep.aeo_readiness_score, 80)
            self.assertGreaterEqual(rep.questions_mapped, 3)
            self.assertGreaterEqual(rep.direct_answers_drafted, 3)
            self.assertEqual(rep.faq_schema_ready, "YES")
            self.assertEqual(rep.snippet_quality, "GOOD")
            self.assertGreaterEqual(len(rep.intent_coverage), 3)

            # Validate FAQPage schema structure
            faq = rep.faq_schema
            self.assertEqual(faq.get("@context"), "https://schema.org")
            self.assertEqual(faq.get("@type"), "FAQPage")
            entities = faq.get("mainEntity", [])
            self.assertGreaterEqual(len(entities), 3)
            for entity in entities:
                self.assertEqual(entity.get("@type"), "Question")
                self.assertTrue(bool(entity.get("name")))
                ans = entity.get("acceptedAnswer", {})
                self.assertEqual(ans.get("@type"), "Answer")
                self.assertTrue(bool(ans.get("text")))

    def test_wrong_prices_purged(self) -> None:
        geo_reps = self.geo_advisor.analyze_batch(self.pilot_ids)
        aeo_reps = self.aeo_advisor.analyze_batch(self.pilot_ids)
        wrong_prices = [9425000, 5720000, 7800000, 8580000, 6825000]

        for g in geo_reps:
            self.assertNotIn(g.price_toman, wrong_prices)
        for a in aeo_reps:
            self.assertNotIn(a.price_toman, wrong_prices)

    def test_business_rules_and_unverified_claims_rejected(self) -> None:
        geo_reps = self.geo_advisor.analyze_batch(self.pilot_ids)
        aeo_reps = self.aeo_advisor.analyze_batch(self.pilot_ids)

        for g in geo_reps:
            g_str = json.dumps(g.to_dict())
            self.assertNotIn("sale_price", g_str.lower())
            self.assertNotIn("saleprice", g_str.lower())
            self.assertNotIn("discount", g_str.lower())

        for a in aeo_reps:
            a_str = json.dumps(a.to_dict())
            self.assertNotIn("sale_price", a_str.lower())
            self.assertNotIn("saleprice", a_str.lower())
            self.assertNotIn("discount", a_str.lower())

            # Check direct answers for forbidden claims
            for qp in a.qa_pairs:
                ans = qp.direct_answer
                self.assertNotIn("09", ans)
                self.assertNotIn("دست‌ساز", ans)
                self.assertNotIn("شناسنامه", ans)
                self.assertNotIn("بسته‌بندی", ans)
                self.assertNotIn("گارانتی", ans)
                self.assertNotIn("ضمانت", ans)

    def test_report_export_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)
            res = run_geo_aeo_pipeline(self.pilot_ids, out_path, dry_run=True)
            self.assertEqual(res, 0)

            # Check 5 GEO and 5 AEO json files
            for pid in self.pilot_ids:
                geo_file = out_path / f"geo-advisory-{pid}.json"
                aeo_file = out_path / f"aeo-advisory-{pid}.json"
                self.assertTrue(geo_file.exists(), f"Missing {geo_file}")
                self.assertTrue(aeo_file.exists(), f"Missing {aeo_file}")

            # Check summaries
            summary_md = out_path / "geo-aeo-summary.md"
            summary_csv = out_path / "geo-aeo-summary.csv"
            unified_md = out_path / "unified-search-optimization-report.md"

            self.assertTrue(summary_md.exists())
            self.assertTrue(summary_csv.exists())
            self.assertTrue(unified_md.exists())

            self.assertIn("GEO & AEO Summary", summary_md.read_text(encoding="utf-8"))
            self.assertIn("12,564,000", summary_md.read_text(encoding="utf-8"))
            self.assertIn("SEO + GEO + AEO", unified_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
