from __future__ import annotations

import re

from .models import ProjectProfile, Scene


def scene_goal(scene: Scene) -> str:
    anchor = scene.visuals[0] if scene.visuals else scene.narration[0]
    anchor = anchor.strip().rstrip(".")
    intent = scene.narration[0].strip().strip('"“”').rstrip(".") if scene.narration else "the tutorial instruction"
    return (
        f"Show {anchor.lower()} so the scene clearly communicates {intent.lower()}, "
        "while keeping the staging concrete, realistic, and continuity-safe."
    )


def shot_title(text: str) -> str:
    base = re.split(r":\s*", text, maxsplit=1)[-1]
    words = re.findall(r"[A-Za-z0-9']+", base)
    return " ".join(word.capitalize() for word in words[:4]) or "Scene Detail"


def derive_shots(scene: Scene, shot_count: int) -> list[str]:
    shots = [line.strip().rstrip(".") + "." for line in scene.visuals[:shot_count] if line.strip()]
    fallback = scene.narration[0].strip().strip('"“”')
    while len(shots) < shot_count:
        shots.append(f"Medium shot: realistic supporting visual for {fallback.lower()}.")
    return shots[:shot_count]


def vendor_neutral_prompt(profile: ProjectProfile, scenes: list[Scene]) -> list[str]:
    lines = [
        f"{profile.title}",
        "Vendor-neutral video-builder prompt",
        "",
        f"Audience: {profile.audience}",
        f"Voice: {profile.voice}",
        f"Language: {profile.language}",
        f"Duration target: {profile.duration_target}",
        f"Aspect ratio: {profile.aspect_ratio}",
        f"Visual style: {profile.visual_style}",
        f"Motion policy: {profile.motion_policy}",
        "",
        "Follow the narration exactly. Treat the visual direction as scene guidance only.",
        "",
    ]
    for scene in scenes:
        lines.append(scene.label())
        lines.append("Narration:")
        lines.extend(scene.narration)
        lines.append("")
        lines.append("Visual:")
        lines.append(" ".join(scene.visuals))
        lines.append("")
    return lines


def invideo_prompt(profile: ProjectProfile, scenes: list[Scene]) -> list[str]:
    lines = [
        "Create a training video using exactly this narration script and scene guide:",
        "VIDEO TITLE (MUST USE THIS EXACTLY, DO NOT CHANGE):",
        f"\"{profile.title}\"",
        "TASK:",
        "Create a fully edited training video from the narration script and scene guide below.",
        "HARD CONSTRAINTS (NARRATION - ALWAYS):",
        "- Use the Narration lines exactly as provided.",
        "- Do not summarize, rewrite, reorder, or add narration.",
        "- Treat every Visual paragraph as shot guidance only.",
        "",
        "SCRIPT:",
        '"""',
    ]
    for scene in scenes:
        lines.append(scene.label())
        lines.append("")
        lines.append("Narration:")
        lines.extend(scene.narration)
        lines.append("")
        lines.append("Visual:")
        lines.append(" ".join(scene.visuals))
        lines.append("")
    lines.append('"""')
    return lines


def visual_pack(profile: ProjectProfile, scenes: list[Scene]) -> list[str]:
    lines = [
        profile.title,
        "Step 5 Visual Generative Prompts",
        "",
        f"Global instruction: {profile.motion_policy}",
        "",
    ]
    for scene in scenes:
        shots = derive_shots(scene, profile.default_shot_count)
        lines.extend(
            [
                scene.label(),
                "Narrator input",
                *scene.narration,
                "Cleaned visuals input",
                *scene.visuals,
                "",
                "Scene goal",
                scene_goal(scene),
                "",
                f"{profile.default_shot_count}-shot montage (all {profile.aspect_ratio} landscape)",
            ]
        )
        for idx, shot in enumerate(shots, start=1):
            lines.append(f"{idx}. Shot {idx} - {shot_title(shot)}: {shot}")
        lines.extend(
            [
                "",
                f"Multi-image prompt text ({profile.default_shot_count} images, {profile.aspect_ratio})",
                f"Create {profile.default_shot_count} separate {profile.aspect_ratio} landscape images, each as a standalone frame. Do not combine them into a collage.",
            ]
        )
        for idx, shot in enumerate(shots, start=1):
            lines.extend(
                [
                    f"{idx}) {shot}",
                    "Wardrobe/PPE: keep people, wardrobe, tools, and context consistent with the tutorial step.",
                    f"Environment: match the project environment and maintain continuity from the surrounding scenes.",
                    "Safety: respect the configured forbidden-visual policy and avoid overlays, logos, or misleading staging.",
                    "Framing: use the shot type described.",
                ]
            )
        lines.extend(
            [
                f"Photo-realistic, real-world live-action style. No text, captions, labels, logos, watermarks, or decorative overlays. All images {profile.aspect_ratio} landscape.",
                "",
                f"Single-shot video prompts ({profile.default_shot_count} shots)",
            ]
        )
        for idx, shot in enumerate(shots, start=1):
            lines.extend(
                [
                    f"Shot {idx}",
                    f"Video creation prompt: {shot} {profile.aspect_ratio} landscape.",
                    f"Who: people and roles appropriate for {profile.audience}.",
                    "What: simple, controlled action only, with minimal movement.",
                    "Where: stay consistent with the established scene environment.",
                    "Safety: avoid overlays, logos, unsafe staging, and continuity breaks.",
                    "Camera is locked off or moves very slowly with stable framing.",
                    "Photo-realistic live-action style with no on-screen text or graphic overlays.",
                ]
            )
        lines.append("")
    return lines


def image_only_export(profile: ProjectProfile, scenes: list[Scene]) -> list[str]:
    lines = [profile.title, "Step 6 Image-Only Prompt Export", ""]
    for scene in scenes:
        shots = derive_shots(scene, profile.default_shot_count)
        lines.extend(
            [
                scene.label(),
                f"Multi-image prompt text ({profile.default_shot_count} images, {profile.aspect_ratio})",
                f"Create {profile.default_shot_count} separate {profile.aspect_ratio} landscape images, each as a standalone frame. Do not combine them into a collage.",
            ]
        )
        for idx, shot in enumerate(shots, start=1):
            lines.extend(
                [
                    f"{idx}) {shot}",
                    "Wardrobe/PPE: keep people, wardrobe, tools, and context consistent with the tutorial step.",
                    "Environment: match the project environment and maintain continuity from the surrounding scenes.",
                    "Safety: avoid overlays, logos, and misleading staging.",
                    "Framing: use the shot type described.",
                ]
            )
        lines.append(
            f"Photo-realistic, real-world live-action style. No text, captions, labels, logos, watermarks, or decorative overlays. All images {profile.aspect_ratio} landscape."
        )
        lines.append("")
    return lines
