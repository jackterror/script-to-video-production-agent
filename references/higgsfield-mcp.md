# Higgsfield MCP Guide

This package includes a capability adapter and operator guidance for Higgsfield MCP.

## Current stance

- supported as an optional future adapter
- not treated as active unless runtime configuration is present
- not represented as tested unless the operator validates the integration

## Suggested integration path

1. Confirm available Higgsfield MCP tools at runtime.
2. Map only verified tool names into a provider adapter.
3. Keep approval gates before any paid generation.
4. Record prompt hash, job ID, attempts, and output path through the local queue.
5. Fall back to `manual` if runtime detection or invocation is incomplete.
