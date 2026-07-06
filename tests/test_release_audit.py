from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from script_to_video_production_agent.audit import release_audit


class ReleaseAuditTests(unittest.TestCase):
    def test_release_audit_passes_clean_temp_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("[Guide](docs/setup.md)\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/setup.md").write_text("safe\n", encoding="utf-8")
            findings = release_audit(root)
            self.assertEqual(findings["provenance"], [])
            self.assertEqual(findings["secrets"], [])
            self.assertEqual(findings["links"], [])
            self.assertEqual(findings["archives"], [])
            self.assertEqual(findings["docx_metadata"], [])

    def test_release_audit_flags_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked = "Final-" + "203"
            (root / "notes.txt").write_text(f"this contains {blocked} and should fail\n", encoding="utf-8")
            findings = release_audit(root)
            self.assertTrue(findings["provenance"])


if __name__ == "__main__":
    unittest.main()
