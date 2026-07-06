#!/usr/bin/env python3

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from script_to_video_production_agent.audit import sha256_file


EXCLUDES = {".git", "__pycache__", ".pytest_cache", "runtime", "dist", ".venv"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dist = root / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    archive = dist / "script-to-video-production-agent-v0.1.0.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in root.rglob("*"):
            rel = path.relative_to(root)
            if any(part in EXCLUDES for part in rel.parts):
                continue
            if path.is_dir():
                continue
            zf.write(path, rel)
    manifest = {
        "archive": str(archive),
        "sha256": sha256_file(archive),
    }
    (dist / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
