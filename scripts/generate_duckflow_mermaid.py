#!/usr/bin/env python3
# Copyright (C) 2026 Gregory R. Warnes
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Render stitched duckflow annotations as Mermaid flowchart markup."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def main() -> int:
    duckflow_cli = importlib.import_module("duckflow.cli")
    return duckflow_cli.mermaid_main()


if __name__ == "__main__":
    raise SystemExit(main())
