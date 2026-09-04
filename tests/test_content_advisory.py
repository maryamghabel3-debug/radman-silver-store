"""
Unit and Integration Tests for RADMAN Content Advisory Engine
==============================================================
Validates Instagram luxury captions, Story CTAs, factual WooCommerce short
descriptions, blog outlines, Fact-Lock rules, and Instagram calendar generation.

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

    def test_all_six_products_analyzed(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        self.assertEqual(len(reports), 6)
        analyzed_ids = [r.product_id for r in reports]
        self.assertEqual(analyzed_ids, self.pilot_ids)

    def test_instagram_captions_structure_and_constraints(self) -> None:
        reports = self.advisor.analyze_batch(self.pilot_ids)
        for rep in reports:
            cap = rep.instagram_caption

            # Check hashtags (3–5 hashtags)
            hashtags = [w for w in cap.split() if w.startswith("#")]
            self.assertGreaterEqual(
                len(hashtags),
                3,
                f"Product {rep.product_id} has fewer than 3 hashtags ({len(hashtags)})",
            )
            self.assertLessEqual(
                len(hashtags),
                5,
                f"Product {rep.product_id} has more than 5 hashtags ({len(hashtags)})",
            )

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
                    self.assertEqual(data["status"], "draft")

            # Check summary markdown
            summary_path = out_path / "content-summary.md"
            self.assertTrue(summary_path.exists())
            self.assertIn("Content Advisory Pilot", summary_path.read_text(encoding="utf-8"))

            # Check Instagram calendar
            calendar_path = out_path / "instagram-calendar-week1.md"
            self.assertTrue(calendar_path.exists())
            cal_text = calendar_path.read_text(encoding="utf-8")
            self.assertIn("شنبه (Saturday)", cal_text)
            self.assertIn("پنج‌شنبه (Thursday)", cal_text)
            for pid in self.pilot_ids:
                self.assertIn(str(pid), cal_text)

            # Check CSV summary
            csv_path = out_path / "content-summary.csv"
            self.assertTrue(csv_path.exists())


if __name__ == "__main__":
    unittest.main()
