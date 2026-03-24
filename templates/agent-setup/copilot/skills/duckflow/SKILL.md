---
name: duckflow
description: >
  Extract, stitch, and render duckflow annotations.
  Use when tracing local data flow, adding or updating comment annotations,
  reviewing whether annotations match current code, or regenerating Mermaid
  flowchart artifacts.
---

Annotate and analyse data-flow through source code using the `duckflow-mcp` MCP server.

## When to Use

- The user wants to add `duckflow:` comment annotations to source files.
- The user wants to extract all annotations from a repository.
- The user wants to visualise component data flow as a Mermaid flowchart.
- The user wants to review whether annotations still match current code.
- The user wants to regenerate stitched graph artifacts after annotation changes.

## MCP Tool Operations

Prefer the `duckflow-mcp` MCP tools when the server is available.
Do not read or write duckflow annotations manually when an MCP tool can perform the operation.
If `duckflow-mcp` is unavailable, fall back to running the CLI tools.

| Operation | How |
|-----------|-----|
| Extract entries from repo | `duckflow_extract(repo_root, include?, match?, stitched?)` |
| Extract entries from text | `duckflow_extract_text(text, path?, match?)` |
| Build stitched graph | `duckflow_stitch(repo_root, include?, match?)` |
| Render Mermaid (repo) | `duckflow_mermaid(repo_root, include?, match?)` |
| Render Mermaid (text) | `duckflow_mermaid_text(text, path?, match?)` |

## CLI Fallback

```bash
duckflow-extract --repo-root .
duckflow-extract --repo-root . --stitched
duckflow-mermaid --repo-root .
duckflow-mermaid --repo-root . --match summary
```

## Annotation Schema

```json
{
  "id": "summary.api.generate",
  "kind": "api",
  "status": "live",
  "handles": ["POST /api/generate-summary"],
  "writes": ["state:session_summaries.ai_generated"],
  "returns": ["response:POST /api/generate-summary.summary"]
}
```

Required fields: `id`, `kind`.
Optional fields: `status` (`live`, `planned`, `shared`), `handles`, `calls`, `reads`, `writes`, `returns`, `notes`.

## Workflow Summary

1. Identify the annotation task: add, update, review, or regenerate.
2. Read repo-local conventions if a `DUCKFLOW.md` or `.github/copilot-instructions.md` exists.
3. Inspect the target source block; record only locally visible facts.
4. Apply the annotation using stable, exact tokens.
5. Verify the annotation is valid JSON inside a comment.
6. Re-extract or re-render to confirm the graph is consistent.

For the full conversational workflow, use the packaged `/duckflow` prompt at `.github/prompts/duckflow.prompt.md`.
