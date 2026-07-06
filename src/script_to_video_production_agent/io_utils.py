from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from docx import Document  # type: ignore

from .models import ProjectBundle, ProjectProfile, Scene


SCENE_RE = re.compile(r"^Scene\s+(\d+)\s*$", re.IGNORECASE)


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    return path.read_text(encoding="utf-8")


def _non_empty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def _first_sentence(text: str) -> str:
    bits = re.split(r"(?<=[.!?])\s+", text.strip())
    return bits[0].strip() if bits and bits[0].strip() else text.strip()


def _provisional_visuals(narration_lines: list[str], tutorial_type: str) -> list[str]:
    joined = " ".join(line.strip().strip('"“”') for line in narration_lines if line.strip())
    sentence = _first_sentence(joined)
    if tutorial_type == "software":
        return [
            f"Show the software interface while the operator performs the step related to: {sentence}",
            "Keep the interface readable, realistic, and free of added overlays or decorative graphics.",
        ]
    return [
        f"Show a realistic physical action or environment beat that supports: {sentence}",
        "Keep the environment, tools, wardrobe, and safety behavior consistent with the tutorial topic.",
    ]


def parse_scenes_from_text(text: str, tutorial_type: str) -> list[Scene]:
    lines = _non_empty_lines(text)
    scenes: list[Scene] = []
    idx = 0
    current_number: int | None = None
    narration: list[str] = []
    visuals: list[str] = []
    mode: str | None = None

    while idx < len(lines):
        raw = lines[idx].strip()
        idx += 1
        if not raw:
            continue
        scene_match = SCENE_RE.match(raw)
        if scene_match:
            if current_number is not None:
                scenes.append(Scene(current_number, narration[:], visuals[:] or _provisional_visuals(narration, tutorial_type)).finalize())
            current_number = int(scene_match.group(1))
            narration = []
            visuals = []
            mode = None
            continue
        lowered = raw.lower()
        if lowered == "narrator:" or lowered == "narration:" or raw == "** Narrator: **":
            mode = "narration"
            continue
        if lowered == "visuals:" or lowered == "visual:" or raw == "[ ** Visuals: **":
            mode = "visuals"
            continue
        if raw == "]":
            mode = None
            continue
        if mode == "narration":
            narration.append(raw)
            continue
        if mode == "visuals":
            visuals.append(re.sub(r"^[—–-]\s*", "", raw))
            continue

    if current_number is not None:
        scenes.append(Scene(current_number, narration[:], visuals[:] or _provisional_visuals(narration, tutorial_type)).finalize())

    if scenes:
        return scenes

    # Fallback. Treat narration paragraphs as scenes.
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocks = [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]
    fallback_scenes: list[Scene] = []
    for number, block in enumerate(blocks, start=1):
        narration_lines = [line.strip() for line in block.splitlines() if line.strip()]
        fallback_scenes.append(
            Scene(number, narration_lines, _provisional_visuals(narration_lines, tutorial_type)).finalize()
        )
    return fallback_scenes


def load_profile(path: Path) -> ProjectProfile:
    return ProjectProfile.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_bundle_from_source(source_path: Path, profile: ProjectProfile) -> ProjectBundle:
    scenes = parse_scenes_from_text(read_text(source_path), profile.tutorial_type)
    return ProjectBundle(profile=profile, scenes=scenes, source_path=source_path)


def write_markdown(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
