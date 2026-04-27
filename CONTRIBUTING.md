# Contributing

## Workflow

- use the flake-based shell via `direnv`
- keep shell snippets in Fish syntax in docs and developer notes
- add or update focused tests before changing router, dashboard, or image runtime behavior
- validate Nix changes with `nix build` or `nix flake check` before opening a PR

## Pull Requests

- keep changes focused
- update `README.md`, `CHANGELOG.md`, and `AGENTS.md` when behavior or workflow changes
- include verification commands and outcomes in the PR description
