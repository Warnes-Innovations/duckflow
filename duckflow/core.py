#!/usr/bin/env python3
# Copyright (C) 2026 Gregory R. Warnes
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Helpers for extracting and rendering duckflow annotations."""

from __future__ import annotations

from datetime import datetime
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


COMMENT_PREFIX_RE = re.compile(r"^\s*(?:#|//|/\*+|\*+/|\*|\{#)\s?")
COMMENT_SUFFIX_RE = re.compile(r"\s*(?:\*/|#\})\s*$")
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ALLOWED_FIELDS = frozenset({
    "id",
    "kind",
    "timestamp",
    "status",
    "handles",
    "calls",
    "reads",
    "writes",
    "returns",
    "notes",
})
ALLOWED_STATUSES = frozenset({"live", "planned", "shared"})
DEFAULT_INCLUDE_GLOBS = (
    "**/*.py",
    "**/*.js",
    "**/*.ts",
    "**/*.tsx",
    "**/*.jsx",
    "**/*.java",
    "**/*.go",
    "**/*.rs",
    "**/*.sh",
)
DEFAULT_EXCLUDE_PARTS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "coverage",
        "htmlcov",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".next",
        "target",
    }
)


@dataclass(frozen=True)
class DuckflowEntry:
    """Normalized duckflow annotation plus source location."""

    id: str
    kind: str
    timestamp: str
    status: str
    handles: tuple[str, ...]
    calls: tuple[str, ...]
    reads: tuple[str, ...]
    writes: tuple[str, ...]
    returns: tuple[str, ...]
    notes: str
    path: str
    line: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "timestamp": self.timestamp,
            "status": self.status,
            "handles": list(self.handles),
            "calls": list(self.calls),
            "reads": list(self.reads),
            "writes": list(self.writes),
            "returns": list(self.returns),
            "notes": self.notes,
            "path": self.path,
            "line": self.line,
        }


def _strip_comment_prefix(line: str) -> str:
    cleaned = COMMENT_PREFIX_RE.sub("", line.rstrip("\n"))
    return COMMENT_SUFFIX_RE.sub("", cleaned).rstrip()


def _is_supported_comment_line(line: str) -> bool:
    return bool(COMMENT_PREFIX_RE.match(line))


def _collect_yaml_payload_lines(
    lines: list[str],
    index: int,
) -> tuple[list[str], int, bool]:
    current_line = lines[index]
    payload_lines: list[str] = []
    cleaned = _strip_comment_prefix(current_line)
    _, payload = cleaned.split("duckflow:", 1)
    first_payload_line = payload.lstrip()
    has_inline_payload = bool(first_payload_line)
    if first_payload_line:
        payload_lines.append(first_payload_line)

    next_index = index + 1
    is_jinja_block = (
        current_line.lstrip().startswith("{#")
        and "#}" not in current_line
    )
    is_c_block = (
        current_line.lstrip().startswith("/*")
        and "*/" not in current_line
    )
    if is_jinja_block:
        while next_index < len(lines):
            raw_line = lines[next_index]
            cleaned_line = _strip_comment_prefix(raw_line)
            payload_lines.append(cleaned_line)
            next_index += 1
            if "#}" in raw_line:
                break
        return payload_lines, next_index, has_inline_payload

    while next_index < len(lines):
        next_line = lines[next_index]
        if not _is_supported_comment_line(next_line):
            break
        cleaned_line = _strip_comment_prefix(next_line)
        if "duckflow:" in cleaned_line:
            break
        payload_lines.append(cleaned_line)
        next_index += 1
        if is_c_block and "*/" in next_line:
            break

    return payload_lines, next_index, has_inline_payload


def _normalize_payload_indentation(
    payload_lines: list[str],
    has_inline_payload: bool,
) -> list[str]:
    start_index = 1 if has_inline_payload else 0
    indents = [
        len(line) - len(line.lstrip(" "))
        for line in payload_lines[start_index:]
        if line.strip()
    ]
    if not indents:
        return payload_lines

    common_indent = min(indents)
    if common_indent == 0:
        return payload_lines

    normalized = payload_lines[:start_index]
    normalized.extend(
        line[common_indent:] if line.strip() else ""
        for line in payload_lines[start_index:]
    )
    return normalized


def _parse_duckflow_payload(
    lines: list[str],
    index: int,
    path: Path,
) -> tuple[dict[str, Any], int, int]:
    line_number = index + 1
    payload_lines, next_index, has_inline_payload = _collect_yaml_payload_lines(
        lines,
        index,
    )
    payload_lines = _normalize_payload_indentation(
        payload_lines,
        has_inline_payload,
    )
    payload_text = "\n".join(payload_lines).strip()
    if not payload_text:
        raise ValueError(f"{path}:{line_number}: empty duckflow payload")
    if payload_text.startswith(("{", "[")):
        raise ValueError(
            f"{path}:{line_number}: duckflow payload must use YAML mapping syntax"
        )
    try:
        parsed = yaml.safe_load(payload_text)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"{path}:{line_number}: invalid duckflow YAML payload"
        ) from exc
    return parsed, next_index, line_number


def _as_string_list(
    value: Any,
    field_name: str,
    entry_id: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValueError(
            f"{entry_id}: '{field_name}' must be a list of strings"
        )
    return tuple(value)


def _normalize_timestamp(value: Any, entry_id: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"{entry_id}: 'timestamp' must be a non-empty string"
        )

    try:
        datetime.strptime(value, TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ValueError(
            f"{entry_id}: 'timestamp' must use UTC format YYYY-MM-DDTHH:MM:SSZ"
        ) from exc

    return value


def _normalize_entry(
    data: dict[str, Any],
    path: Path,
    line: int,
) -> DuckflowEntry:
    unknown_fields = sorted(set(data) - ALLOWED_FIELDS)
    if unknown_fields:
        raise ValueError(
            f"{path}:{line}: duckflow payload contains unsupported fields: {', '.join(unknown_fields)}"
        )

    entry_id = data.get("id")
    kind = data.get("kind")
    if not isinstance(entry_id, str) or not entry_id:
        raise ValueError(
            f"{path}:{line}: duckflow entry must define non-empty 'id'"
        )
    if not isinstance(kind, str) or not kind:
        raise ValueError(
            f"{path}:{line}: duckflow entry must define non-empty 'kind'"
        )
    timestamp = _normalize_timestamp(data.get("timestamp"), entry_id)

    status = data.get("status", "live")
    if not isinstance(status, str) or not status:
        raise ValueError(
            f"{entry_id}: 'status' must be a non-empty string when present"
        )
    if status not in ALLOWED_STATUSES:
        raise ValueError(
            f"{entry_id}: 'status' must be one of {', '.join(sorted(ALLOWED_STATUSES))}"
        )

    notes = data.get("notes", "")
    if notes is None:
        notes = ""
    if not isinstance(notes, str):
        raise ValueError(f"{entry_id}: 'notes' must be a string when present")

    return DuckflowEntry(
        id=entry_id,
        kind=kind,
        timestamp=timestamp,
        status=status,
        handles=_as_string_list(data.get("handles"), "handles", entry_id),
        calls=_as_string_list(data.get("calls"), "calls", entry_id),
        reads=_as_string_list(data.get("reads"), "reads", entry_id),
        writes=_as_string_list(data.get("writes"), "writes", entry_id),
        returns=_as_string_list(data.get("returns"), "returns", entry_id),
        notes=notes,
        path=str(path),
        line=line,
    )


def extract_duckflow_entries_from_text(
    text: str,
    path: Path,
) -> list[DuckflowEntry]:
    """Return all duckflow entries found in the given source text."""
    entries: list[DuckflowEntry] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not _is_supported_comment_line(line):
            index += 1
            continue

        cleaned = _strip_comment_prefix(line)
        if "duckflow:" not in cleaned:
            index += 1
            continue

        data, index, line_number = _parse_duckflow_payload(lines, index, path)
        if not isinstance(data, dict):
            raise ValueError(
                f"{path}:{line_number}: duckflow payload must be a YAML mapping"
            )
        entries.append(_normalize_entry(data, path, line_number))

    return entries


def iter_source_files(
    repo_root: Path,
    include: Iterable[str] | None = None,
    exclude_parts: Iterable[str] | None = None,
) -> list[Path]:
    """Return a stable list of files to scan for duckflow annotations."""
    patterns = (
        tuple(include) if include is not None else DEFAULT_INCLUDE_GLOBS
    )
    excluded = (
        frozenset(exclude_parts)
        if exclude_parts is not None
        else DEFAULT_EXCLUDE_PARTS
    )
    files: set[Path] = set()
    for pattern in patterns:
        files.update(
            path
            for path in repo_root.glob(pattern)
            if path.is_file()
            and not any(part in excluded for part in path.parts)
        )
    return sorted(files)


def extract_duckflow_entries(
    repo_root: Path,
    include: Iterable[str] | None = None,
    exclude_parts: Iterable[str] | None = None,
) -> list[DuckflowEntry]:
    """Scan source files beneath repo_root for duckflow annotations."""
    entries: list[DuckflowEntry] = []
    for path in iter_source_files(
        repo_root,
        include=include,
        exclude_parts=exclude_parts,
    ):
        text = path.read_text(encoding="utf-8")
        entries.extend(
            extract_duckflow_entries_from_text(
                text,
                path.relative_to(repo_root),
            )
        )
    return sorted(
        entries,
        key=lambda entry: (entry.path, entry.line, entry.id),
    )


def filter_entries(
    entries: Iterable[DuckflowEntry],
    match: str | None = None,
) -> list[DuckflowEntry]:
    """Filter entries by id, path, token, or notes substring."""
    all_entries = list(entries)
    if not match:
        return all_entries

    needle = match.lower()
    filtered: list[DuckflowEntry] = []
    for entry in all_entries:
        haystacks = [
            entry.id,
            entry.kind,
            entry.status,
            entry.path,
            entry.notes,
            *entry.handles,
            *entry.calls,
            *entry.reads,
            *entry.writes,
            *entry.returns,
        ]
        if any(needle in item.lower() for item in haystacks):
            filtered.append(entry)
    return filtered


def _statuses_compatible(source: DuckflowEntry, target: DuckflowEntry) -> bool:
    return (
        source.status == target.status
        or source.status == "shared"
        or target.status == "shared"
    )


def stitch_duckflow(entries: Iterable[DuckflowEntry]) -> dict[str, Any]:
    """Build a stitched graph from local duckflow facts."""
    node_list = list(entries)
    node_by_id = {entry.id: entry for entry in node_list}
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for source in node_list:
        source_outputs = set(source.writes) | set(source.returns)
        for target in node_list:
            if source.id == target.id:
                continue
            if not _statuses_compatible(source, target):
                continue

            shared_calls = sorted(set(source.calls) & set(target.handles))
            for token in shared_calls:
                key = (source.id, target.id, "call", token)
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        "source": source.id,
                        "target": target.id,
                        "kind": "call",
                        "token": token,
                    })

            shared_data = sorted(source_outputs & set(target.reads))
            for token in shared_data:
                key = (source.id, target.id, "data", token)
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        "source": source.id,
                        "target": target.id,
                        "kind": "data",
                        "token": token,
                    })

    return {
        "nodes": [
            node_by_id[node_id].to_dict()
            for node_id in sorted(node_by_id)
        ],
        "edges": sorted(
            edges,
            key=lambda edge: (
                edge["source"],
                edge["target"],
                edge["kind"],
                edge["token"],
            ),
        ),
    }


def _mermaid_label(entry: DuckflowEntry) -> str:
    short_path = f"{entry.path}:{entry.line}"
    return f"{entry.id}<br/>{entry.kind} [{entry.status}]<br/>{short_path}"


def render_mermaid(graph: dict[str, Any]) -> str:
    """Render a stitched duckflow graph as Mermaid flowchart markup."""
    lines = [
        "flowchart TD",
        "  classDef live fill:#dcfce7,stroke:#166534,color:#14532d;",
        (
            "  classDef planned fill:#fef3c7,stroke:#b45309,"
            "color:#78350f,stroke-dasharray: 5 3;"
        ),
        "  classDef shared fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a;",
    ]

    for node in graph["nodes"]:
        entry = DuckflowEntry(
            id=node["id"],
            kind=node["kind"],
            timestamp=node["timestamp"],
            status=node["status"],
            handles=tuple(node["handles"]),
            calls=tuple(node["calls"]),
            reads=tuple(node["reads"]),
            writes=tuple(node["writes"]),
            returns=tuple(node["returns"]),
            notes=node["notes"],
            path=node["path"],
            line=node["line"],
        )
        lines.append(f'  {entry.id}["{_mermaid_label(entry)}"]')
        lines.append(f"  class {entry.id} {entry.status};")

    for edge in graph["edges"]:
        prefix = "call" if edge["kind"] == "call" else "data"
        lines.append(
            f'  {edge["source"]} -->|{prefix}: {edge["token"]}| '
            f'{edge["target"]}'
        )

    return "\n".join(lines)


__all__ = [
    "DEFAULT_EXCLUDE_PARTS",
    "DEFAULT_INCLUDE_GLOBS",
    "DuckflowEntry",
    "extract_duckflow_entries",
    "extract_duckflow_entries_from_text",
    "filter_entries",
    "iter_source_files",
    "render_mermaid",
    "stitch_duckflow",
]
