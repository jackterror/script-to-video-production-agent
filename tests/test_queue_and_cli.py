from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from script_to_video_production_agent.cli import main, project_db
from script_to_video_production_agent.io_utils import load_profile
from script_to_video_production_agent.models import ProjectBundle, Scene
from script_to_video_production_agent.prompts import derive_shots
from script_to_video_production_agent.providers import all_capabilities
from script_to_video_production_agent.storage import connect, load_bundle, next_asset, record_attempt, save_bundle, seed_asset_queue, update_approval, retry_target


class QueueAndCliTests(unittest.TestCase):
    def test_queue_seed_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            profile = load_profile(ROOT / "assets/config/examples/physical-process.json")
            scene = Scene(1, ["\"Lock the unit before service.\""], ["Medium shot: technician isolates power."]).finalize()
            bundle = ProjectBundle(profile=profile, scenes=[scene])
            prompts = {1: derive_shots(scene, 4)}
            with connect(tmp_path / "project.sqlite3") as conn:
                save_bundle(conn, bundle)
                seed_asset_queue(conn, bundle, prompts, asset_kind="image")
                seed_asset_queue(conn, bundle, prompts, asset_kind="image")
                row = conn.execute("SELECT COUNT(*) AS count FROM asset_target").fetchone()
                self.assertEqual(int(row["count"]), 4)
                first = next_asset(conn, profile.project_id)
                assert first is not None
                record_attempt(conn, int(first["id"]), "manual", "job-1", "generated", "outputs/file.png")
                update_approval(conn, int(first["id"]), "approved")
                retry_target(conn, int(first["id"]), "needs alternate angle")
                retried = conn.execute("SELECT status, approval_state, last_error FROM asset_target WHERE id = ?", (int(first["id"]),)).fetchone()
                self.assertEqual(retried["status"], "retry")
                self.assertEqual(retried["approval_state"], "approved")
                self.assertEqual(retried["last_error"], "needs alternate angle")

    def test_cli_import_and_queue_next(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo"
            rc = main(
                [
                    "import-script",
                    "--input",
                    str(ROOT / "assets/fixtures/physical-process/source-script.md"),
                    "--config",
                    str(ROOT / "assets/config/examples/physical-process.json"),
                    "--project-dir",
                    str(project_dir),
                ]
            )
            self.assertEqual(rc, 0)
            db = project_db(project_dir)
            with connect(db) as conn:
                bundle = load_bundle(conn, "fixture-physical")
                prompts = {scene.number: derive_shots(scene, bundle.profile.default_shot_count) for scene in bundle.scenes}
                seed_asset_queue(conn, bundle, prompts, asset_kind="image")
            rc = main(
                [
                    "queue-next",
                    "--project-dir",
                    str(project_dir),
                    "--project-id",
                    "fixture-physical",
                ]
            )
            self.assertEqual(rc, 0)
            self.assertTrue((project_dir / "outputs/fixture-physical-clean.docx").exists())

    def test_provider_status_has_manual(self) -> None:
        providers = all_capabilities()
        names = {provider.name for provider in providers}
        self.assertIn("manual", names)
        manual = next(provider for provider in providers if provider.name == "manual")
        self.assertTrue(manual.available)
        self.assertTrue(manual.manual_only)


if __name__ == "__main__":
    unittest.main()
