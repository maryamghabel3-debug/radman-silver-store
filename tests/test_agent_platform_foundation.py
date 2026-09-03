"""
Unit and Integration Tests for RADMAN Agent Platform Foundation
==============================================================
Validates agent registry, business rules engine, approval gates,
task planning contracts, artifact manifests, and dry-run execution.

Runnable via:
  pytest tests/test_agent_platform_foundation.py
  python tests/test_agent_platform_foundation.py
"""

import os
import sys
import unittest
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.platform.registry import AgentRegistry, SkillDefinition
from agents.platform.business_rules import (
    RadmanBusinessRules,
    PricingValidationResult,
    ContentValidationResult,
    ProductValidationResult,
)
from agents.platform.approval_gate import (
    ApprovalGateEngine,
    GateEvaluationResult,
    ApprovalGateDefinition,
)
from agents.platform.task_contract import (
    TaskBrief,
    TaskPlan,
    TaskStep,
    TaskStatus,
    build_plan_for_task,
)
from agents.platform.artifact_manifest import (
    ArtifactManifest,
    MediaManifest,
    ArtifactItem,
)
from agents.platform.dry_run import run_dry_run_demonstration


class TestAgentRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = AgentRegistry()

    def test_registry_contains_all_six_skills(self) -> None:
        expected_skills = [
            "radman-orchestrator",
            "radman-seo-agent",
            "radman-content-agent",
            "radman-sales-agent",
            "radman-media-agent",
            "radman-qa-guard",
        ]
        skills = self.registry.list_skills()
        for skill in expected_skills:
            self.assertIn(skill, skills)
            skill_def = self.registry.get_skill(skill)
            self.assertIsNotNone(skill_def)
            self.assertTrue(len(skill_def.capabilities) > 0)
            self.assertTrue(bool(skill_def.description))

    def test_registry_contains_standalone_agents(self) -> None:
        expected_standalone = [
            "order_watch",
            "price_engine",
            "stock_guard",
            "excel_product_pipeline",
            "product_seo",
            "product_seo_qa",
        ]
        standalone = self.registry.list_standalone_agents()
        for agent in expected_standalone:
            self.assertIn(agent, standalone)
            agent_def = self.registry.get_standalone_agent(agent)
            self.assertIsNotNone(agent_def)
            self.assertTrue(bool(agent_def.file))

    def test_registry_validation_passes(self) -> None:
        self.assertTrue(self.registry.validate_registry())

    def test_task_routing_by_keywords(self) -> None:
        self.assertEqual(self.registry.route_task("Optimize Rank Math SEO title"), "radman-seo-agent")
        self.assertEqual(self.registry.route_task("Write Instagram caption and luxury blog story"), "radman-content-agent")
        self.assertEqual(self.registry.route_task("Customer inquiry on ring sizing and silver care"), "radman-sales-agent")
        self.assertEqual(self.registry.route_task("Verify image watermark removal and manifest"), "radman-media-agent")
        self.assertEqual(self.registry.route_task("Run preflight QA compliance check"), "radman-qa-guard")
        self.assertEqual(self.registry.route_task("Coordinate general operations"), "radman-orchestrator")

    def test_task_routing_explicit_target(self) -> None:
        self.assertEqual(
            self.registry.route_task("Any general query", target_skill="radman-seo-agent"),
            "radman-seo-agent",
        )


