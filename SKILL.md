---
name: script-to-video-production-agent
description: Turns tutorial or explainer scripts into narration-locked Scene blocks, human-reviewed visual direction, vendor-ready video-builder prompts, still and video prompt packs, image-only exports, and a resumable local asset queue. Use for DOCX, Markdown, or plain-text script imports, review-sheet generation, prompt-pack creation, queue seeding, retry tracking, release packaging, or clean-room script-to-video workflows that require human approval before visual changes or paid generation.
---

# Script-to-Video Production Agent

Turn a source script into a controlled script-to-video workflow. Keep narration exact. Keep visual changes reviewable. Keep generation state resumable and local.

## Operating Rules

1. Preserve narration exactly by default. Treat narration edits as exceptional and deliberate.
2. Use the Python runtime for parsing, hashing, rendering, queue state, and audit checks.
3. Use the host agent for script judgment, visual judgment, prompt writing, and review reasoning.
4. Require human approval before visual changes, paid generation, asset acceptance, or final delivery.
5. Treat the SQLite queue as the source of truth for asset attempts and approval state.
6. Do not claim a live provider integration unless it has been explicitly tested in the current environment.
7. Run the release audit before calling a package public-ready.

## Workflow

### 1. Import and normalize

Run:

```bash
python3 scripts/stv_agent.py import-script \
  --input /path/to/source-script.docx \
  --config assets/config/examples/physical-process.json \
  --project-dir runtime/project-name
```

The runtime reads DOCX, Markdown, or plain text and normalizes the script into ordered `Scene` blocks with `Narration` and `Visuals`.

Read [references/scene-schema.md](references/scene-schema.md) before changing the schema contract.

### 2. Audit visual direction

Run:

```bash
python3 scripts/stv_agent.py review-export \
  --project-dir runtime/project-name \
  --project-id fixture-physical
```

Review the generated Step 2 document. The host agent should reason about visual issues, but the exported decisions must use the explicit A, R, or F format.

### 3. Apply review decisions

Run:

```bash
python3 scripts/stv_agent.py review-apply \
  --project-dir runtime/project-name \
  --project-id fixture-physical \
  --decisions runtime/project-name/outputs/review-decisions.txt
```

This writes before/after traceability and a cleaned v2 script.

### 4. Export prompt documents

Choose the required output:

```bash
python3 scripts/stv_agent.py export-builder-prompt --project-dir runtime/project-name --project-id fixture-physical
python3 scripts/stv_agent.py export-invideo-prompt --project-dir runtime/project-name --project-id fixture-physical
python3 scripts/stv_agent.py export-visual-pack --project-dir runtime/project-name --project-id fixture-physical
python3 scripts/stv_agent.py export-image-only --project-dir runtime/project-name --project-id fixture-physical
```

Use [references/prompt-profiles.md](references/prompt-profiles.md) before editing any exported prompt shape.

### 5. Seed and operate the asset queue

Run:

```bash
python3 scripts/stv_agent.py queue-seed \
  --project-dir runtime/project-name \
  --project-id fixture-physical \
  --asset-kind image
python3 scripts/stv_agent.py queue-next \
  --project-dir runtime/project-name \
  --project-id fixture-physical
```

Record attempts, approvals, rejections, and retries through the queue commands. Read [references/providers.md](references/providers.md) before representing a generation path.

### 6. Audit the release

Run:

```bash
python3 scripts/release_audit.py
python3 scripts/package_release.py
```

Read [references/clean-room-release.md](references/clean-room-release.md) before preparing a public archive.

## Resources

- `scripts/stv_agent.py`: CLI entrypoint.
- `assets/config/project-profile.schema.json`: profile contract.
- `assets/config/examples/`: example configurations.
- `assets/fixtures/`: synthetic source inputs and expected outputs.
- `references/scene-schema.md`: canonical schema and narration-lock rules.
- `references/prompt-profiles.md`: prompt-export contract.
- `references/providers.md`: provider and approval contract.
- `references/higgsfield-mcp.md`: optional Higgsfield integration guide.
- `references/clean-room-release.md`: public-release requirements.
