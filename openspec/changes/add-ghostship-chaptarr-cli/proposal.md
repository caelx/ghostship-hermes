# Add ghostship-chaptarr

## Summary

Add a repo-owned `ghostship-chaptarr` utility that exposes the Chaptarr public API (the Readarr-derived public API that ships inside the `robertlordhood/chaptarr` container) with the same JSON-first CLI contract we use for other integrations. The change must document the API, bundle the official OpenAPI snapshot in `docs/api`, and ensure the utility and its docs appear in the Hermes image.

## Motivation
- Operators already run the published `robertlordhood/chaptarr` Docker image in our environments; it exposes an official Swagger/OpenAPI surface under `/api/v1` that requires a configurable `X-Api-Key` header.
- There is no current `ghostship-*` wrapper for Chaptarr, so automation and diagnostics rely on ad-hoc curl calls.
- The new CLI will make every endpoint in the OpenAPI contract available, matching the design of `ghostship-n8n` and `ghostship-radarr`, and it will reuse the same env-driven config and shared CLI plumbing.

## Key Deliverables
1. Persist the canonical OpenAPI spec in `docs/api/chaptarr-openapi.json` (pulled from `https://raw.githubusercontent.com/Readarr/Readarr/develop/src/Readarr.Api.V1/openapi.json`) and document auth + pagination + endpoint coverage in `docs/api/chaptarr.md`.
2. Create `packages/chaptarr-cli` (based on `ghostship-cli-contract`) that reads `CHAPTARR_URL`/`CHAPTARR_API_KEY` (and optional path/version overrides) and emits `ghostship-chaptarr` with commands for each operation defined in the spec plus a `request` escape hatch, all honoring the shared `--timeout` and `--dry-run` contracts.
3. Wire the package into `flake.nix` and the Hermes image so the CLI is always on the runtime path, and update README/CHANGELOG/AGENTS guidance to include the new utility and its env vars.

## API Surface References
- Official OpenAPI: `https://raw.githubusercontent.com/Readarr/Readarr/develop/src/Readarr.Api.V1/openapi.json` (mirrored in `references/chaptarr-openapi.json`).
- Live behavior verified by running `docker run -p 8789:8789 --name chaptarr-test robertlordhood/chaptarr` and calling `/api/v1/system/status` with `X-Api-Key` as configured in `/config/config.xml`.
