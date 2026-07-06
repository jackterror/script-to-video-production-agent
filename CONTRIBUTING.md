# Contributing

## Scope

Contributions should preserve the package contract:

- narration stays locked by default
- human approval stays required for visual changes, paid generation, asset acceptance, and delivery
- deterministic logic stays in Python
- context-sensitive judgment stays with the host agent

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m unittest discover -s tests -v
```

## Pull request standards

- keep the canonical scene schema backward-compatible unless there is a migration plan
- add or update tests for any parsing, rendering, queue, or audit change
- keep fixtures synthetic
- do not introduce client provenance, local machine paths, credentials, or generated outputs from private work
- run `python3 scripts/release_audit.py` before requesting review

## Release standards

- pass unit tests
- pass release audit
- regenerate any fixture outputs touched by the change
- update `CHANGELOG.md` for user-visible changes
