# chaptarr-cli Delta Specification

## Purpose

Document the addition of the repo-owned `ghostship-chaptarr` CLI, the mirrored Chaptarr OpenAPI artifact, and the supporting documentation required for the change.

## ADDED Requirements

### Requirement: Hermes SHALL ship the `ghostship-chaptarr` CLI that mirrors the upstream Chaptarr public API
The repo SHALL provide a `ghostship-chaptarr` CLI as a first-class `ghostship-*` utility and ensure the package is built, evaluated, and added to the Hermes runtime so the service navigates the entire upstream public API via snake_case commands.

#### Scenario: Repository evaluation exposes the package
- **WHEN** maintainers build or evaluate `packages.x86_64-linux.ghostship-chaptarr`
- **THEN** the package builds successfully and provides the mirror of the Chaptarr public API surface

#### Scenario: Hermes evaluation includes the CLI
- **WHEN** maintainers inspect `ghostshipHermesSystem` or the runtime service wiring
- **THEN** `ghostship-chaptarr` is included alongside the other `ghostship-*` utilities on the shared PATH

### Requirement: The repo SHALL document auth/environment and spec coverage for Chaptarr
The repo SHALL bundle the official OpenAPI snapshot under `docs/api/`, document the env var contract in Markdown/AGENTS guidance, and highlight the new utility in the API index so operators know how to configure and use the CLI.

#### Scenario: Documentation surfaces configure points
- **WHEN** maintainers consult `docs/api/chaptarr.md`, `docs/api/README.md`, or `AGENTS.md`
- **THEN** they find the mirrored spec location plus the required `CHAPTARR_URL`/`CHAPTARR_API_KEY`/`CHAPTARR_API_PATH`/`CHAPTARR_API_VERSION` guidance

#### Scenario: Tests verify CLI behavior
- **WHEN** maintainers run the CLI tests
- **THEN** every command respects `--timeout`, dry-run coverage, and JSON output by default
