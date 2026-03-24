#!/usr/bin/env python3
# Copyright (C) 2026 Gregory R. Warnes
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Extract normalized duckflow entries from source comments."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Callable


ExtractEntriesFn = Callable[..., list[Any]]
FilterEntriesFn = Callable[..., list[Any]]
StitchDuckflowFn = Callable[..., dict[str, Any]]


def _load_duckflow_api(
) -> tuple[ExtractEntriesFn, FilterEntriesFn, StitchDuckflowFn]:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    duckflow_module = importlib.import_module("duckflow")

    return (
        getattr(duckflow_module, "extract_duckflow_entries"),
        getattr(duckflow_module, "filter_entries"),
        getattr(duckflow_module, "stitch_duckflow"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument(
        "--stitched",
        action="store_true",
        help="Emit stitched graph JSON instead of flat entry JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    (
        extract_duckflow_entries,
        filter_entries,
        stitch_duckflow,
    ) = _load_duckflow_api()
    entries = extract_duckflow_entries(args.repo_root, include=args.include)
    entries = filter_entries(entries, args.match)
    payload: dict[str, Any] | list[dict[str, Any]]
    if args.stitched:
        payload = stitch_duckflow(entries)
    else:
        payload = [entry.to_dict() for entry in entries]
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
