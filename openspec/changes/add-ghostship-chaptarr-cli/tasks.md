## 1. API Documentation

- [ ] Inventory the OpenAPI operations (from `references/chaptarr-openapi.json`) and describe auth, pagination, and tag coverage in `docs/api/chaptarr.md`.
- [ ] Mirror the raw spec into `docs/api/chaptarr-openapi.json` and add the new row to `docs/api/README.md`.
- [ ] Note the required environment variables (`CHAPTARR_URL`, `CHAPTARR_API_KEY`, optional `CHAPTARR_API_PATH`, `CHAPTARR_API_VERSION`) in the docs, README, and AGENTS guidance.

## 2. Package and Client

- [ ] Scaffold `packages/chaptarr-cli` with README, `pyproject.toml`, `package.nix`, and a Python package that depends on `ghostship-cli-contract`.
- [ ] Implement `ghostship_chaptarr.client` to wrap `BaseHttpClient`, handle base path overrides, and attach `X-Api-Key` headers.
- [ ] Generate `ghostship_chaptarr.catalog` data from the OpenAPI spec and a CLI (`ghostship_chaptarr.cli`) that registers one command per operation plus a generic `request` command, following the shared CLI contract.

## 3. Command Coverage and Tests

- [ ] Add unit tests covering the catalog, client request plumbing, and CLI command generation (using mock transports for `httpx`).
- [ ] Ensure mutations expose `--dry-run`, commands accept `--timeout`, and the CLI emits JSON by default while providing `--pretty` when requested.

## 4. Wiring and Verification

- [ ] Expose `ghostship-chaptarr` in `flake.nix`, include it in `ghostshipUtilities`, and ensure the Hermes image pulls it onto `$PATH`.
- [ ] Update `README.md`, `CHANGELOG.md`, and `AGENTS.md` to mention the new utility and its env vars.
- [ ] Run relevant `python3 scripts/python_utility.py` flows (lock, test, build) plus `nix build`/`nix eval` to confirm the package compiles and the image sees the CLI.
