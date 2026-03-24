# Duckflow

`duckflow` is a lightweight annotation format and toolkit for tracing data flow through source code using local, comment-based facts.

The split is intentional:

- Source comments store only local facts about the code immediately below them.
- Generated graph artifacts stitch those local facts into end-to-end paths.

## Repository layout

- `duckflow/core.py`: extraction, filtering, stitching, and Mermaid rendering logic
- `duckflow/cli.py`: installable CLI entry points
- `duckflow/server.py`: MCP server exposing duckflow tools via FastMCP
- `scripts/extract_duckflow.py`: CLI for normalized JSON output
- `scripts/generate_duckflow_mermaid.py`: CLI for Mermaid flowchart output
- `tests/test_duckflow_tools.py`: parser and graph-behavior tests
- `tests/test_mcp_server.py`: MCP server tool tests
- `templates/agent-setup/`: agent instruction templates for Copilot, Codex, Claude Code, and Cline
- `install.sh`: interactive install script for all four AI tool clients
- `docs/skill-outline.md`: draft user-level skill outline
- `docs/prompt-structure.md`: draft `/duckflow` prompt structure

## Minimal schema

Each annotation is a JSON object stored in a source comment after `duckflow:`.

Required fields:

- `id`: stable unique identifier for the annotated code block.
- `kind`: one of `ui`, `api`, `state`, `orchestrator`, `artifact`, or another small local role label.

Optional fields:

- `status`: `live`, `planned`, or `shared`.
- `handles`: operations this block owns, such as `POST /api/generate-summary` or `ui:summary-review.build`.
- `calls`: operations this block invokes.
- `reads`: state, response, or artifact tokens consumed locally.
- `writes`: state or artifact tokens written locally.
- `returns`: response or function-output tokens exposed locally.
- `notes`: brief local clarification.

Example:

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

## Token conventions

Use exact string tokens so the graph builder can stitch by equality.

- HTTP handlers: `POST /api/generate-summary`
- UI steps: `ui:summary-review.build`
- Session state: `state:summary_focus_override`
- Customization payload: `customizations:summary_focus`
- API responses: `response:GET /api/status.professional_summaries`
- Preview artifacts: `artifact:generation_state.preview_html`
- Output files: `file:generated_files.final_html`

## Stitch rules

The extractor and Mermaid generator build edges from local facts only:

- Control edge: `calls` matches another annotation's `handles`
- Data edge: `writes` or `returns` matches another annotation's `reads`

## Maintenance rules

- Keep annotations adjacent to the code they describe.
- Record only facts visible in the local block.
- Prefer a small number of stable tokens over prose.
- When two implementations mirror the same local flow, annotate both and mark `status` accurately.
- Do not describe whole workflows in source comments; let generated artifacts do that.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mcp]"
```

## Commands

Extract normalized entries:

```bash
duckflow-extract --repo-root .
```

or:

```bash
python scripts/extract_duckflow.py --repo-root .
```

Render Mermaid:

```bash
duckflow-mermaid --repo-root .
```

or:

```bash
python scripts/generate_duckflow_mermaid.py --repo-root .
```

Render only matching flow entries:

```bash
python scripts/generate_duckflow_mermaid.py --repo-root . --match summary
```

Restrict scanning to explicit globs:

```bash
duckflow-extract --repo-root . --include "src/**/*.py" --include "web/**/*.ts"
```

## MCP server

`duckflow-mcp` exposes duckflow tools to AI agents over the Model Context
Protocol using [FastMCP](https://github.com/jlowin/fastmcp).

### Running the server directly

```bash
duckflow-mcp
```

or with `uvx` from this checkout:

```bash
uvx --from . duckflow-mcp
```

### Available tools

| Tool | Description |
|------|-------------|
| `duckflow_extract` | Extract annotations from a repository path |
| `duckflow_extract_text` | Extract annotations from source text already in the conversation |
| `duckflow_stitch` | Build a stitched call/data-flow graph for a repository |
| `duckflow_mermaid` | Render a Mermaid flowchart for a repository |
| `duckflow_mermaid_text` | Render a Mermaid flowchart from source text |

All tools accept an optional `match` argument to filter entries by substring.
`duckflow_extract` also accepts `stitched=true` to return a graph with nodes
and edges rather than a flat list.

### Agent setup

Run the interactive install script to wire `duckflow-mcp` into GitHub Copilot,
Codex, Claude Code, and/or Cline:

```bash
bash install.sh
```

The script prompts you to choose which clients to configure and whether to
install instructions at user level or inside a target project directory.  It
writes the MCP server entry into each client's config file and merges the
duckflow workflow instructions into the appropriate agent instruction file
(`copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, or `.clinerules`).

To install from the published GitHub URL instead of a local checkout, replace
the `--from` path in the generated config with:

```
git+https://github.com/warnes-innovations/duckflow
```
