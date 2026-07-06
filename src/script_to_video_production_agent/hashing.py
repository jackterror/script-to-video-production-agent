from __future__ import annotations

import hashlib


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_narration_lines(lines: list[str]) -> str:
    return "\n".join(line.rstrip() for line in lines).strip()


def narration_hash(lines: list[str]) -> str:
    return sha256_text(normalize_narration_lines(lines))


def prompt_hash(text: str) -> str:
    return sha256_text(text.strip())
