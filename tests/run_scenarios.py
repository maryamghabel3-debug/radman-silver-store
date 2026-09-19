"""
Mock Scenario Runner for RADMAN SILVER 925 Integration Plan v1
==============================================================
Tests resilience, idempotency, checkpoint recovery, and approval gates
for scenarios S6 through S10 without external dependencies or live network calls.

Runnable via:
  python tests/run_scenarios.py
  pytest tests/run_scenarios.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.platform.approval_gate import ApprovalGateEngine
from agents.platform.business_rules import RadmanBusinessRules
from agents.platform.task_contract import TaskBrief, TaskPlan, TaskStatus, build_plan_for_task
from agents.platform.registry import AgentRegistry


class MockAnalyticsCollector:
    """Simulates analytics data collection with missing telemetry support."""
    @staticmethod
    def get_daily_metrics(date_str: str, has_connection: bool = False) -> Dict[str, Any]:
        if not has_connection:
            return {
                "date": date_str,
                "page_views": "UNKNOWN",
                "unique_visitors": "UNKNOWN",
                "cart_additions": "UNKNOWN",
                "status": "TELEMETRY_DISCONNECTED",
            }
        return {
            "date": date_str,
            "page_views": 120,
            "unique_visitors": 85,
            "cart_additions": 4,
            "status": "TELEMETRY_CONNECTED",
        }


class MockBatchProcessor:
    """Simulates idempotent and checkpoint-aware batch execution."""
    def __init__(self, state_file: Path) -> None:
        self.state_file = state_file

    def load_checkpoint(self) -> Dict[str, Any]:
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"completed_items": [], "last_index": 0}

    def save_checkpoint(self, state: Dict[str, Any]) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def process_items(
        self,
        items: List[int],
        fail_at_index: Optional[int] = None,
        simulate_api_error: bool = False,
    ) -> Dict[str, Any]:
        state = self.load_checkpoint()
        processed_this_run = []
        skipped_this_run = []

        for idx, item_id in enumerate(items, start=1):
            if item_id in state["completed_items"]:
                skipped_this_run.append(item_id)
                continue

            if fail_at_index and idx == fail_at_index:
                # Simulate mid-batch crash
                return {
                    "status": "INTERRUPTED",
                    "completed": state["completed_items"],
                    "processed_now": processed_this_run,
                    "skipped": skipped_this_run,
                    "error": f"Simulated crash at index {idx}",
                }

            if simulate_api_error:
                # Simulate API 429/Timeout with zero state writes
                return {
                    "status": "STOP",
                    "completed": state["completed_items"],
                    "processed_now": processed_this_run,
                    "error": "API_RATE_LIMIT_429",
                }

            # Process successfully
            processed_this_run.append(item_id)
            state["completed_items"].append(item_id)
            state["last_index"] = idx
            self.save_checkpoint(state)

        return {
            "status": "SUCCESS",
            "completed": state["completed_items"],
            "processed_now": processed_this_run,
            "skipped": skipped_this_run,
        }


class TestIntegrationScenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = AgentRegistry()
        self.gate_engine = ApprovalGateEngine()

    def test_s6_missing_visit_data_reports_unknown(self) -> None:
        """S6: When analytics telemetry is unavailable, report UNKNOWN rather than 0."""
        report = MockAnalyticsCollector.get_daily_metrics("2026-09-04", has_connection=False)
        self.assertEqual(report["page_views"], "UNKNOWN")
        self.assertEqual(report["unique_visitors"], "UNKNOWN")
        self.assertNotEqual(report["page_views"], 0)
        self.assertEqual(report["status"], "TELEMETRY_DISCONNECTED")

    def test_s7_price_change_proposal_routes_to_approval_queue(self) -> None:
        """S7: Price adjustments above 5% threshold must route to HITL approval queue."""
        baseline_price = 5_901_000
        proposed_price = 6_600_000  # ~11.8% change (> 5%)

        brief = TaskBrief(
            task_id="TASK-PRICE-ADJUST-001",
            objective="Adjust product price according to spot silver rate update",
            target_skill="radman-orchestrator",
            context={
                "product_id": 275,
                "baseline_price": baseline_price,
                "proposed_price": proposed_price,
                "price_variance_ratio": (proposed_price - baseline_price) / baseline_price,
            },
        )
        plan = build_plan_for_task(brief, self.registry, self.gate_engine)

        self.assertEqual(plan.status, TaskStatus.AWAITING_APPROVAL)
        self.assertIn("GATE_PRICE_CHANGE_LARGE", plan.required_gates)

    def test_s8_idempotent_execution(self) -> None:
        """S8: Re-running the same job must be idempotent (skip duplicate operations)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            processor = MockBatchProcessor(state_file)

            items = [232, 205, 378, 375, 372, 369]

            # Run 1: processes all 6 items
            res1 = processor.process_items(items)
            self.assertEqual(res1["status"], "SUCCESS")
            self.assertEqual(len(res1["processed_now"]), 6)
            self.assertEqual(len(res1["skipped"]), 0)

            # Run 2: skips all 6 items without re-running
            res2 = processor.process_items(items)
            self.assertEqual(res2["status"], "SUCCESS")
            self.assertEqual(len(res2["processed_now"]), 0)
            self.assertEqual(len(res2["skipped"]), 6)

    def test_s9_checkpoint_recovery_after_disconnection(self) -> None:
        """S9: Mid-batch crash at item 4 must resume from item 5 without repeating 1..4."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            processor = MockBatchProcessor(state_file)

            items = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]

            # Run 1: Crash at index 4 (items 101..103 completed)
            res1 = processor.process_items(items, fail_at_index=4)
            self.assertEqual(res1["status"], "INTERRUPTED")
            self.assertEqual(res1["completed"], [101, 102, 103])

            # Run 2: Resume after crash
            res2 = processor.process_items(items)
            self.assertEqual(res2["status"], "SUCCESS")
            self.assertEqual(res2["skipped"], [101, 102, 103])  # items 1..3 skipped
            self.assertEqual(res2["processed_now"], [104, 105, 106, 107, 108, 109, 110])
            self.assertEqual(len(res2["completed"]), 10)

    def test_s10_api_error_handling_and_zero_state_mutation(self) -> None:
        """S10: API 429 or Timeout error halts cleanly with zero state corruption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            processor = MockBatchProcessor(state_file)

            items = [201, 202, 203]
            res = processor.process_items(items, simulate_api_error=True)

            self.assertEqual(res["status"], "STOP")
            self.assertEqual(res["error"], "API_RATE_LIMIT_429")
            self.assertEqual(len(res["completed"]), 0)
            self.assertFalse(state_file.exists())  # No corrupted state written


def run_scenarios() -> int:
    print("=" * 75)
    print("  RADMAN SILVER 925 — MOCK SCENARIO TEST RUNNER (S6..S10)")
    print("=" * 75)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegrationScenarios)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\n" + "=" * 75)
    if result.wasSuccessful():
        print("  ALL SCENARIO TESTS (S6..S10) PASSED SUCCESSFULLY (STATUS: PASS)")
        print("=" * 75)
        return 0
    else:
        print("  SOME SCENARIO TESTS FAILED (STATUS: FAIL)")
        print("=" * 75)
        return 1


if __name__ == "__main__":
    sys.exit(run_scenarios())
