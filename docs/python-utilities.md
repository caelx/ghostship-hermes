# Python Utilities

This repository standardizes Python utility packaging so every repo-owned CLI behaves the same way.

## Naming

- project name must start with `ghostship-`
- executable name should start with `ghostship-`
- import package should use underscores, for example `ghostship_searxng`

## Required Layout

Every Python utility should include:

- `pyproject.toml`
- `package.nix`
- `uv.lock`
- `README.md`
- `src/<import_name>/`
- `tests/`

## Standard Commands

All utilities should use the shared helper:

```fish
python3 scripts/python_utility.py lock <package-dir>
python3 scripts/python_utility.py test <package-dir>
python3 scripts/python_utility.py build <package-dir>
```

Current example:

```fish
python3 scripts/python_utility.py lock packages/searxng-cli
python3 scripts/python_utility.py test packages/searxng-cli
python3 scripts/python_utility.py build packages/searxng-cli
```

## Behavioral Contract

Python utilities in this repo should:

- **Output native JSON by default**: All commands MUST output valid JSON to stdout.
- **Support `--pretty`**: Provide a flag for formatted, human-readable JSON output.
- **No rich tables**: Avoid tables, colors, or other terminal-specific formatting in the default output path.
- **Use environment variables as the runtime interface**: Commands may read `APP_URL`, `APP_API_KEY`, and similar values from environment variables at process launch time.
- **Avoid interactive prompts**: All tools must be fully automatable.
- **Use stable flag names**: Ensure consistency across different utilities.
- **Include unit tests**: Verify core logic and CLI interface with mocks.

## Source Of Truth Policy

New `ghostship-*` utilities should follow this split:

- `bw` is the image-managed Bitwarden CLI for operator-managed vault access; `bw-unlock` and `bw-lock` are the supported session wrappers.
- `BITWARDENCLI_APPDATA_DIR=/home/hermes/.local/state/bitwarden-cli` is the persisted Bitwarden CLI state path.
- `bw-lock` locks/removes the active runtime session but does not log out of the persisted Bitwarden account.
- Service credentials and automation-compatible website credentials belong in Bitwarden by default.
- Service URLs, hostnames, ports, profile names, workspace paths, and similar local topology belong in env/config by default unless the value itself contains credential material.
- If a utility still consumes secrets through env vars, treat those env vars as the runtime interface only. Do not document them as the preferred durable storage location for secrets.
- Prefer examples that materialize only the secret values needed for one command or workflow rather than exporting a large long-lived shell environment.

## Nix Packaging

Each utility should export a Nix package via `package.nix` using `buildPythonApplication`.

At minimum, the package should define:

- `pname`
- `version`
- `pyproject = true`
- build-system requirements
- runtime dependencies
- `pythonImportsCheck`

If tests can run inside the Nix builder, wire them through the package definition so `nix flake check` covers them.

## CI Expectations

CI should:

- run the shared `test` helper
- run the shared `build` helper
- keep utility verification separate from image/runtime verification when possible
