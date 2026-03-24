# Copyright (C) 2026 Gregory R. Warnes
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CLI entry points for duckflow extraction and Mermaid generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import (
    extract_duckflow_entries,
    filter_entries,
    render_mermaid,
    stitch_duckflow,
)


def _build_common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--repo-root",
        default=Path.cwd(),
        type=Path,
        help="Repository root to scan (default: current working directory)",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=None,
        help="Repeatable glob of source files to include",
    )
    parser.add_argument(
        "--match",
        default=None,
        help=(
            "Filter entries by substring across ids, paths, notes, "
            "and tokens"
        ),
    )
    return parser


def parse_extract_args() -> argparse.Namespace:
    parser = _build_common_parser(
        "Extract normalized duckflow entries from source comments."
    )
    parser.add_argument(
        "--stitched",
        action="store_true",
        help="Emit stitched graph JSON instead of flat entry JSON",
    )
    return parser.parse_args()


def parse_mermaid_args() -> argparse.Namespace:
    return _build_common_parser(
        "Render stitched duckflow annotations as Mermaid flowchart markup."
    ).parse_args()


def extract_main() -> int:
    args = parse_extract_args()
    entries = extract_duckflow_entries(args.repo_root, include=args.include)
    entries = filter_entries(entries, args.match)
    payload: dict[str, Any] | list[dict[str, Any]]
    if args.stitched:
        payload = stitch_duckflow(entries)
    else:
        payload = [entry.to_dict() for entry in entries]
    print(json.dumps(payload, indent=2))
    return 0


def mermaid_main() -> int:
    args = parse_mermaid_args()
    entries = extract_duckflow_entries(args.repo_root, include=args.include)
    graph = stitch_duckflow(filter_entries(entries, args.match))
    print(render_mermaid(graph))
    return 0


__all__ = [
    "extract_main",
    "mermaid_main",
    "parse_extract_args",
    "parse_mermaid_args",
]
