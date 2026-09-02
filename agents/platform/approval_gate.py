"""
Approval Gate Engine
====================
Manages Human-In-The-Loop (HITL) approval gates and evaluates whether proposed
agent actions require explicit store owner sign-off.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ApprovalGateDefinition:
    gate_id: str
    name: str
    risk_level: str
    approver: str
    description: str
    blocking: bool = True
    threshold_variance_ratio: Optional[float] = None
    required_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "risk_level": self.risk_level,
            "approver": self.approver,
            "description": self.description,
            "blocking": self.blocking,
            "threshold_variance_ratio": self.threshold_variance_ratio,
            "required_evidence": self.required_evidence,
        }


@dataclass
class GateEvaluationResult:
    requires_approval: bool
    triggered_gates: List[ApprovalGateDefinition] = field(default_factory=list)
    blocking: bool = False
    reasons: List[str] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    approval_id: str
    gate_id: str
    action: str
    summary: str
    context: Dict[str, Any]
    status: str = "PENDING_REVIEW"
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "gate_id": self.gate_id,
            "action": self.action,
            "summary": self.summary,
            "context": self.context,
            "status": self.status,
            "created_at": self.created_at,
        }


class ApprovalGateEngine:
    """Evaluates task actions against defined HITL gates."""

    DEFAULT_CONFIG_PATH = Path(".agents/config/approval-gates.json")

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or self._resolve_default_path()
        self._gates: Dict[str, ApprovalGateDefinition] = {}
        self.load()

    def _resolve_default_path(self) -> Path:
        cwd = Path.cwd()
        candidate = cwd / self.DEFAULT_CONFIG_PATH
        if candidate.exists():
            return candidate

        repo_root = Path(__file__).resolve().parent.parent.parent
        candidate = repo_root / self.DEFAULT_CONFIG_PATH
        if candidate.exists():
            return candidate

        return Path(self.DEFAULT_CONFIG_PATH)

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Approval gates config not found at: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._gates = {}
        for gate_id, item in data.get("approval_gates", {}).items():
            self._gates[gate_id] = ApprovalGateDefinition(
                gate_id=gate_id,
                name=item.get("name", gate_id),
                risk_level=item.get("risk_level", "HIGH"),
                approver=item.get("approver", "store_owner"),
                description=item.get("description", ""),
                blocking=bool(item.get("blocking", True)),
                threshold_variance_ratio=item.get("threshold_variance_ratio"),
                required_evidence=item.get("required_evidence", []),
            )

    def get_gate(self, gate_id: str) -> Optional[ApprovalGateDefinition]:
        return self._gates.get(gate_id)

    def list_gates(self) -> List[str]:
        return list(self._gates.keys())

    def evaluate_action(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> GateEvaluationResult:
        """Evaluates an intended action and context against all gates."""
        ctx = context or {}
        triggered: List[ApprovalGateDefinition] = []
        reasons: List[str] = []

        act_lower = action.lower()

        # 1. Product Publication Gate
        if "publish" in act_lower or ctx.get("status") == "publish" or ctx.get("transition_to") == "publish":
            gate = self._gates.get("GATE_PUBLISH_PRODUCT")
            if gate:
                triggered.append(gate)
                reasons.append("Transitioning product to 'publish' requires explicit owner sign-off.")

        # 2. Large Price Variance Gate (>5%)
        price_variance = ctx.get("price_variance_ratio", 0.0)
        baseline_price = ctx.get("baseline_price", 0)
        proposed_price = ctx.get("proposed_price", 0)
        if baseline_price > 0 and proposed_price > 0 and not price_variance:
            price_variance = abs(proposed_price - baseline_price) / float(baseline_price)

        if price_variance > 0.05 or "large_price" in act_lower:
            gate = self._gates.get("GATE_PRICE_CHANGE_LARGE")
            if gate:
                triggered.append(gate)
                reasons.append(f"Price variance ({price_variance * 100:.2f}%) exceeds 5% threshold.")

        # 3. Media Replacement Gate
        if "media_replace" in act_lower or ctx.get("replace_media") is True:
            gate = self._gates.get("GATE_MEDIA_REPLACE")
            if gate:
                triggered.append(gate)
                reasons.append("Catalog media replacement requires owner sign-off.")

        # 4. AI Image Replacement Gate
        if "ai_image_replace" in act_lower or ctx.get("is_ai_image_replacement") is True:
            gate = self._gates.get("GATE_AI_IMAGE_REPLACE")
            if gate:
                triggered.append(gate)
                reasons.append("Replacing authentic photography with AI-generated/cleaned assets requires owner sign-off.")

        # 5. Direct Host Mutation Gate
        if "host_mutation" in act_lower or ctx.get("direct_mutation") is True:
            gate = self._gates.get("GATE_DIRECT_MUTATION")
            if gate:
                triggered.append(gate)
                reasons.append("Direct mutation of host or production database requires owner sign-off.")

        requires_approval = len(triggered) > 0
        blocking = any(g.blocking for g in triggered)

        return GateEvaluationResult(
            requires_approval=requires_approval,
            triggered_gates=triggered,
            blocking=blocking,
            reasons=reasons,
        )
