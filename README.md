# Script to Video Production Agent

A modular AI-ready script-to-video production agent that turns tutorial scripts into narration-locked scenes, reviewable visual direction, prompt packs, and local asset queues.

## What it does

- imports tutorial and explainer scripts from DOCX, Markdown, and plain text
- normalizes scripts into ordered Scene blocks with locked narration
- exports review sheets for visual cleanup before production
- applies accepted visual decisions with before and after traceability
- renders vendor-neutral builder prompts and an InVideo-oriented prompt profile
- generates still-image, video-shot, and image-only prompt packs
- tracks asset targets, retries, approvals, rejections, and provider attempts in local SQLite
- packages the repo and audits it for public clean-room release

## Default behavior

Unprompted, the package preserves narration exactly, treats visual changes as a review step, keeps provider actions explicit, requires approval before paid generation or asset acceptance, and stores operational state locally.

## Architecture / Package structure

```text
script-to-video-production-agent/
├── SKILL.md
├── README.md
├── TEST-PROMPTS.md
├── references/
│   ├── scene-schema.md
│   ├── prompt-profiles.md
│   ├── providers.md
│   └── clean-room-release.md
├── assets/
│   ├── config/
│   └── fixtures/
├── scripts/
│   ├── stv_agent.py
│   ├── release_audit.py
│   └── package_release.py
├── src/
│   └── script_to_video_production_agent/
├── evals/
└── tests/
```

## Agent Skill installation

The repository root follows the [Agent Skills specification](https://agentskills.io/specification).

Claude Code:

```bash
ln -s /absolute/path/script-to-video-production-agent ~/.claude/skills/script-to-video-production-agent
```

OpenAI Codex:

```bash
ln -s /absolute/path/script-to-video-production-agent ~/.codex/skills/script-to-video-production-agent
```

Then ask:

```text
Use $script-to-video-production-agent to turn my tutorial or explainer script into narration-locked scenes, a visual review pass, prompt documents, and a resumable local asset queue.
```

## Notes

The host agent handles judgment, review reasoning, and prompt writing.

The Python runtime handles parsing, hashing, rendering, queue state, provider attempt logging, and release checks.

Manual export always works. Provider integrations are optional and must stay approval-aware.

## Testing

```bash
python3 -m unittest discover -s tests -v
python3 scripts/release_audit.py
python3 scripts/package_release.py
```

## Limitations

- the package does not run paid generation by itself
- InVideo support is an output profile, not an API integration
- Higgsfield support remains a capability adapter plus setup guide until a tested runtime path exists
- human approval remains required before visual changes, paid generation, asset acceptance, or final delivery

## Creator and license

Created by [Jack Dalrymple](https://www.jackdalrymple.com/), Founder of [Cap & Cut](https://capandcut.com/). See [CREATOR.md](CREATOR.md).

Released under the MIT License. See [LICENSE](LICENSE).
