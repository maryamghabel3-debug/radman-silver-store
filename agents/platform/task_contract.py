"""
Task Contract & Execution Models
================================
Defines structured dataclasses for task briefs, execution plans, steps,
and skill results within the RADMAN Agent Platform.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from agents.platform.approval_gate import ApprovalGateEngine
from agents.platform.registry import AgentRegistry


class TaskStatus(str, enum.Enum):
    CREATED = "CREATED"
    PLANNED = "PLANNED"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass
class TaskBrief:
    task_id: str
    objective: str
    target_skill: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    requester: str = "agent-orchestrator"
    risk_level: str = "LOW"
    dry_run: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "objective": self.objective,
            "target_skill": self.target_skill,
            "context": self.context,
            "requester": self.requester,
            "risk_level": self.risk_level,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskBrief:
        return cls(
            task_id=data["task_id"],
            objective=data["objective"],
            target_skill=data.get("target_skill"),
            context=data.get("context", {}),
            requester=data.get("requester", "agent-orchestrator"),
            risk_level=data.get("risk_level", "LOW"),
            dry_run=bool(data.get("dry_run", True)),
        )


@dataclass
class TaskStep:
    step_index: int
    skill: str
    action: str
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    requires_gate: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "skill": self.skill,
            "action": self.action,
            "description": self.description,
            "params": self.params,
            "requires_gate": self.requires_gate,
        }


@dataclass
class TaskPlan:
    plan_id: str
    task_id: str
    routed_skill: str
    objective: str
    steps: List[TaskStep] = field(default_factory=list)
    required_gates: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PLANNED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "routed_skill": self.routed_skill,
            "objective": self.objective,
            "steps": [s.to_dict() for s in self.steps],
            "required_gates": self.required_gates,
            "status": self.status.value,
        }


@dataclass
class SkillResult:
    task_id: str
    skill_id: str
    action: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "skill_id": self.skill_id,
            "action": self.action,
            "success": self.success,
            "output": self.output,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "errors": self.errors,
        }


def build_plan_for_task(
    brief: TaskBrief,
    registry: AgentRegistry,
    gate_engine: ApprovalGateEngine,
) -> TaskPlan:
    """Orchestrator plan constructor."""
    routed_skill = registry.route_task(brief.objective, brief.target_skill)
    plan_id = f"PLAN-{brief.task_id}"

    steps: List[TaskStep] = []
    required_gates: List[str] = []

    # Step 1: Always preflight QA / rule check
    steps.append(
        TaskStep(
            step_index=1,
            skill="radman-qa-guard",
            action="preflight_compliance_check",
            description="Verify input context against RADMAN business rules",
            params={"context": brief.context},
        )
    )

    # Step 2: Primary skill action
    primary_action = f"execute_{routed_skill.replace('radman-', '').replace('-', '_')}"
    gate_eval = gate_engine.evaluate_action(primary_action, brief.context)
    step_gate = None
    if gate_eval.requires_approval:
        step_gates = [g.gate_id for g in gate_eval.triggered_gates]
        required_gates.extend(step_gates)
        step_gate = step_gates[0] if step_gates else None

    steps.append(
        TaskStep(
            step_index=2,
            skill=routed_skill,
            action=primary_action,
            description=f"Execute core skill action for {routed_skill}",
            params={"context": brief.context},
            requires_gate=step_gate,
        )
    )

    # Step 3: Post-execution QA verification & manifest update
    steps.append(
        TaskStep(
            step_index=3,
            skill="radman-qa-guard",
            action="post_execution_audit",
            description="Audit output artifacts for content safety and gate conformance",
            params={},
        )
    )

    # Set status
    status = TaskStatus.AWAITING_APPROVAL if required_gates else TaskStatus.READY_FOR_EXECUTION

    return TaskPlan(
        plan_id=plan_id,
        task_id=brief.task_id,
        routed_skill=routed_skill,
        objective=brief.objective,
        steps=steps,
        required_gates=list(set(required_gates)),
        status=status,
    )
