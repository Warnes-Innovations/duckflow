# /duckflow Prompt Structure

## Goal

Provide a repeatable slash-command workflow for adding, updating, reviewing, and regenerating duckflow annotations.

## Recommended Prompt Metadata

```yaml
---
name: duckflow
description: Add, review, or regenerate duckflow annotations and graph artifacts
argument-hint: describe the file, flow, or task such as annotate web/foo.js or review changed duckflow files
---
```

## Suggested flow

### Step 1: Classify the request

Determine whether the user wants to:

- add annotations
- update stale annotations
- review existing annotations
- regenerate graph artifacts
- inspect a specific flow

If ambiguous, ask for the target file or flow.

### Step 2: Inspect repo-local duckflow conventions

Read repo-local docs or instructions if present:

- `DUCKFLOW.md`
- `.github/copilot-instructions.md`
- repo-local duckflow skills
- existing generated artifact locations

### Step 3: Inspect the target code

- read the relevant files
- identify the local facts the block actually owns
- avoid inferring behavior implemented elsewhere

### Step 4: Apply the requested operation

#### Annotate

- add duckflow comments adjacent to the code
- include a UTC `timestamp` in `YYYY-MM-DDTHH:MM:SSZ` format
- use stable tokens and accurate status values

#### Update

- revise timestamp, tokens, status, notes, or adjacency as needed
- keep mirrored implementations aligned where relevant

#### Review

- compare annotations against current code behavior
- flag stale or misleading annotations first

#### Regenerate

- run extractor and Mermaid generation commands if configured
- summarize any graph changes

### Step 5: Validate

- ensure annotations are syntactically valid JSON objects inside comments
- ensure every annotation includes a current UTC `timestamp`
- run targeted tests if the repo has them
- confirm generated artifacts are in sync when committed

### Step 6: Report

Summarize:

- files changed
- flows touched
- regeneration commands run
- follow-up gaps or repo-local decisions still needed

## Good arguments

- `/duckflow annotate web/summary-review.js`
- `/duckflow review changed files`
- `/duckflow regenerate summary flow`
- `/duckflow trace selected summary from UI to final HTML`
