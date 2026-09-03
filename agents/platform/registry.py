"""
Agent & Skill Registry Module
=============================
Loads and manages skill definitions, standalone agents, and metadata contracts
from .agents/config/agent-registry.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SkillDefinition:
    skill_id: str
    name: str
    version: str
    risk_level: str
    requires_owner_approval: bool
    description: str
    capabilities: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    skill_doc: str = ""
    entry_point: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "risk_level": self.risk_level,
            "requires_owner_approval": self.requires_owner_approval,
            "description": self.description,
            "capabilities": self.capabilities,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "skill_doc": self.skill_doc,
            "entry_point": self.entry_point,
        }


@dataclass
class StandaloneAgentDefinition:
    agent_id: str
    file: str
    schedule: str
    purpose: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "file": self.file,
            "schedule": self.schedule,
            "purpose": self.purpose,
        }


class AgentRegistry:
    """Registry managing available skills and standalone agents."""

    DEFAULT_CONFIG_PATH = Path(".agents/config/agent-registry.json")

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or self._resolve_default_path()
        self.version: str = "1.0.0"
        self.platform: str = "RADMAN-AGENT-PLATFORM"
        self.description: str = ""
        self._skills: Dict[str, SkillDefinition] = {}
        self._standalone_agents: Dict[str, StandaloneAgentDefinition] = {}
        self.load()

    def _resolve_default_path(self) -> Path:
        # Check current working directory or traverse upward to repo root
        cwd = Path.cwd()
        candidate = cwd / self.DEFAULT_CONFIG_PATH
        if candidate.exists():
            return candidate
        
        # Check relative to this file
        repo_root = Path(__file__).resolve().parent.parent.parent
        candidate = repo_root / self.DEFAULT_CONFIG_PATH
        if candidate.exists():
            return candidate
        
        return Path(self.DEFAULT_CONFIG_PATH)

    def load(self) -> None:
        """Loads and parses the registry config."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Agent registry config not found at: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.version = data.get("version", "1.0.0")
        self.platform = data.get("platform", "RADMAN-AGENT-PLATFORM")
        self.description = data.get("description", "")

        self._skills = {}
        for skill_id, item in data.get("skills", {}).items():
            self._skills[skill_id] = SkillDefinition(
                skill_id=skill_id,
                name=item.get("name", skill_id),
                version=item.get("version", "1.0.0"),
                risk_level=item.get("risk_level", "LOW"),
                requires_owner_approval=bool(item.get("requires_owner_approval", False)),
                description=item.get("description", ""),
                capabilities=item.get("capabilities", []),
                input_schema=item.get("input_schema", {}),
                output_schema=item.get("output_schema", {}),
                skill_doc=item.get("skill_doc", ""),
                entry_point=item.get("entry_point", ""),
            )

        self._standalone_agents = {}
        for agent_id, item in data.get("standalone_agents", {}).items():
            self._standalone_agents[agent_id] = StandaloneAgentDefinition(
                agent_id=agent_id,
                file=item.get("file", ""),
                schedule=item.get("schedule", ""),
                purpose=item.get("purpose", ""),
            )

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id)

    def list_skills(self) -> List[str]:
        return list(self._skills.keys())

    def get_standalone_agent(self, agent_id: str) -> Optional[StandaloneAgentDefinition]:
        return self._standalone_agents.get(agent_id)

    def list_standalone_agents(self) -> List[str]:
        return list(self._standalone_agents.keys())

    def validate_registry(self) -> bool:
        """Verifies that all core skills and standalone agents are present."""
        required_skills = [
            "radman-orchestrator",
            "radman-seo-agent",
            "radman-geo-agent",
            "radman-aeo-agent",
            "radman-content-agent",
            "radman-sales-agent",
            "radman-media-agent",
            "radman-qa-guard",
        ]
        for req in required_skills:
            if req not in self._skills:
                return False

        required_standalone = [
            "order_watch",
            "price_engine",
            "stock_guard",
            "excel_product_pipeline",
            "product_seo",
            "product_seo_qa",
        ]
        for req in required_standalone:
            if req not in self._standalone_agents:
                return False

        return True

    def route_task(self, objective: str, target_skill: Optional[str] = None) -> str:
        """Determines the appropriate skill for a given task objective."""
        if target_skill and target_skill in self._skills:
            return target_skill

        obj_lower = objective.lower()

        # Check explicit keywords
        if any(k in obj_lower for k in ["geo", "generative engine", "ai overview", "gemini", "perplexity", "citation"]):
            return "radman-geo-agent"
        if any(k in obj_lower for k in ["aeo", "answer engine", "chatgpt", "faq schema", "voice assistant", "direct answer"]):
            return "radman-aeo-agent"
        if any(k in obj_lower for k in ["seo", "rank math", "meta description", "focus keyword", "search console"]):
            return "radman-seo-agent"
        if any(k in obj_lower for k in ["content", "blog", "instagram", "caption", "article", "editorial", "story"]):
            return "radman-content-agent"
        if any(k in obj_lower for k in ["customer", "inquiry", "sales", "size", "sizing", "consultation", "support"]):
            return "radman-sales-agent"
        if any(k in obj_lower for k in ["media", "image", "photo", "watermark", "gallery", "manifest", "fidelity"]):
            return "radman-media-agent"
        if any(k in obj_lower for k in ["qa", "audit", "compliance", "preflight", "check", "verify", "gate"]):
            return "radman-qa-guard"

        return "radman-orchestrator"
