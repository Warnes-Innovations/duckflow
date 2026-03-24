#!/usr/bin/env python3
# Copyright (C) 2026 Gregory R. Warnes
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the duckflow MCP server tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from duckflow.server import (
    duckflow_extract,
    duckflow_extract_text,
    duckflow_mermaid,
    duckflow_mermaid_text,
    duckflow_stitch,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PRODUCER_TEXT = """\
# duckflow: {
#   "id": "summary.api",
#   "kind": "api",
#   "status": "live",
#   "handles": ["POST /api/generate-summary"],
#   "writes": ["state:session_summaries.ai_generated"],
#   "returns": ["response:POST /api/generate-summary.summary"]
# }
def handler():
    return None
"""

CONSUMER_TEXT = """\
// duckflow: {
//   "id": "summary.ui",
//   "kind": "ui",
//   "status": "live",
//   "calls": ["POST /api/generate-summary"],
//   "reads": ["response:POST /api/generate-summary.summary"]
// }
"""

PLANNED_TEXT = """\
# duckflow: {
#   "id": "planned.route",
#   "kind": "api",
#   "status": "planned",
#   "reads": ["state:summary_focus_override"]
# }
"""

LIVE_WRITER_TEXT = """\
# duckflow: {
#   "id": "live.route",
#   "kind": "api",
#   "status": "live",
#   "writes": ["state:summary_focus_override"]
# }
"""


@pytest.fixture()
def repo_with_annotations(tmp_path: Path) -> Path:
    """Create a minimal repo with two annotated source files."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "api.py").write_text(PRODUCER_TEXT, encoding="utf-8")
    (src / "ui.js").write_text(CONSUMER_TEXT, encoding="utf-8")
    return tmp_path


@pytest.fixture()
def empty_repo(tmp_path: Path) -> Path:
    """Create a repo with no duckflow annotations."""
    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# duckflow_extract_text
# ---------------------------------------------------------------------------


class TestDuckflowExtractText:
    def test_returns_json_list(self) -> None:
        result = duckflow_extract_text(PRODUCER_TEXT)
        entries = json.loads(result)
        assert isinstance(entries, list)
        assert len(entries) == 1

    def test_entry_fields(self) -> None:
        result = duckflow_extract_text(PRODUCER_TEXT)
        entry = json.loads(result)[0]
        assert entry["id"] == "summary.api"
        assert entry["kind"] == "api"
        assert entry["status"] == "live"
        assert "POST /api/generate-summary" in entry["handles"]

    def test_match_filter_keeps_matching_entry(self) -> None:
        combined = PRODUCER_TEXT + "\n" + CONSUMER_TEXT
        result = duckflow_extract_text(combined, path="combined.py", match="api")
        entries = json.loads(result)
        ids = [e["id"] for e in entries]
        assert "summary.api" in ids

    def test_match_filter_excludes_non_matching(self) -> None:
        combined = PRODUCER_TEXT + "\n" + CONSUMER_TEXT
        result = duckflow_extract_text(combined, path="combined.py", match="summary.api")
        entries = json.loads(result)
        ids = [e["id"] for e in entries]
        assert "summary.ui" not in ids

    def test_no_annotations_returns_empty_list(self) -> None:
        result = duckflow_extract_text("x = 1\n")
        assert json.loads(result) == []

    def test_invalid_json_returns_error(self) -> None:
        bad = "# duckflow: {broken json\n"
        result = duckflow_extract_text(bad)
        assert result.startswith("ERROR:")

    def test_path_stored_in_entry(self) -> None:
        result = duckflow_extract_text(PRODUCER_TEXT, path="mymodule.py")
        entry = json.loads(result)[0]
        assert entry["path"] == "mymodule.py"

    def test_default_path_is_inline(self) -> None:
        result = duckflow_extract_text(PRODUCER_TEXT)
        entry = json.loads(result)[0]
        assert entry["path"] == "<inline>"


# ---------------------------------------------------------------------------
# duckflow_extract
# ---------------------------------------------------------------------------


class TestDuckflowExtract:
    def test_extracts_entries_from_repo(
        self, repo_with_annotations: Path
    ) -> None:
        result = duckflow_extract(str(repo_with_annotations))
        entries = json.loads(result)
        assert isinstance(entries, list)
        assert len(entries) == 2
        ids = {e["id"] for e in entries}
        assert ids == {"summary.api", "summary.ui"}

    def test_include_glob_restricts_scan(
        self, repo_with_annotations: Path
    ) -> None:
        result = duckflow_extract(
            str(repo_with_annotations), include=["**/*.py"]
        )
        entries = json.loads(result)
        assert len(entries) == 1
        assert entries[0]["id"] == "summary.api"

    def test_match_filter(self, repo_with_annotations: Path) -> None:
        result = duckflow_extract(str(repo_with_annotations), match="summary.api")
        entries = json.loads(result)
        ids = [e["id"] for e in entries]
        assert "summary.api" in ids
        assert "summary.ui" not in ids

    def test_stitched_flag_returns_graph(
        self, repo_with_annotations: Path
    ) -> None:
        result = duckflow_extract(str(repo_with_annotations), stitched=True)
        graph = json.loads(result)
        assert "nodes" in graph
        assert "edges" in graph

    def test_stitched_graph_has_expected_edges(
        self, repo_with_annotations: Path
    ) -> None:
        result = duckflow_extract(str(repo_with_annotations), stitched=True)
        graph = json.loads(result)
        edge_kinds = {e["kind"] for e in graph["edges"]}
        assert "call" in edge_kinds
        assert "data" in edge_kinds

    def test_empty_repo_returns_empty_list(self, empty_repo: Path) -> None:
        result = duckflow_extract(str(empty_repo))
        assert json.loads(result) == []

    def test_nonexistent_repo_returns_error(self) -> None:
        result = duckflow_extract("/nonexistent/path/does/not/exist")
        assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# duckflow_stitch
# ---------------------------------------------------------------------------


class TestDuckflowStitch:
    def test_returns_graph_with_nodes_and_edges(
        self, repo_with_annotations: Path
    ) -> None:
        result = duckflow_stitch(str(repo_with_annotations))
        graph = json.loads(result)
        assert "nodes" in graph
        assert "edges" in graph

    def test_call_edge_present(self, repo_with_annotations: Path) -> None:
        result = duckflow_stitch(str(repo_with_annotations))
        graph = json.loads(result)
        call_edges = [e for e in graph["edges"] if e["kind"] == "call"]
        assert any(
            e["token"] == "POST /api/generate-summary" for e in call_edges
        )

    def test_data_edge_present(self, repo_with_annotations: Path) -> None:
        result = duckflow_stitch(str(repo_with_annotations))
        graph = json.loads(result)
        data_edges = [e for e in graph["edges"] if e["kind"] == "data"]
        assert any(
            e["token"] == "response:POST /api/generate-summary.summary"
            for e in data_edges
        )

    def test_match_narrows_nodes(self, repo_with_annotations: Path) -> None:
        result = duckflow_stitch(str(repo_with_annotations), match="summary.api")
        graph = json.loads(result)
        node_ids = [n["id"] for n in graph["nodes"]]
        assert "summary.api" in node_ids
        assert "summary.ui" not in node_ids

    def test_incompatible_statuses_produce_no_edges(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "live.py").write_text(LIVE_WRITER_TEXT, encoding="utf-8")
        (tmp_path / "planned.py").write_text(PLANNED_TEXT, encoding="utf-8")
        result = duckflow_stitch(str(tmp_path))
        graph = json.loads(result)
        assert graph["edges"] == []

    def test_empty_repo_returns_empty_graph(self, empty_repo: Path) -> None:
        result = duckflow_stitch(str(empty_repo))
        graph = json.loads(result)
        assert graph["nodes"] == []
        assert graph["edges"] == []


# ---------------------------------------------------------------------------
# duckflow_mermaid
# ---------------------------------------------------------------------------


class TestDuckflowMermaid:
    def test_returns_flowchart_header(
        self, repo_with_annotations: Path
    ) -> None:
        result = duckflow_mermaid(str(repo_with_annotations))
        assert result.startswith("flowchart TD")

    def test_contains_node_ids(self, repo_with_annotations: Path) -> None:
        result = duckflow_mermaid(str(repo_with_annotations))
        assert "summary.api" in result
        assert "summary.ui" in result

    def test_contains_edge_label(self, repo_with_annotations: Path) -> None:
        result = duckflow_mermaid(str(repo_with_annotations))
        assert "POST /api/generate-summary" in result

    def test_match_narrows_diagram(self, repo_with_annotations: Path) -> None:
        result = duckflow_mermaid(str(repo_with_annotations), match="summary.api")
        assert "summary.api" in result
        assert "summary.ui" not in result

    def test_classdefs_included(self, repo_with_annotations: Path) -> None:
        result = duckflow_mermaid(str(repo_with_annotations))
        assert "classDef live" in result
        assert "classDef planned" in result

    def test_status_class_applied(self, tmp_path: Path) -> None:
        (tmp_path / "planned.py").write_text(PLANNED_TEXT, encoding="utf-8")
        result = duckflow_mermaid(str(tmp_path))
        assert "class planned.route planned;" in result

    def test_nonexistent_repo_returns_error(self) -> None:
        result = duckflow_mermaid("/nonexistent/path/does/not/exist")
        assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# duckflow_mermaid_text
# ---------------------------------------------------------------------------


class TestDuckflowMermaidText:
    def test_returns_flowchart_header(self) -> None:
        result = duckflow_mermaid_text(PRODUCER_TEXT)
        assert result.startswith("flowchart TD")

    def test_contains_node_id(self) -> None:
        result = duckflow_mermaid_text(PRODUCER_TEXT)
        assert "summary.api" in result

    def test_match_filter(self) -> None:
        combined = PRODUCER_TEXT + "\n" + CONSUMER_TEXT
        result = duckflow_mermaid_text(combined, match="summary.api")
        assert "summary.api" in result
        assert "summary.ui" not in result

    def test_no_annotations_returns_flowchart_header_only(self) -> None:
        result = duckflow_mermaid_text("x = 1\n")
        assert "flowchart TD" in result

    def test_invalid_json_returns_error(self) -> None:
        bad = "# duckflow: {broken\n"
        result = duckflow_mermaid_text(bad)
        assert result.startswith("ERROR:")

    def test_planned_status_in_mermaid(self) -> None:
        result = duckflow_mermaid_text(PLANNED_TEXT)
        assert "class planned.route planned;" in result
