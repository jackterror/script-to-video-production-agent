from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .hashing import prompt_hash
from .models import ProjectBundle, ProjectProfile, ReviewIssue, Scene


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS project (
  project_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  tutorial_type TEXT NOT NULL,
  audience TEXT NOT NULL,
  profile_json TEXT NOT NULL,
  source_path TEXT,
  narration_sha256 TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scene (
  project_id TEXT NOT NULL,
  scene_number INTEGER NOT NULL,
  narration_json TEXT NOT NULL,
  visuals_json TEXT NOT NULL,
  narration_sha256 TEXT NOT NULL,
  notes_json TEXT NOT NULL,
  PRIMARY KEY (project_id, scene_number),
  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_issue (
  project_id TEXT NOT NULL,
  scene_number INTEGER NOT NULL,
  reasons_json TEXT NOT NULL,
  offending_block TEXT NOT NULL,
  suggested_visuals_json TEXT NOT NULL,
  severity TEXT NOT NULL,
  PRIMARY KEY (project_id, scene_number),
  FOREIGN KEY (project_id, scene_number) REFERENCES scene(project_id, scene_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asset_target (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  scene_number INTEGER NOT NULL,
  shot_number INTEGER NOT NULL,
  asset_kind TEXT NOT NULL,
  prompt_text TEXT NOT NULL,
  prompt_sha256 TEXT NOT NULL,
  output_basename TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  approval_state TEXT NOT NULL DEFAULT 'pending',
  provider TEXT,
  job_id TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  output_path TEXT,
  last_error TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id, scene_number, shot_number, asset_kind),
  FOREIGN KEY (project_id, scene_number) REFERENCES scene(project_id, scene_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS provider_job (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_target_id INTEGER NOT NULL,
  provider TEXT NOT NULL,
  job_id TEXT,
  prompt_sha256 TEXT NOT NULL,
  attempt INTEGER NOT NULL,
  status TEXT NOT NULL,
  output_path TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (asset_target_id) REFERENCES asset_target(id) ON DELETE CASCADE
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save_bundle(conn: sqlite3.Connection, bundle: ProjectBundle) -> None:
    import json

    conn.execute(
        """
        INSERT INTO project(project_id, title, tutorial_type, audience, profile_json, source_path, narration_sha256)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
          title=excluded.title,
          tutorial_type=excluded.tutorial_type,
          audience=excluded.audience,
          profile_json=excluded.profile_json,
          source_path=excluded.source_path,
          narration_sha256=excluded.narration_sha256
        """,
        (
            bundle.profile.project_id,
            bundle.profile.title,
            bundle.profile.tutorial_type,
            bundle.profile.audience,
            json.dumps(bundle.profile.to_dict(), ensure_ascii=True),
            str(bundle.source_path) if bundle.source_path else None,
            bundle.narration_sha256(),
        ),
    )
    conn.execute("DELETE FROM scene WHERE project_id = ?", (bundle.profile.project_id,))
    for scene in bundle.scenes:
        conn.execute(
            """
            INSERT INTO scene(project_id, scene_number, narration_json, visuals_json, narration_sha256, notes_json)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                bundle.profile.project_id,
                scene.number,
                json.dumps(scene.narration, ensure_ascii=True),
                json.dumps(scene.visuals, ensure_ascii=True),
                scene.narration_sha256,
                json.dumps(scene.notes, ensure_ascii=True),
            ),
        )
    conn.commit()


def load_bundle(conn: sqlite3.Connection, project_id: str) -> ProjectBundle:
    import json

    project = conn.execute("SELECT * FROM project WHERE project_id = ?", (project_id,)).fetchone()
    if project is None:
        raise KeyError(project_id)
    scenes_rows = conn.execute(
        "SELECT * FROM scene WHERE project_id = ? ORDER BY scene_number ASC", (project_id,)
    ).fetchall()
    profile = ProjectProfile.from_dict(json.loads(project["profile_json"]))
    scenes = [
        Scene(
            number=row["scene_number"],
            narration=json.loads(row["narration_json"]),
            visuals=json.loads(row["visuals_json"]),
            narration_sha256=row["narration_sha256"],
            notes=json.loads(row["notes_json"]),
        )
        for row in scenes_rows
    ]
    return ProjectBundle(profile=profile, scenes=scenes, source_path=Path(project["source_path"]) if project["source_path"] else None)


def save_review_issues(conn: sqlite3.Connection, project_id: str, issues: list[ReviewIssue]) -> None:
    import json

    conn.execute("DELETE FROM review_issue WHERE project_id = ?", (project_id,))
    for issue in issues:
        conn.execute(
            """
            INSERT INTO review_issue(project_id, scene_number, reasons_json, offending_block, suggested_visuals_json, severity)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                issue.scene_number,
                json.dumps(issue.reasons, ensure_ascii=True),
                issue.offending_block,
                json.dumps(issue.suggested_visuals, ensure_ascii=True),
                issue.severity,
            ),
        )
    conn.commit()


def load_review_issues(conn: sqlite3.Connection, project_id: str) -> list[ReviewIssue]:
    import json

    rows = conn.execute("SELECT * FROM review_issue WHERE project_id = ? ORDER BY scene_number ASC", (project_id,)).fetchall()
    return [
        ReviewIssue(
            scene_number=row["scene_number"],
            reasons=json.loads(row["reasons_json"]),
            offending_block=row["offending_block"],
            suggested_visuals=json.loads(row["suggested_visuals_json"]),
            severity=row["severity"],
        )
        for row in rows
    ]


def overwrite_scenes(conn: sqlite3.Connection, bundle: ProjectBundle) -> None:
    save_bundle(conn, bundle)


def seed_asset_queue(
    conn: sqlite3.Connection, bundle: ProjectBundle, prompts_by_scene: dict[int, list[str]], asset_kind: str = "image"
) -> None:
    for scene in bundle.scenes:
        prompts = prompts_by_scene.get(scene.number, [])
        for shot_number, prompt in enumerate(prompts, start=1):
            basename = f"{bundle.profile.project_id}-scene-{scene.number:02d}-shot-{shot_number:02d}-{asset_kind}"
            conn.execute(
                """
                INSERT INTO asset_target(project_id, scene_number, shot_number, asset_kind, prompt_text, prompt_sha256, output_basename)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, scene_number, shot_number, asset_kind) DO NOTHING
                """,
                (
                    bundle.profile.project_id,
                    scene.number,
                    shot_number,
                    asset_kind,
                    prompt,
                    prompt_hash(prompt),
                    basename,
                ),
            )
    conn.commit()


def next_asset(conn: sqlite3.Connection, project_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM asset_target
        WHERE project_id = ? AND status IN ('pending', 'retry')
        ORDER BY scene_number ASC, shot_number ASC, id ASC
        LIMIT 1
        """,
        (project_id,),
    ).fetchone()
    return dict(row) if row else None


def record_attempt(
    conn: sqlite3.Connection,
    target_id: int,
    provider: str,
    job_id: str | None,
    status: str,
    output_path: str | None = None,
    last_error: str | None = None,
) -> None:
    row = conn.execute("SELECT attempts, prompt_sha256 FROM asset_target WHERE id = ?", (target_id,)).fetchone()
    if row is None:
        raise KeyError(target_id)
    attempt = int(row["attempts"]) + 1
    conn.execute(
        """
        UPDATE asset_target
        SET provider = ?, job_id = ?, status = ?, output_path = COALESCE(?, output_path),
            last_error = ?, attempts = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (provider, job_id, status, output_path, last_error, attempt, target_id),
    )
    conn.execute(
        """
        INSERT INTO provider_job(asset_target_id, provider, job_id, prompt_sha256, attempt, status, output_path)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """,
        (target_id, provider, job_id, row["prompt_sha256"], attempt, status, output_path),
    )
    conn.commit()


def update_approval(conn: sqlite3.Connection, target_id: int, approval_state: str) -> None:
    conn.execute(
        "UPDATE asset_target SET approval_state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (approval_state, target_id),
    )
    conn.commit()


def retry_target(conn: sqlite3.Connection, target_id: int, reason: str) -> None:
    conn.execute(
        "UPDATE asset_target SET status = 'retry', last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (reason, target_id),
    )
    conn.commit()
