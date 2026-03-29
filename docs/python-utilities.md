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
- **Use environment variables**: Configuration should be sourced from environment variables (e.g., `APP_URL`, `APP_API_KEY`).
- **Avoid interactive prompts**: All tools must be fully automatable.
- **Use stable flag names**: Ensure consistency across different utilities.
- **Include unit tests**: Verify core logic and CLI interface with mocks.

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
