# Prompt Profiles

## Vendor-neutral builder prompt

Use when the downstream editor or model should follow the narration exactly while treating visuals as guidance.

## InVideo-oriented prompt

Use when the destination operator wants a scene-by-scene script block that separates:

- `Scene X`
- `Narration:`
- `Visual:`

Rules:

- keep narration exact
- keep visual guidance in paragraph form
- do not insert gap markers, bracket wrappers, or ornamental formatting into the narration

## Visual prompt pack

Step 5 exports:

- scene goal
- shot montage
- multi-image prompt text
- single-shot video prompts

## Image-only export

Step 6 strips the package down to copy-paste-ready multi-image prompt blocks for manual batch generation.
