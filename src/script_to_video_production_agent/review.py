from __future__ import annotations

from dataclasses import dataclass
import re

from .models import ReviewDecision, ReviewIssue, Scene


DISALLOWED_PATTERNS = {
    "text or overlay instruction": re.compile(r"\b(text|caption|subtitle|lower third|title card|bullet)\b", re.IGNORECASE),
    "graphic instruction": re.compile(r"\b(icon|graphic|animation|motion graphic|callout|hud)\b", re.IGNORECASE),
    "branding instruction": re.compile(r"\b(logo|watermark)\b", re.IGNORECASE),
}


def suggest_visual_replacement(scene: Scene) -> list[str]:
    anchor = scene.narration[0].strip().strip('"“”') if scene.narration else "the current tutorial step"
    return [
        f"Show a realistic visual moment that supports: {anchor}",
        "Keep the environment, people, wardrobe, products, and continuity consistent with the rest of the tutorial.",
        "Do not use overlays, icons, logos, captions, or decorative graphics.",
    ]


def audit_scene(scene: Scene) -> ReviewIssue | None:
    joined = " ".join(scene.visuals)
    reasons: list[str] = []
    for label, pattern in DISALLOWED_PATTERNS.items():
        if pattern.search(joined):
            reasons.append(f"Contains {label} that should be removed before delivery.")
    if not scene.visuals:
        reasons.append("Visual direction is missing and needs a concrete replacement.")
    if not reasons:
        return None
    offending = [scene.label(), "Narrator:"] + scene.narration + ["", "Visuals:"] + scene.visuals
    return ReviewIssue(
        scene_number=scene.number,
        offending_block="\n".join(offending).strip(),
        reasons=reasons,
        suggested_visuals=suggest_visual_replacement(scene),
    )


def audit_scenes(scenes: list[Scene]) -> list[ReviewIssue]:
    return [issue for scene in scenes if (issue := audit_scene(scene)) is not None]


def parse_decisions(text: str) -> list[ReviewDecision]:
    decisions: list[ReviewDecision] = []
    scene_number: int | None = None
    decision_value = ""
    note_value = ""

    def commit() -> None:
        nonlocal scene_number, decision_value, note_value
        if scene_number is not None and decision_value:
            decisions.append(ReviewDecision(scene_number=scene_number, decision=decision_value.upper(), note=note_value.strip()))
        scene_number = None
        decision_value = ""
        note_value = ""

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"Scene:\s*Scene\s+(\d+)", line, re.IGNORECASE)
        if match:
            commit()
            scene_number = int(match.group(1))
            continue
        if line.lower().startswith("decision"):
            _, _, tail = line.partition(":")
            decision_value = tail.strip()
            continue
        if line.lower().startswith("note for fixes"):
            _, _, tail = line.partition(":")
            note_value = tail.strip()
            continue
    commit()
    return decisions


@dataclass
class ApplyResult:
    updated_scenes: list[Scene]
    accepted: list[int]
    rejected: list[int]
    fix_requested: list[int]


def apply_review_decisions(
    scenes: list[Scene], issues: list[ReviewIssue], decisions: list[ReviewDecision]
) -> ApplyResult:
    scene_map = {scene.number: Scene(scene.number, scene.narration[:], scene.visuals[:], scene.narration_sha256, scene.notes[:]) for scene in scenes}
    issue_map = {issue.scene_number: issue for issue in issues}
    accepted: list[int] = []
    rejected: list[int] = []
    fix_requested: list[int] = []

    for decision in decisions:
        scene = scene_map.get(decision.scene_number)
        if scene is None:
            continue
        normalized = decision.decision.upper()
        if normalized == "A" and decision.scene_number in issue_map:
            scene.visuals = issue_map[decision.scene_number].suggested_visuals[:]
            scene.notes.append("Accepted suggested visual replacement.")
            accepted.append(decision.scene_number)
        elif normalized == "R":
            scene.notes.append("Rejected suggested visual replacement.")
            rejected.append(decision.scene_number)
        elif normalized == "F":
            scene.notes.append(f"Fix requested: {decision.note.strip()}")
            fix_requested.append(decision.scene_number)
        scene.finalize()

    updated = [scene_map[number].finalize() for number in sorted(scene_map)]
    return ApplyResult(updated_scenes=updated, accepted=accepted, rejected=rejected, fix_requested=fix_requested)
