# Clean-Room Release

## Public package rule

The release archive must contain no private provenance.

## Prohibited content

- client names
- private originals
- private generated images or prompts
- local absolute machine paths
- inherited Word metadata from private documents
- inherited Git history
- secrets or credentials

## Required checks

- provenance scan
- secret scan
- relative-link scan
- archive scan
- DOCX metadata scan

## Release commands

```bash
python3 -m unittest discover -s tests -v
python3 scripts/release_audit.py
python3 scripts/package_release.py
```
