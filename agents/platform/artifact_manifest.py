"""
Artifact & Media Manifest Module
================================
Tracks generated deliverables, media assets, and preflight manifests
ensuring structured provenance for all autonomous agent outputs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ArtifactItem:
    artifact_id: str
    artifact_type: str  # report, json_manifest, css, markdown, seo_meta, etc.
    file_path: str
    description: str
    sha256_hash: str = ""
    size_bytes: int = 0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "file_path": self.file_path,
            "description": self.description,
            "sha256_hash": self.sha256_hash,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
        }


@dataclass
class MediaManifest:
    product_id: int
    sku: str
    primary_image: str
    gallery_images: List[str] = field(default_factory=list)
    social_assets: List[str] = field(default_factory=list)
    geometry_locked: bool = True
    fidelity_status: str = "FIDELITY_VERIFIED"
    requires_gate: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "sku": self.sku,
            "primary_image": self.primary_image,
            "gallery_images": self.gallery_images,
            "social_assets": self.social_assets,
            "geometry_locked": self.geometry_locked,
            "fidelity_status": self.fidelity_status,
            "requires_gate": self.requires_gate,
            "warnings": self.warnings,
        }


@dataclass
class ArtifactManifest:
    manifest_id: str
    task_id: str
    producer_skill: str
    items: List[ArtifactItem] = field(default_factory=list)
    media_manifests: List[MediaManifest] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_artifact(self, item: ArtifactItem) -> None:
        self.items.append(item)

    def add_media_manifest(self, mm: MediaManifest) -> None:
        self.media_manifests.append(mm)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "task_id": self.task_id,
            "producer_skill": self.producer_skill,
            "items": [it.to_dict() for it in self.items],
            "media_manifests": [mm.to_dict() for mm in self.media_manifests],
            "metadata": self.metadata,
        }

    def save_to_file(self, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
