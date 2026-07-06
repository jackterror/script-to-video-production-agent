# Scene Schema

## Canonical unit

Every stage shares the same scene model:

- `number`
- `narration`
- `visuals`
- `narration_sha256`
- `notes`

## Narration lock

Narration is the protected field.

Rules:

- preserve narration lines exactly by default
- hash normalized narration lines at the scene level
- derive a project-level narration hash from the ordered scene hashes
- treat narration edits as exceptional and intentional

## Import expectations

Preferred script structure:

```text
Scene 1
Narration:
"Exact spoken line."
Visual:
What the viewer sees.
```

The importer also tolerates older `Narrator` and `Visuals` labels and falls back to paragraph-based scene creation when explicit scene labels are missing.

## Review expectations

Review changes should target visuals, not narration, unless the operator intentionally approves a narration change outside the default workflow.
