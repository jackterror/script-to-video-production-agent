from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .hashing import narration_hash


@dataclass
class Scene:
    number: int
    narration: list[str]
    visuals: list[str]
    narration_sha256: str = ""
    notes: list[str] = field(default_factory=list)

    def finalize(self) -> "Scene":
        self.narration_sha256 = narration_hash(self.narration)
        return self

    def label(self) -> str:
        return f"Scene {self.number}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Scene":
        return cls(
            number=int(payload["number"]),
            narration=list(payload["narration"]),
            visuals=list(payload["visuals"]),
            narration_sha256=str(payload.get("narration_sha256", "")),
            notes=list(payload.get("notes", [])),
        ).finalize()


@dataclass
class ReviewIssue:
    scene_number: int
    offending_block: str
    reasons: list[str]
    suggested_visuals: list[str]
    severity: str = "medium"

    def label(self) -> str:
        return f"Scene {self.scene_number}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewDecision:
    scene_number: int
    decision: str
    note: str = ""


@dataclass
class ProjectProfile:
    project_id: str
    title: str
    tutorial_type: str
    audience: str
    language: str = "English"
    voice: str = "Neutral professional narrator"
    duration_target: str = "3-5 minutes"
    aspect_ratio: str = "16:9"
    default_shot_count: int = 4
    visual_style: str = "Photorealistic, real-world live-action"
    motion_policy: str = (
        "Keep movement subtle and minimal: small hand adjustments, short head turns, slow walking only. "
        "No running, no exaggerated gestures, and no distracting camera motion."
    )
    brand_rules: list[str] = field(default_factory=list)
    forbidden_visuals: list[str] = field(default_factory=list)
    provider_budget_policy: str = "Require explicit approval before paid generation."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectProfile":
        return cls(**payload)


@dataclass
class ProjectBundle:
    profile: ProjectProfile
    scenes: list[Scene]
    source_path: Path | None = None

    def narration_sha256(self) -> str:
        joined = "\n\n".join(scene.narration_sha256 or scene.finalize().narration_sha256 for scene in self.scenes)
        from .hashing import sha256_text

        return sha256_text(joined)
