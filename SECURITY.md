# Security Policy

## Supported versions

Only the latest tagged release is supported for security issues.

## Reporting

Do not open a public issue for a suspected secret leak, provenance leak, or unsafe release artifact.

Report privately to the maintainer with:

- affected version
- reproduction steps
- impact
- whether the issue exposes private data, credentials, or release contamination

## Security boundaries

- provider credentials should stay outside portable profiles
- release archives should contain no private provenance
- no paid generation path should run without approval
- no asset should be accepted without approval
- runtime state should stay local unless the operator exports it intentionally
