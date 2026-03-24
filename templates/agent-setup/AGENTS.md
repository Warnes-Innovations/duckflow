# Duckflow Guidelines

Use the duckflow MCP tools for all annotation extraction, stitching, and Mermaid rendering work in this repository.

## When To Use Duckflow

- Use duckflow when you need to add or update `duckflow:` comment annotations in source files.
- Use duckflow when you want to extract all annotations from a repository and inspect them as structured data.
- Use duckflow when you need to visualize data flow between components as a Mermaid flowchart.
- Use duckflow when reviewing whether annotations still match current code behavior.
- Use duckflow when regenerating stitched graph artifacts after annotation changes.
- Prefer normal file reads for small single-file questions that do not require graph analysis.

## Required Workflow

- Use `duckflow_extract` to obtain normalized annotation entries from a repository.
- Use `duckflow_extract_text` when source text is already available in the conversation.
- Use `duckflow_stitch` to build the full call and data-flow graph.
- Use `duckflow_mermaid` to render a Mermaid flowchart for a repository.
- Use `duckflow_mermaid_text` to render Mermaid markup directly from source text.
- Pass the `match` argument to narrow results to a specific flow or component.
- Pass `stitched=true` to `duckflow_extract` when you need edges alongside nodes.

## Annotation Conventions

- Annotations are JSON objects in source comments after the `duckflow:` marker.
- Required fields: `id` (stable unique string), `kind` (role label such as `ui`, `api`, `state`).
- Optional fields: `status` (`live`, `planned`, `shared`), `handles`, `calls`, `reads`, `writes`, `returns`, `notes`.
- Keep annotations adjacent to the code block they describe.
- Record only facts visible in the local block; do not narrate whole workflows.
- Use exact string tokens for all token fields so the graph builder can stitch by equality.
- Set `status` accurately when code paths exist in parallel live and planned implementations.

## Graph Stitching Rules

- Control edge: a `calls` token in one entry matches a `handles` token in another.
- Data edge: a `writes` or `returns` token in one entry matches a `reads` token in another.
- Edges are only created between entries with compatible statuses (same status, or either side is `shared`).

## Maintenance Rules

- After modifying annotations, re-run extraction and Mermaid generation to verify the graph is consistent.
- Prefer a small number of stable tokens over prose descriptions.
- When two implementations mirror the same local flow, annotate both and set `status` accurately.
