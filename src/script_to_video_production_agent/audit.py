from __future__ import annotations

import hashlib
import re
import subprocess
import zipfile
from pathlib import Path


PROVENANCE_PATTERNS = [
    re.compile(r"/users/[^/\s]+/dev/codex/clients/active/", re.IGNORECASE),
    re.compile(r"\bfinal-\d{3}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-c\d{2}-s\d{2}\b", re.IGNORECASE),
]

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?i)secret\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_file(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".txt", ".py", ".yaml", ".yml", ".json", ".toml", ".css", ".js", ".html", ".svg"}


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        parts = []
        for name in archive.namelist():
            if name.startswith("word/") or name.startswith("docProps/"):
                try:
                    parts.append(archive.read(name).decode("utf-8", errors="ignore"))
                except Exception:
                    continue
        return "\n".join(parts)


def scan_provenance(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        lowered = str(path.relative_to(root)).lower()
        for pattern in PROVENANCE_PATTERNS:
            if pattern.search(lowered):
                findings.append(f"Filename provenance match: {path}")
        content = ""
        if text_file(path):
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
        elif path.suffix.lower() == ".docx":
            content = extract_docx_text(path).lower()
        elif path.suffix.lower() in {".zip", ".skill"}:
            try:
                with zipfile.ZipFile(path) as archive:
                    archive_text = "\n".join(archive.namelist()).lower()
                    content = archive_text
            except zipfile.BadZipFile:
                content = ""
        for pattern in PROVENANCE_PATTERNS:
            if pattern.search(content):
                findings.append(f"Content provenance match ({pattern.pattern}) in {path}")
    if (root / ".git").exists():
        proc = subprocess.run(
            ["git", "-C", str(root), "log", "--all", "--format=%H%n%B"],
            capture_output=True,
            text=True,
            check=False,
        )
        text = proc.stdout.lower()
        for pattern in PROVENANCE_PATTERNS:
            if pattern.search(text):
                findings.append(f"Git history provenance match: {pattern.pattern}")
    return findings


def scan_secrets(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if path.is_dir() or not text_file(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"Secret-like pattern {pattern.pattern} in {path}")
    return findings


def scan_links(root: Path) -> list[str]:
    findings: list[str] = []
    link_re = re.compile(r"\[.+?\]\((.+?)\)")
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in link_re.findall(text):
            if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
                continue
            if target.startswith("#"):
                continue
            link_path = (path.parent / target).resolve()
            if not link_path.exists():
                findings.append(f"Broken relative link in {path}: {target}")
    return findings


def archive_audit(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*.zip"):
        try:
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    lowered = name.lower()
                    for pattern in PROVENANCE_PATTERNS:
                        if pattern.search(lowered):
                            findings.append(f"Archive provenance match in {path}: {name}")
        except zipfile.BadZipFile:
            findings.append(f"Unreadable zip archive: {path}")
    return findings


def docx_metadata_audit(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*.docx"):
        text = extract_docx_text(path).lower()
        if "jackterror" in text or "/users/" in text:
            findings.append(f"DOCX metadata contains local identifiers: {path}")
    return findings


def release_audit(root: Path) -> dict[str, list[str]]:
    return {
        "provenance": scan_provenance(root),
        "secrets": scan_secrets(root),
        "links": scan_links(root),
        "archives": archive_audit(root),
        "docx_metadata": docx_metadata_audit(root),
    }
