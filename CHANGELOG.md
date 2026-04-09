# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-09

### Added
- Initial release of `duckflow`.
- `DuckflowEntry` dataclass for normalized annotation data.
- `extract_duckflow_entries_from_text` for parsing inline JSON annotations from
  source comments (`#`, `//`, `/* */` styles).
- `extract_duckflow_entries` for recursive source-tree scanning.
- `iter_source_files` with configurable glob patterns and exclude-parts.
- `filter_entries` for substring-based filtering across all fields.
- `stitch_duckflow` to build a control/data-flow graph from local facts.
- `render_mermaid` to emit a Mermaid `flowchart TD` diagram.
- `duckflow-extract` and `duckflow-mermaid` CLI entry points.
- Mandatory UTC `timestamp` validation on every annotation.

[Unreleased]: https://github.com/Warnes-Innovations/duckflow/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Warnes-Innovations/duckflow/releases/tag/v0.1.0
