# Agent Contract

## Agent-owned work

Use the host agent for:

- interpreting user intent
- deciding whether a visual needs review
- drafting or revising visual direction
- applying human review decisions
- writing provider-facing prompts
- reasoning about continuity, pacing, and clarity

## Runtime-owned work

Use the Python runtime for:

- parsing
- hashing
- schema normalization
- queue persistence
- filenames
- prompt export formatting
- retry state
- approval state
- release audits

## Input contract

The runtime should return structured, file-based artifacts.
The agent should consume those artifacts, not re-derive state from memory.

## Output contract

Agent-created decisions should come back in explicit file or text form, especially during Step 2 review.
