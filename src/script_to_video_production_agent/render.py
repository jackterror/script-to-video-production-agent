from __future__ import annotations

import json
from pathlib import Path

from docx import Document  # type: ignore
from docx.shared import Pt  # type: ignore

from .io_utils import write_markdown
from .models import ProjectBundle, ReviewIssue, Scene
from .prompts import image_only_export, invideo_prompt, vendor_neutral_prompt, visual_pack


def _doc() -> Document:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Aptos"
    style.font.size = Pt(11)
    props = doc.core_properties
    props.author = "Script-to-Video Production Agent"
    props.company = "Open source"
    props.comments = ""
    props.category = "workflow"
    props.keywords = "script-to-video, open-source"
    return doc


def _save_doc(lines: list[str], path: Path) -> None:
    doc = _doc()
    for line in lines:
        doc.add_paragraph(line)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))


def render_clean_script(bundle: ProjectBundle, docx_path: Path, md_path: Path) -> None:
    lines = [bundle.profile.title, "Step 1 Clean Script", ""]
    for scene in bundle.scenes:
        lines.extend([scene.label(), "Narrator:", *scene.narration, "", "Visuals:", *scene.visuals, "", "--------------------", ""])
    _save_doc(lines, docx_path)
    write_markdown(md_path, lines)


def render_review_sheet(bundle: ProjectBundle, issues: list[ReviewIssue], docx_path: Path, md_path: Path) -> None:
    lines = [bundle.profile.title, "Step 2 Visual Review", ""]
    if not issues:
        lines.extend(["No Step 2 issues found.", "", "Ready to continue on your command."])
    else:
        for issue in issues:
            lines.extend(
                [
                    f"Scene: {issue.label()}",
                    "Offending block:",
                    issue.offending_block,
                    "",
                    "Why it is off:",
                    *[f"- {reason}" for reason in issue.reasons],
                    "",
                    "Suggested replacement:",
                    *issue.suggested_visuals,
                    "",
                    "--------------------",
                    "",
                ]
            )
        lines.extend(["For Next Step", "Copy/Paste below template into prompt window and provide feedback or type [ACCEPT ALL]:", ""])
        lines.append("```text")
        lines.append("Execute on my decisions below.")
        lines.append("")
        for issue in issues:
            lines.extend(
                [
                    f"Scene: {issue.label()}",
                    "Decision (A for Accept, R for Reject, F for Fix):",
                    "Note for Fixes:",
                    "",
                ]
            )
        lines.append("```")
        lines.append("")
        lines.append("Ready to continue on your command.")
    _save_doc(lines, docx_path)
    write_markdown(md_path, lines)


def render_before_after(
    profile_title: str, before_scenes: list[Scene], after_scenes: list[Scene], docx_path: Path, md_path: Path
) -> None:
    lines = [profile_title, "Step 2 Before / After Comparison", ""]
    for before, after in zip(before_scenes, after_scenes):
        lines.extend(
            [
                before.label(),
                "Before visuals:",
                *before.visuals,
                "",
                "After visuals:",
                *after.visuals,
                "",
                "--------------------",
                "",
            ]
        )
    _save_doc(lines, docx_path)
    write_markdown(md_path, lines)


def render_vendor_prompt(bundle: ProjectBundle, docx_path: Path, md_path: Path) -> None:
    lines = vendor_neutral_prompt(bundle.profile, bundle.scenes)
    _save_doc(lines, docx_path)
    write_markdown(md_path, lines)


def render_invideo_prompt(bundle: ProjectBundle, docx_path: Path, md_path: Path) -> None:
    lines = invideo_prompt(bundle.profile, bundle.scenes)
    _save_doc(lines, docx_path)
    write_markdown(md_path, lines)


def render_visual_pack(bundle: ProjectBundle, docx_path: Path, md_path: Path) -> None:
    lines = visual_pack(bundle.profile, bundle.scenes)
    _save_doc(lines, docx_path)
    write_markdown(md_path, lines)


def render_image_only(bundle: ProjectBundle, docx_path: Path, md_path: Path) -> None:
    lines = image_only_export(bundle.profile, bundle.scenes)
    _save_doc(lines, docx_path)
    write_markdown(md_path, lines)


def render_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
