"""
Unit and Integration Tests for RADMAN Content Advisory Engine
==============================================================
Validates Instagram luxury captions, Story CTAs, factual WooCommerce short
descriptions, blog outlines, Fact-Lock rules, locked identity verification,
and Instagram calendar generation.

Runnable via:
  pytest tests/test_content_advisory.py
  python tests/test_content_advisory.py
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
from agents.platform.content_advisory import ContentAdvisor, ContentAdvisoryReport
from agents.platform.run_content_advisory import run_content_pipeline


class TestContentAdvisory(unittest.TestCase):
    def setUp(self) -> None:
        self.advisor = ContentAdvisor()
        self.pilot_ids = [232, 205, 378, 375, 372, 369]
        self.expected_skus = {
            232: "NM-3596",
            205: "NM-3605",
            378: "NM-3548",
            375: "NM-3549",
            372: "NM-3550",
            369: "NM-3551",
        }
        self.expected_stones = {
            232: "آماتیست طبیعی دامله",
            205: "عقیق باباقوری",
            378: "عقیق سیاه",
            375: "عقیق سوسنی",
            372: "دُر نجف",
            369: "عقیق زرد",
        }
        self.expected_weights = {
            232: 8,
            205: 8,
            378: 12,
            375: 12,
            372: 12,
            369: 12,
        }

    def test_all_six_products_analyzed_with_correct_mappings(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        self.assertEqual(len(reports), 6)
        for rep in reports:
            pid = rep.product_id
            self.assertEqual(rep.sku, self.expected_skus[pid], f"Wrong SKU for product {pid}")
            self.assertEqual(rep.stone, self.expected_stones[pid], f"Wrong stone for product {pid}")
            self.assertEqual(rep.weight_g, self.expected_weights[pid], f"Wrong weight for product {pid}")
            self.assertEqual(rep.qa_verdict, "PASS")

    def test_false_mappings_completely_purged(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        rep_dict = {r.product_id: r for r in reports}

        # Check that false SKUs are absent
        false_skus = ["NM-3612", "NM-3615", "NM-3618", "NM-3622"]
        for rep in reports:
            self.assertNotIn(rep.sku, false_skus)

        # Check specific product false stones
        self.assertNotIn("فیروزه", rep_dict[378].stone)
        self.assertNotIn("کبود", rep_dict[375].stone)
        self.assertNotIn("یاقوت", rep_dict[372].stone)
        self.assertEqual(rep_dict[369].stone, "عقیق زرد")

    def test_locked_identity_tuple_enforcement(self) -> None:
        # Correct identity tuple passes
        valid, viols = RadmanBusinessRules.validate_locked_identity(
            378, "NM-3548", "انگشتر نقره مردانه عقیق سیاه حکاکی حسبی الله", "عقیق سیاه"
        )
        self.assertTrue(valid)
        self.assertEqual(len(viols), 0)

        # Incorrect SKU fails
        valid_bad_sku, viols_sku = RadmanBusinessRules.validate_locked_identity(
            378, "NM-3612", "انگشتر نقره مردانه عقیق سیاه حکاکی حسبی الله", "عقیق سیاه"
        )
        self.assertFalse(valid_bad_sku)
        self.assertIn("BR-IDENT-01", viols_sku[0])

        # Incorrect stone fails
        valid_bad_stone, viols_stone = RadmanBusinessRules.validate_locked_identity(
            378, "NM-3548", "انگشتر نقره مردانه عقیق سیاه حکاکی حسبی الله", "فیروزه نیشابور"
        )
        self.assertFalse(valid_bad_stone)
        self.assertIn("BR-IDENT-03", viols_stone[0])

    def test_instagram_captions_structure_and_constraints(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            cap = rep.instagram_caption

            # Check hashtags (3–5 hashtags)
            hashtags = [w for w in cap.split() if w.startswith("#")]
            self.assertGreaterEqual(len(hashtags), 3, f"Product {rep.product_id} has fewer than 3 hashtags")
            self.assertLessEqual(len(hashtags), 5, f"Product {rep.product_id} has more than 5 hashtags")

            # Check no price
            self.assertNotIn("تومان", cap)
            self.assertNotIn("ریال", cap)
            self.assertNotIn("قیمت", cap)

            # Check no phone
            self.assertNotIn("09", cap)
            self.assertNotIn("+98", cap)

            # Check Fact-Lock
            self.assertNotIn("دست‌ساز", cap)
            self.assertNotIn("شناسنامه", cap)
            self.assertNotIn("بسته‌بندی هدیه", cap)
            self.assertNotIn("گارانتی", cap)
            self.assertNotIn("ضمانت", cap)
            self.assertNotIn("نرخ مصوب", cap)

    def test_instagram_story_text_structure(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            story = rep.instagram_story_text
            self.assertGreater(len(story), 20)
            self.assertLess(len(story), 200)
            self.assertTrue("بایو" in story or "سایت" in story or "رادمان" in story)

    def test_woocommerce_short_description_factual_accuracy(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            desc = rep.product_short_description
            self.assertIn("۹۲۵", desc)
            self.assertIn(rep.stone, desc)
            if rep.weight_g:
                self.assertIn("گرم", desc)
            self.assertIn("نقره ماشینی", desc)
            self.assertEqual(rep.qa_verdict, "PASS")

    def test_blog_outline_structure(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            blog = rep.blog_outline
            self.assertTrue(bool(blog.title))
            self.assertGreaterEqual(len(blog.sections), 3)
            self.assertGreaterEqual(len(blog.key_takeaways), 2)
            self.assertEqual(blog.target_stone, rep.stone)

    def test_unverified_claim_injection_fails(self) -> None:
        bad_captions = [
            "انگشتر دست‌ساز نقره ۹۲۵ با شناسنامه معتبر #نقره #انگشتر #رادمان",
            "خرید انگشتر با ارسال فوری تضمینی و گارانتی همیشگی #نقره #انگشتر #رادمان",
            "خرید انگشتر با بسته بندی نفیس هدیه و ضمانت اصالت #نقره #انگشتر #رادمان",
            "سفارش با شماره 09121234567 #نقره #انگشتر #رادمان",
        ]
        for cap in bad_captions:
            res = RadmanBusinessRules.validate_content(cap)
            self.assertFalse(res.is_valid, f"Failed to reject bad caption: {cap}")

    def test_report_export_and_calendar_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)
            res = run_content_pipeline(self.pilot_ids, out_path, dry_run=True)
            self.assertEqual(res, 0)

            # Check 6 JSON files
            for pid in self.pilot_ids:
                fpath = out_path / f"content-advisory-{pid}.json"
                self.assertTrue(fpath.exists())
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                    self.assertEqual(data["product_id"], pid)
                    self.assertEqual(data["sku"], self.expected_skus[pid])
                    self.assertEqual(data["stone"], self.expected_stones[pid])
                    self.assertEqual(data["status"], "draft")

            # Check summary markdown
            summary_path = out_path / "content-summary.md"
            self.assertTrue(summary_path.exists())
            summary_content = summary_path.read_text(encoding="utf-8")
            self.assertIn("Content Advisory Pilot", summary_content)
            self.assertIn("NM-3548", summary_content)
            self.assertIn("NM-3551", summary_content)

            # Check Instagram calendar
            calendar_path = out_path / "instagram-calendar-week1.md"
            self.assertTrue(calendar_path.exists())
            cal_text = calendar_path.read_text(encoding="utf-8")
            self.assertIn("شنبه (Saturday)", cal_text)
            self.assertIn("پنج‌شنبه (Thursday)", cal_text)
            self.assertIn("حسبی الله", cal_text)
            self.assertIn("یا اباعبدالله", cal_text)
            for pid in self.pilot_ids:
                self.assertIn(str(pid), cal_text)

            # Check CSV summary
            csv_path = out_path / "content-summary.csv"
            self.assertTrue(csv_path.exists())


if __name__ == "__main__":
    unittest.main()
