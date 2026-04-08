# Design for ghostship-chaptarr

## Architecture

1. **API mirror** – Save the Readarr public API OpenAPI (available at https://raw.githubusercontent.com/Readarr/Readarr/develop/src/Readarr.Api.V1/openapi.json) into `docs/api/chaptarr-openapi.json`, and keep it alongside `docs/api/chaptarr.md` which highlights the base URL (`/api/v1`), the `X-Api-Key` auth header, pagination patterns, and coverage of the cataloged tags (System, Books, Authors, Series, Imports, Tasks, etc.).
2. **Chaptarr client** – Build `ghostship_chaptarr` core that extends `ghostship-cli-contract.BaseHttpClient`, configures the base URL from `CHAPTARR_URL` (default `http://localhost:8789`), and injects `X-Api-Key` from `CHAPTARR_API_KEY`. Provide optional overrides for `CHAPTARR_API_PATH` (defaults to `/api`) and `CHAPTARR_API_VERSION` (defaults to `v1`) so self-hosted changes to the prefix can be handled.
3. **Command generation** – Derive operation metadata from the mirrored OpenAPI (similar to the n8n catalog): every operation gets a snake_case command, `--path-param`/`--query-param` pairs, optional `--body-json`, `--dry-run` for mutations, and shared `--timeout` and `--pretty` options. Include a fallback `request` command for manual spec-driven calls.
4. **Runtime wiring** – Expose `ghostship-chaptarr` from the flake, add it to `ghostshipUtilities`, and ensure the Hermes image profile installs it. Update `README.md`, `CHANGELOG.md`, and `AGENTS.md` sections that list env vars/utilities to reference the new CLI and remind operators to set `CHAPTARR_URL`/`CHAPTARR_API_KEY`.

## Verification flow

- Use `docker run -p 8789:8789 --name chaptarr-test robertlordhood/chaptarr` to confirm the service boots and the default API key is stored in `/config/config.xml` (already observed as `a96ffe42fdf749048c80ed3488431b83`).
- Query `/api/v1/system/status` with `X-Api-Key` to prove the baseline endpoint works (the CLI will mirror this as `ghostship-chaptarr get_system_status`).
- Confirm the raw OpenAPI is accessible inside the container (no built-in swagger endpoint; we rely on upstream `Readarr` spec) and that the CLI’s generated commands align with the spec’s paths.

## Tooling

- Mirror generation of `OperationDef` data from the OpenAPI spec in `packages/chaptarr-cli/src/ghostship_chaptarr/catalog.py`, just like `packages/n8n-cli` does.
- Keep tests in `packages/chaptarr-cli/tests/` that run the catalog, client, and CLI argument parsing (mock API responses with `httpx.MockTransport`).
- Document the environment variables in the package README and in `docs/api/chaptarr.md` so downstream automation knows to set `CHAPTARR_URL`/`CHAPTARR_API_KEY`.
