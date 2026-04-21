# Duckflow

`duckflow` is a lightweight annotation format and toolkit for tracing data flow through source code using local, comment-based facts.

The split is intentional:

- Source comments store only local facts about the code immediately below them.
- Generated graph artifacts stitch those local facts into end-to-end paths.

## Repository layout

- `duckflow/core.py`: extraction, filtering, stitching, and Mermaid rendering logic
- `duckflow/cli.py`: installable CLI entry points
- `scripts/extract_duckflow.py`: CLI for normalized JSON output
- `scripts/generate_duckflow_mermaid.py`: CLI for Mermaid flowchart output
- `tests/test_duckflow_tools.py`: parser and graph-behavior tests
- `docs/skill-outline.md`: draft user-level skill outline
- `docs/prompt-structure.md`: draft `/duckflow` prompt structure

## Minimal schema

Each annotation is a YAML mapping stored in a source comment after `duckflow:`.
Use one fixed vocabulary only.

Required fields:

- `id`: stable unique identifier for the annotated code block.
- `kind`: one of `ui`, `api`, `state`, `orchestrator`, `artifact`, or another small local role label.
- `timestamp`: UTC annotation update time in `YYYY-MM-DDTHH:MM:SSZ` format. Bump it whenever the annotated code block changes in a way that affects duckflow facts.

Optional fields:

- `status`: `live`, `planned`, or `shared`.
- `handles`: operations this block owns, such as `POST /api/generate-summary` or `ui:summary-review.build`.
- `calls`: operations this block invokes.
- `reads`: state, response, or artifact tokens consumed locally.
- `writes`: state or artifact tokens written locally.
- `returns`: response or function-output tokens exposed locally.
- `notes`: brief local clarification.

```text
# duckflow:
#   id: summary.api.generate
#   kind: api
#   timestamp: "2026-03-25T00:00:00Z"
#   status: live
#   handles: ["POST /api/generate-summary"]
#   writes: ["state:session_summaries.ai_generated"]
#   returns: ["response:POST /api/generate-summary.summary"]
```

Allowed keys:

- `id`
- `kind`
- `timestamp`
- `status`
- `handles`
- `calls`
- `reads`
- `writes`
- `returns`
- `notes`

Legacy JSON and shorthand annotations are not supported.

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
- Every annotation must include a UTC `timestamp`, and that timestamp must be refreshed whenever the annotated code changes.
- When two implementations mirror the same local flow, annotate both and mark `status` accurately.
- Do not describe whole workflows in source comments; let generated artifacts do that.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
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
python scripts/extract_duckflow.py --repo-root . --include "src/**/*.py" --include "web/**/*.ts"
```
