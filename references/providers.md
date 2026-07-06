# Providers

## Provider model

The runtime uses a capability adapter instead of a hard-coded service workflow.

Current capabilities:

- `manual`
- `higgsfield` detection adapter

## Manual

Manual export must always work without any external service.

Use the queue to:

- fetch the next target
- generate externally
- record provider, job ID, status, and output path
- approve or reject the result

## Higgsfield

Higgsfield support is intentionally conservative.

Rules:

- detect only explicit runtime configuration
- do not invent MCP tool names
- do not claim a tested live path until it has been exercised in the target environment
- make spending and approval explicit before any paid call
