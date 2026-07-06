#!/usr/bin/env python3

from pathlib import Path

from script_to_video_production_agent.audit import release_audit


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = release_audit(root)
    for name, items in findings.items():
        print(f"[{name}]")
        if not items:
            print("ok")
            continue
        for item in items:
            print(item)
    return 1 if any(findings.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