class TestRadmanBusinessRules(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = RadmanBusinessRules()

    def test_gram_rates(self) -> None:
        self.assertEqual(self.rules.get_gram_rate("standard"), 650_000)
        self.assertEqual(self.rules.get_gram_rate("unknown"), 650_000)
        self.assertEqual(self.rules.get_gram_rate("large_stone"), 590_000)
        self.assertEqual(self.rules.get_gram_rate("سنگ درشت"), 590_000)

    def test_pricing_floor_calculation(self) -> None:
        # Standard: 10g * 650,000 = 6,500,000
        floor_std = self.rules.calculate_price_floor(weight_grams=10.0, stone_type="standard")
        self.assertEqual(floor_std, 6_500_000)

        # Large stone: 10g * 590,000 = 5,900,000
        floor_large = self.rules.calculate_price_floor(weight_grams=10.0, stone_type="large_stone")
        self.assertEqual(floor_large, 5_900_000)

        # Legacy price max rule: legacy = 7,000,000 > floor (6,500,000)
        floor_max = self.rules.calculate_price_floor(weight_grams=10.0, stone_type="standard", legacy_price=7_000_000)
        self.assertEqual(floor_max, 7_000_000)

        # Legacy price < computed floor -> computed floor wins
        floor_max2 = self.rules.calculate_price_floor(weight_grams=10.0, stone_type="standard", legacy_price=5_000_000)
        self.assertEqual(floor_max2, 6_500_000)

    def test_sale_price_is_strictly_forbidden(self) -> None:
        res = self.rules.validate_pricing(
            proposed_price_toman=7_000_000,
            weight_grams=10.0,
            sale_price="6500000",
        )
        self.assertFalse(res.is_valid)
        self.assertTrue(any("sale_price" in v for v in res.violations))

    def test_price_below_floor_is_rejected(self) -> None:
        res = self.rules.validate_pricing(
            proposed_price_toman=5_000_000,  # Floor is 6,500,000
            weight_grams=10.0,
        )
        self.assertFalse(res.is_valid)
        self.assertTrue(any("below minimum price floor" in v for v in res.violations))

    def test_large_price_variance_triggers_gate(self) -> None:
        # 10% change from 6,500,000 to 7_200_000
        res = self.rules.validate_pricing(
            proposed_price_toman=7_200_000,
            weight_grams=10.0,
            baseline_price=6_500_000,
        )
        self.assertTrue(res.is_valid)
        self.assertEqual(res.requires_gate, "GATE_PRICE_CHANGE_LARGE")
        self.assertGreater(res.variance_ratio, 0.05)

    def test_small_price_variance_does_not_trigger_gate(self) -> None:
        # ~2% change from 6,500,000 to 6,630,000
        res = self.rules.validate_pricing(
            proposed_price_toman=6_630_000,
            weight_grams=10.0,
            baseline_price=6_500_000,
        )
        self.assertTrue(res.is_valid)
        self.assertIsNone(res.requires_gate)

    def test_content_safety_prohibited_phone_numbers(self) -> None:
        bad_texts = [
            "جهت سفارش با 09123456789 تماس بگیرید",
            "پشتیبانی در واتساپ: +989123456789",
            "شماره تماس: ۰۹۱۲۳۴۵۶۷۸۹",
        ]
        for txt in bad_texts:
            res = self.rules.validate_content(txt)
            self.assertFalse(res.is_valid, f"Failed to reject: {txt}")
            self.assertTrue(any("telephone or mobile" in v for v in res.violations))

    def test_content_safety_prohibited_shipping_promises(self) -> None:
        bad_texts = [
            "خرید انگشتر با ارسال فوری تضمینی در سراسر کشور",
            "تحویل ۲۴ ساعته درب منزل",
            "ارسال همان روز پس از ثبت سفارش",
        ]
        for txt in bad_texts:
            res = self.rules.validate_content(txt)
            self.assertFalse(res.is_valid, f"Failed to reject: {txt}")
            self.assertTrue(any("shipping guarantee" in v for v in res.violations))

    def test_content_safety_prohibited_warranty_claims(self) -> None:
        bad_texts = [
            "این انگشتر دارای گارانتی مادام‌العمر و ضمانت همیشگی می‌باشد",
            "تضمین ۱۰۰٪ بدون تغییر رنگ برای تمام محصولات",
            "غیر قابل شکستن با ضمانت بی‌قید و شرط",
        ]
        for txt in bad_texts:
            res = self.rules.validate_content(txt)
            self.assertFalse(res.is_valid, f"Failed to reject: {txt}")
            self.assertTrue(any("warranty claim" in v for v in res.violations))

    def test_content_safety_clean_text_passes(self) -> None:
        clean_text = "انگشتر نقره مردانه عقیق سرخ یمنی با عیار ۹۲۵ و طراحی فاخر رادمان سیلور."
        res = self.rules.validate_content(clean_text)
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.violations), 0)

    def test_product_payload_full_validation_pass(self) -> None:
        payload = {
            "product_id": 65,
            "regular_price": 7_280_000,
            "weight_grams": 11.2,
            "stone_type": "standard",
            "status": "draft",
            "stock_quantity": 1,
            "sale_price": None,
            "description": "انگشتر نقره مردانه عقیق یمنی عیار ۹۲۵ اصل فاخر.",
        }
        res = self.rules.validate_product_payload(payload, baseline_price=7_280_000)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.verdict, "PASS")
        self.assertEqual(len(res.blockers), 0)

    def test_product_payload_validation_blocks_bad_stock_and_sale_price(self) -> None:
        payload = {
            "product_id": 65,
            "regular_price": 7_280_000,
            "weight_grams": 11.2,
            "status": "draft",
            "stock_quantity": 5,  # Bad: not 1:1
            "sale_price": "6000000",  # Bad: sale_price
            "description": "تماس با 09121111111",  # Bad: phone
        }
        res = self.rules.validate_product_payload(payload)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.verdict, "BLOCKED")
        self.assertIn("SALE_PRICE_NOT_ALLOWED", res.blockers)
        self.assertIn("STOCK_MODEL_VIOLATION", res.blockers)
        self.assertIn("PROHIBITED_CONTENT_DETECTED", res.blockers)


class TestApprovalGateEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.gate_engine = ApprovalGateEngine()

    def test_all_five_gates_loaded(self) -> None:
        expected_gates = [
            "GATE_PUBLISH_PRODUCT",
            "GATE_PRICE_CHANGE_LARGE",
            "GATE_MEDIA_REPLACE",
            "GATE_AI_IMAGE_REPLACE",
            "GATE_DIRECT_MUTATION",
        ]
        gates = self.gate_engine.list_gates()
        for gate in expected_gates:
            self.assertIn(gate, gates)
            gdef = self.gate_engine.get_gate(gate)
            self.assertIsNotNone(gdef)
            self.assertTrue(gdef.blocking)

    def test_publish_action_triggers_gate(self) -> None:
        res = self.gate_engine.evaluate_action("publish_product", {"status": "publish"})
        self.assertTrue(res.requires_approval)
        self.assertTrue(any(g.gate_id == "GATE_PUBLISH_PRODUCT" for g in res.triggered_gates))

    def test_price_change_above_5_percent_triggers_gate(self) -> None:
        res = self.gate_engine.evaluate_action(
            "update_price",
            {"baseline_price": 1_000_000, "proposed_price": 1_100_000},
        )
        self.assertTrue(res.requires_approval)
        self.assertTrue(any(g.gate_id == "GATE_PRICE_CHANGE_LARGE" for g in res.triggered_gates))

    def test_media_replace_triggers_gate(self) -> None:
        res = self.gate_engine.evaluate_action("update_catalog_media", {"replace_media": True})
        self.assertTrue(res.requires_approval)
        self.assertTrue(any(g.gate_id == "GATE_MEDIA_REPLACE" for g in res.triggered_gates))

    def test_ai_image_replace_triggers_gate(self) -> None:
        res = self.gate_engine.evaluate_action("clean_image", {"is_ai_image_replacement": True})
        self.assertTrue(res.requires_approval)
        self.assertTrue(any(g.gate_id == "GATE_AI_IMAGE_REPLACE" for g in res.triggered_gates))

    def test_direct_mutation_triggers_gate(self) -> None:
        res = self.gate_engine.evaluate_action("deploy_db_migration", {"direct_mutation": True})
        self.assertTrue(res.requires_approval)
        self.assertTrue(any(g.gate_id == "GATE_DIRECT_MUTATION" for g in res.triggered_gates))

    def test_safe_read_only_action_no_gate(self) -> None:
        res = self.gate_engine.evaluate_action("generate_seo_metadata", {"product_id": 65})
        self.assertFalse(res.requires_approval)
        self.assertEqual(len(res.triggered_gates), 0)


class TestTaskContractsAndPlanning(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.gate_engine = ApprovalGateEngine()

    def test_build_plan_for_safe_task(self) -> None:
        brief = TaskBrief(
            task_id="TASK-TEST-001",
            objective="Generate Persian SEO title and meta description",
            target_skill="radman-seo-agent",
            context={"product_id": 65},
        )
        plan = build_plan_for_task(brief, self.registry, self.gate_engine)
        self.assertEqual(plan.task_id, "TASK-TEST-001")
        self.assertEqual(plan.routed_skill, "radman-seo-agent")
        self.assertEqual(len(plan.steps), 3)
        self.assertEqual(plan.status, TaskStatus.READY_FOR_EXECUTION)
        self.assertEqual(len(plan.required_gates), 0)

    def test_build_plan_for_gated_task(self) -> None:
        brief = TaskBrief(
            task_id="TASK-TEST-002",
            objective="Replace catalog image with new manifest",
            target_skill="radman-media-agent",
            context={"product_id": 137, "replace_media": True},
        )
        plan = build_plan_for_task(brief, self.registry, self.gate_engine)
        self.assertEqual(plan.routed_skill, "radman-media-agent")
        self.assertEqual(plan.status, TaskStatus.AWAITING_APPROVAL)
        self.assertIn("GATE_MEDIA_REPLACE", plan.required_gates)

    def test_task_brief_serialization(self) -> None:
        brief = TaskBrief(
            task_id="TASK-SERIAL-001",
            objective="Customer size guidance",
            target_skill="radman-sales-agent",
            context={"size": 60},
        )
        d = brief.to_dict()
        reconstructed = TaskBrief.from_dict(d)
        self.assertEqual(brief.task_id, reconstructed.task_id)
        self.assertEqual(brief.objective, reconstructed.objective)
        self.assertEqual(brief.target_skill, reconstructed.target_skill)


class TestArtifactManifest(unittest.TestCase):
    def test_manifest_lifecycle(self) -> None:
        manifest = ArtifactManifest(
            manifest_id="MAN-001",
            task_id="TASK-001",
            producer_skill="radman-seo-agent",
        )
        item = ArtifactItem(
            artifact_id="ART-001",
            artifact_type="seo_metadata",
            file_path="outbox/seo_65.json",
            description="Generated Rank Math SEO payload",
        )
        media = MediaManifest(
            product_id=65,
            sku="RAD-65",
            primary_image="media/p65/primary.webp",
            geometry_locked=True,
        )
        manifest.add_artifact(item)
        manifest.add_media_manifest(media)

        d = manifest.to_dict()
        self.assertEqual(d["manifest_id"], "MAN-001")
        self.assertEqual(len(d["items"]), 1)
        self.assertEqual(len(d["media_manifests"]), 1)
        self.assertEqual(d["items"][0]["artifact_id"], "ART-001")


class TestDryRunDemonstration(unittest.TestCase):
    def test_dry_run_executes_successfully(self) -> None:
        exit_code = run_dry_run_demonstration()
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
