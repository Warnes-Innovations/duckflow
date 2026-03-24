# Duckflow Skill Outline

## Purpose

Provide reusable, cross-project guidance for authoring, reviewing, and regenerating duckflow annotations.

## Recommended Skill Metadata

```yaml
---
name: duckflow
description: >
  Add, review, and maintain duckflow annotations and stitched graph outputs.
  Use when tracing local data flow, updating comment annotations, or regenerating duckflow artifacts.
---
```

## Sections

### Use when

- tracing a feature across UI, API, state, and artifact boundaries
- adding or updating duckflow comments in source files
- reviewing whether annotations still match current code behavior
- regenerating stitched JSON or Mermaid outputs after annotation changes

### Core rules

1. Keep source comments local to the code block they describe.
2. Record only facts visible in that local block.
3. Prefer exact stable tokens over prose in `handles`, `calls`, `reads`, `writes`, and `returns`.
4. Use `status` to distinguish live, planned, and shared flows.
5. Let generated graphs describe the end-to-end workflow; do not narrate whole workflows in source comments.

### Annotation checklist

- choose a stable `id`
- choose a concise `kind`
- capture local reads and writes only
- prefer token equality over natural-language matching
- verify mirrored implementations use compatible tokens

### Review checklist

- annotation is adjacent to the code it describes
- tokens are stable and exact
- status is accurate
- generated artifacts were refreshed if the repo commits them
- no annotation claims behavior not implemented in code

### Regeneration workflow

- identify the repo root
- run the extractor
- run Mermaid generation
- inspect diffs in generated artifacts
- fix token mismatches if the graph breaks unexpectedly

### Anti-patterns

- whole-workflow prose in source comments
- vague tokens like `data:input` or `step:done`
- copying annotations across files without matching actual behavior
- mixing planned and live facts without explicit `status`

### Repo-local override points

- default source globs
- token naming conventions
- committed artifact locations
- required regeneration commands
