"""
RADMAN SILVER 925 — Agent Platform Foundation
=============================================
A lightweight, validation-first, human-in-the-loop (HITL) agent foundation.

Core modules:
- registry: Skill & standalone agent registration and lookup
- business_rules: Deterministic validation of Radman business rules
- approval_gate: HITL gate definitions and evaluation
- task_contract: Task brief, task plan, and execution models
- artifact_manifest: Artifact tracking and media manifests
- dry_run: Multi-skill dry-run orchestrator and demonstration runner
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "RADMAN Engineering"

from agents.platform.registry import AgentRegistry, SkillDefinition
from agents.platform.business_rules import (
    RadmanBusinessRules,
    PricingValidationResult,
    ContentValidationResult,
    ProductValidationResult,
)
from agents.platform.approval_gate import ApprovalGateEngine, GateEvaluationResult
from agents.platform.task_contract import (
    TaskBrief,
    TaskPlan,
    TaskStep,
    SkillResult,
    TaskStatus,
)
from agents.platform.artifact_manifest import (
    ArtifactManifest,
    MediaManifest,
    ArtifactItem,
)

__all__ = [
    "__version__",
    "AgentRegistry",
    "SkillDefinition",
    "RadmanBusinessRules",
    "PricingValidationResult",
    "ContentValidationResult",
    "ProductValidationResult",
    "ApprovalGateEngine",
    "GateEvaluationResult",
    "TaskBrief",
    "TaskPlan",
    "TaskStep",
    "SkillResult",
    "TaskStatus",
    "ArtifactManifest",
    "MediaManifest",
    "ArtifactItem",
]
