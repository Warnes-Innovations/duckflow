#!/usr/bin/env python3
# Copyright (C) 2026 Gregory R. Warnes
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for duckflow extraction and Mermaid rendering."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Callable


ExtractFromTextFn = Callable[..., list[Any]]
IterSourceFilesFn = Callable[..., list[Path]]
RenderMermaidFn = Callable[[dict[str, Any]], str]
StitchDuckflowFn = Callable[..., dict[str, Any]]


def _load_duckflow_api(
) -> tuple[
    ExtractFromTextFn,
    IterSourceFilesFn,
    RenderMermaidFn,
    StitchDuckflowFn,
]:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    duckflow_module = importlib.import_module("duckflow")

    return (
        getattr(duckflow_module, "extract_duckflow_entries_from_text"),
        getattr(duckflow_module, "iter_source_files"),
        getattr(duckflow_module, "render_mermaid"),
        getattr(duckflow_module, "stitch_duckflow"),
    )


def test_extract_duckflow_entries_from_python_comments() -> None:
    extract_duckflow_entries_from_text, _, _, _ = _load_duckflow_api()
    text = """
# duckflow: {
#   "id": "summary.api",
#   "kind": "api",
#   "timestamp": "2026-03-25T00:00:00Z",
#   "handles": ["POST /api/generate-summary"],
#   "writes": ["state:session_summaries.ai_generated"],
#   "returns": ["response:POST /api/generate-summary.summary"]
# }
def handler():
    return None
"""

    entries = extract_duckflow_entries_from_text(text, Path("sample.py"))

    assert len(entries) == 1
    assert entries[0].id == "summary.api"
    assert entries[0].timestamp == "2026-03-25T00:00:00Z"
    assert entries[0].handles == ("POST /api/generate-summary",)
    assert entries[0].writes == ("state:session_summaries.ai_generated",)


def test_stitch_duckflow_builds_call_and_data_edges() -> None:
    (
        extract_duckflow_entries_from_text,
        _,
        _,
        stitch_duckflow,
    ) = _load_duckflow_api()
    producer_text = """
# duckflow: {
#   "id": "summary.api",
#   "kind": "api",
#   "timestamp": "2026-03-25T00:00:00Z",
#   "handles": ["POST /api/generate-summary"],
#   "writes": ["state:session_summaries.ai_generated"],
#   "returns": ["response:POST /api/generate-summary.summary"]
# }
"""
    consumer_text = """
// duckflow: {
//   "id": "summary.ui",
//   "kind": "ui",
//   "timestamp": "2026-03-25T00:00:00Z",
//   "calls": ["POST /api/generate-summary"],
//   "reads": ["response:POST /api/generate-summary.summary"]
// }
"""

    entries = extract_duckflow_entries_from_text(
        producer_text,
        Path("producer.py"),
    )
    entries += extract_duckflow_entries_from_text(
        consumer_text,
        Path("consumer.js"),
    )
    graph = stitch_duckflow(entries)

    assert {edge["kind"] for edge in graph["edges"]} == {"call", "data"}
    assert any(
        edge["token"] == "POST /api/generate-summary"
        for edge in graph["edges"]
    )
    assert any(
        edge["token"] == "response:POST /api/generate-summary.summary"
        for edge in graph["edges"]
    )


def test_render_mermaid_marks_node_status() -> None:
    (
        extract_duckflow_entries_from_text,
        _,
        render_mermaid,
        stitch_duckflow,
    ) = _load_duckflow_api()
    text = """
# duckflow: {
#   "id": "summary.route",
#   "kind": "api",
#   "timestamp": "2026-03-25T00:00:00Z",
#   "status": "planned"
# }
"""

    entries = extract_duckflow_entries_from_text(text, Path("route.py"))
    mermaid = render_mermaid(stitch_duckflow(entries))

    assert "class summary.route planned;" in mermaid
    assert "flowchart TD" in mermaid


def test_extract_duckflow_ignores_non_comment_string_literals() -> None:
    extract_duckflow_entries_from_text, _, _, _ = _load_duckflow_api()
    text = '''
payload = "duckflow: {\"id\": \"not_real\"}"
# duckflow: {
#   "id": "real.entry",
#   "timestamp": "2026-03-25T00:00:00Z",
#   "kind": "api"
# }
'''

    entries = extract_duckflow_entries_from_text(text, Path("literal.py"))

    assert [entry.id for entry in entries] == ["real.entry"]


def test_stitch_duckflow_skips_direct_live_to_planned_edges() -> None:
    (
        extract_duckflow_entries_from_text,
        _,
        _,
        stitch_duckflow,
    ) = _load_duckflow_api()
    live_text = """
# duckflow: {
#   "id": "live.route",
#   "kind": "api",
#   "timestamp": "2026-03-25T00:00:00Z",
#   "status": "live",
#   "writes": ["state:summary_focus_override"]
# }
"""
    planned_text = """
# duckflow: {
#   "id": "planned.route",
#   "kind": "api",
#   "timestamp": "2026-03-25T00:00:00Z",
#   "status": "planned",
#   "reads": ["state:summary_focus_override"]
# }
"""

    entries = extract_duckflow_entries_from_text(live_text, Path("live.py"))
    entries += extract_duckflow_entries_from_text(
        planned_text,
        Path("planned.py"),
    )

    graph = stitch_duckflow(entries)

    assert graph["edges"] == []


def test_extract_duckflow_requires_timestamp() -> None:
    extract_duckflow_entries_from_text, _, _, _ = _load_duckflow_api()
    text = """
# duckflow: {
#   "id": "summary.route",
#   "kind": "api"
# }
"""

    try:
        extract_duckflow_entries_from_text(text, Path("missing.py"))
    except ValueError as exc:
        assert "timestamp" in str(exc)
    else:
        raise AssertionError("missing timestamp should fail validation")


def test_extract_duckflow_rejects_non_utc_timestamp_format() -> None:
    extract_duckflow_entries_from_text, _, _, _ = _load_duckflow_api()
    text = """
# duckflow: {
#   "id": "summary.route",
#   "kind": "api",
#   "timestamp": "2026-03-25"
# }
"""

    try:
        extract_duckflow_entries_from_text(text, Path("bad-timestamp.py"))
    except ValueError as exc:
        assert "YYYY-MM-DDTHH:MM:SSZ" in str(exc)
    else:
        raise AssertionError("invalid timestamp format should fail validation")


def test_iter_source_files_skips_generated_dirs(
    tmp_path: Path,
) -> None:
    _, iter_source_files, _, _ = _load_duckflow_api()
    source_file = tmp_path / "src" / "handler.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("# duckflow: {}\n", encoding="utf-8")

    ignored_file = tmp_path / "node_modules" / "pkg" / "index.js"
    ignored_file.parent.mkdir(parents=True)
    ignored_file.write_text("// duckflow: {}\n", encoding="utf-8")

    files = iter_source_files(tmp_path)

    assert files == [source_file]
