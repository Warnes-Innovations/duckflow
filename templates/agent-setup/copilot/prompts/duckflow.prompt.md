---
description: "Add, review, or regenerate duckflow annotations and Mermaid graph artifacts"
name: "Duckflow Annotation"
argument-hint: "Describe the file, flow, or task such as: annotate web/foo.js, review changed duckflow files, or regenerate summary flow"
agent: "agent"
tools: [duckflow-mcp/*]
---

Use the `duckflow-mcp` MCP server to work with duckflow annotations in the current workspace.

Follow this workflow:

1. Determine whether the request is to **add**, **update**, **review**, or **regenerate** duckflow annotations.
2. If ambiguous, ask for the target file, flow name, or task description.
3. Read repo-local duckflow conventions from `DUCKFLOW.md`, `.github/copilot-instructions.md`, or existing annotations if present.

### Add annotations

4. Read the target source file(s) and identify the code blocks to annotate.
5. For each block, record only locally visible facts: what it handles, calls, reads, writes, or returns.
6. Choose a stable `id` and a concise `kind` label.
7. Write the annotation as a JSON object in a comment immediately above the code block.
8. Call `duckflow_extract_text` on the updated file content to verify the annotation parses correctly.

### Update annotations

4. Call `duckflow_extract` to surface all current annotations and their tokens.
5. Identify stale or incorrect fields by comparing annotations against current code.
6. Revise tokens, status values, adjacency, or notes as needed.
7. Re-verify with `duckflow_extract_text` after each change.

### Review annotations

4. Call `duckflow_extract` to obtain all current entries.
5. Compare each annotation against the corresponding code block.
6. Flag stale, misleading, or missing annotations.
7. Propose edits; apply only after explicit user approval.

### Regenerate graph artifacts

4. Call `duckflow_mermaid` to render the full Mermaid flowchart.
5. Use `match` to narrow the diagram to a specific flow if requested.
6. Show the Mermaid output and summarise any graph changes.

### Final step (all tasks)

9. Report: files changed, flows touched, regeneration commands run, and any follow-up gaps.

Rules:

- Record only facts visible in the local code block; do not narrate whole workflows.
- Use exact string tokens for all `handles`, `calls`, `reads`, `writes`, and `returns` fields.
- Set `status` (`live`, `planned`, `shared`) accurately when parallel implementations exist.
- Prefer stable tokens over prose; avoid vague tokens like `data:input` or `step:done`.
- If the MCP server is unavailable, fall back to the CLI commands and tell the user.

Input: ${input}
