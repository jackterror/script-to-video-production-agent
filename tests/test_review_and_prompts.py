from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from script_to_video_production_agent.models import ProjectBundle, ProjectProfile, ReviewIssue, Scene
from script_to_video_production_agent.prompts import image_only_export, invideo_prompt, vendor_neutral_prompt, visual_pack
from script_to_video_production_agent.render import render_clean_script, render_review_sheet
from script_to_video_production_agent.review import apply_review_decisions, audit_scene, parse_decisions


class ReviewAndPromptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = ProjectProfile(
            project_id="fixture",
            title="Fixture Tutorial",
            tutorial_type="physical",
            audience="operators",
        )
        self.scene = Scene(
            number=1,
            narration=["\"Explain the safe setup step.\""],
            visuals=["Show a title card with bullet points about setup."],
        ).finalize()

    def test_audit_scene_flags_overlays(self) -> None:
        issue = audit_scene(self.scene)
        self.assertIsNotNone(issue)
        assert issue is not None
        self.assertTrue(any("overlay" in reason or "text" in reason for reason in issue.reasons))

    def test_apply_review_decisions_accepts_replacement(self) -> None:
        issue = ReviewIssue(
            scene_number=1,
            offending_block="bad block",
            reasons=["Contains text"],
            suggested_visuals=["Show a technician performing the step.", "Keep staging realistic."],
        )
        decisions = parse_decisions("Scene: Scene 1\nDecision (A for Accept, R for Reject, F for Fix): A\n")
        result = apply_review_decisions([self.scene], [issue], decisions)
        self.assertEqual(result.accepted, [1])
        self.assertEqual(result.updated_scenes[0].visuals[0], "Show a technician performing the step.")

    def test_prompt_exports_keep_scene_labels(self) -> None:
        clean_scene = Scene(
            number=1,
            narration=["\"Explain the safe setup step.\""],
            visuals=["Medium shot: operator checks the panel before starting work."],
        ).finalize()
        lines = vendor_neutral_prompt(self.profile, [clean_scene])
        self.assertIn("Scene 1", lines)
        invideo_lines = invideo_prompt(self.profile, [clean_scene])
        self.assertIn("Visual:", invideo_lines)
        visual_lines = visual_pack(self.profile, [clean_scene])
        self.assertIn("Scene goal", visual_lines)
        image_lines = image_only_export(self.profile, [clean_scene])
        self.assertIn("Multi-image prompt text (4 images, 16:9)", image_lines)

    def test_render_outputs_write_files(self) -> None:
        clean_scene = Scene(
            number=1,
            narration=["\"Explain the safe setup step.\""],
            visuals=["Medium shot: operator checks the panel before starting work."],
        ).finalize()
        bundle = ProjectBundle(profile=self.profile, scenes=[clean_scene])
        issue = ReviewIssue(
            scene_number=1,
            offending_block="bad block",
            reasons=["Contains text"],
            suggested_visuals=["Show a technician performing the step."],
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            render_clean_script(bundle, tmp_path / "clean.docx", tmp_path / "clean.md")
            render_review_sheet(bundle, [issue], tmp_path / "review.docx", tmp_path / "review.md")
            self.assertTrue((tmp_path / "clean.docx").exists())
            self.assertTrue((tmp_path / "clean.md").exists())
            self.assertTrue((tmp_path / "review.docx").exists())
            self.assertTrue((tmp_path / "review.md").exists())


if __name__ == "__main__":
    unittest.main()
