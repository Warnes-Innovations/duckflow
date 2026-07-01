#!/usr/bin/env python3
# Copyright (C) 2026 Gregory R. Warnes
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Duckflow MCP Server — tools for data-flow annotation extraction and rendering.

Uses FastMCP for concise tool registration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from duckflow.core import (
    extract_duckflow_entries,
    extract_duckflow_entries_from_text,
    filter_entries,
    render_mermaid,
    stitch_duckflow,
)

mcp = FastMCP(
    "duckflow-mcp",
    instructions=(
        "Duckflow tools for extracting, stitching, and rendering "
        "comment-based data-flow annotations."
    ),
)

_TOOL_EXCEPTIONS = (OSError, ValueError, json.JSONDecodeError)


# ---------------------------------------------------------------------------
# Tool: duckflow_extract
# ---------------------------------------------------------------------------


@mcp.tool()
def duckflow_extract(
    repo_root: str,
    include: Optional[list[str]] = None,
    match: Optional[str] = None,
    stitched: bool = False,
) -> str:
    """Extract duckflow annotations from source files beneath repo_root.

    Args:
        repo_root: Absolute path to the repository root to scan.
        include: Optional list of glob patterns to restrict which source files
                 are scanned (e.g. ["src/**/*.py", "web/**/*.ts"]).
                 Defaults to all supported source-file extensions.
        match: Optional substring filter applied across entry ids, kinds,
               statuses, paths, notes, and tokens.  Only matching entries
               are returned.
        stitched: When True, return a stitched graph object with "nodes" and
                  "edges" keys instead of a flat list of entries.
    """
    try:
        root = Path(repo_root)
        if not root.exists():
            return f"ERROR: repo_root does not exist: {repo_root}"
        entries = extract_duckflow_entries(root, include=include)
        entries = filter_entries(entries, match)
        if stitched:
            return json.dumps(stitch_duckflow(entries), indent=2)
        return json.dumps([e.to_dict() for e in entries], indent=2)
    except _TOOL_EXCEPTIONS as exc:
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Tool: duckflow_extract_text
# ---------------------------------------------------------------------------


@mcp.tool()
def duckflow_extract_text(
    text: str,
    path: str = "<inline>",
    match: Optional[str] = None,
) -> str:
    """Extract duckflow annotations directly from a string of source text.

    Useful when the source code is already loaded in the conversation rather
    than residing on disk.

    Args:
        text: Source text to scan for duckflow annotations.
        path: Logical file path to use in error messages and entry metadata
              (default: "<inline>").
        match: Optional substring filter.
    """
    try:
        entries = extract_duckflow_entries_from_text(text, Path(path))
        entries = filter_entries(entries, match)
        return json.dumps([e.to_dict() for e in entries], indent=2)
    except _TOOL_EXCEPTIONS as exc:
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Tool: duckflow_stitch
# ---------------------------------------------------------------------------


@mcp.tool()
def duckflow_stitch(
    repo_root: str,
    include: Optional[list[str]] = None,
    match: Optional[str] = None,
) -> str:
    """Build a stitched duckflow graph from all annotations in repo_root.

    The graph contains "nodes" (all matching entries) and "edges" stitched
    from call / data relationships between them.

    Args:
        repo_root: Absolute path to the repository root to scan.
        include: Optional list of glob patterns (see duckflow_extract).
        match: Optional substring filter applied before stitching.
    """
    try:
        root = Path(repo_root)
        if not root.exists():
            return f"ERROR: repo_root does not exist: {repo_root}"
        entries = extract_duckflow_entries(root, include=include)
        entries = filter_entries(entries, match)
        return json.dumps(stitch_duckflow(entries), indent=2)
    except _TOOL_EXCEPTIONS as exc:
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Tool: duckflow_mermaid
# ---------------------------------------------------------------------------


@mcp.tool()
def duckflow_mermaid(
    repo_root: str,
    include: Optional[list[str]] = None,
    match: Optional[str] = None,
) -> str:
    """Render a Mermaid flowchart for all duckflow annotations in repo_root.

    Returns the raw Mermaid markup as a string.

    Args:
        repo_root: Absolute path to the repository root to scan.
        include: Optional list of glob patterns (see duckflow_extract).
        match: Optional substring filter to restrict which entries appear
               in the rendered diagram.
    """
    try:
        root = Path(repo_root)
        if not root.exists():
            return f"ERROR: repo_root does not exist: {repo_root}"
        entries = extract_duckflow_entries(root, include=include)
        entries = filter_entries(entries, match)
        graph = stitch_duckflow(entries)
        return render_mermaid(graph)
    except _TOOL_EXCEPTIONS as exc:
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Tool: duckflow_mermaid_text
# ---------------------------------------------------------------------------


@mcp.tool()
def duckflow_mermaid_text(
    text: str,
    path: str = "<inline>",
    match: Optional[str] = None,
) -> str:
    """Render a Mermaid flowchart directly from a string of source text.

    Args:
        text: Source text to scan for duckflow annotations.
        path: Logical file path used in node labels (default: "<inline>").
        match: Optional substring filter.
    """
    try:
        entries = extract_duckflow_entries_from_text(text, Path(path))
        entries = filter_entries(entries, match)
        graph = stitch_duckflow(entries)
        return render_mermaid(graph)
    except _TOOL_EXCEPTIONS as exc:
        return f"ERROR: {exc}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
