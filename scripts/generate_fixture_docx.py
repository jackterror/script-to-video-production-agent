#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from docx import Document


def write_docx(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    doc = Document()
    props = doc.core_properties
    props.author = "Script-to-Video Production Agent"
    props.company = "Open source"
    props.comments = ""
    props.category = "fixture"
    props.keywords = "fixture"
    for line in text.splitlines():
        doc.add_paragraph(line)
    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dst))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    fixtures = [
        root / "assets/fixtures/physical-process/source-script.md",
        root / "assets/fixtures/software-tutorial/source-script.md",
    ]
    for src in fixtures:
        write_docx(src, src.with_suffix(".docx"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
