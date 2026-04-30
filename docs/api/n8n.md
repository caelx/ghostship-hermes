# n8n Public API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [n8n-openapi.json](./n8n-openapi.json)
- Companion reference: this file

## Service Identity

- Product: n8n Public API
- Version mirrored in repo: `1.1.0`
- Base API URL: `http(s)://<host>/<public-api-endpoint>/v1`
- Default base API URL: `http(s)://<host>/api/v1`
- Primary auth: `X-N8N-API-KEY`
- Built-in self-hosted docs UI: `/<public-api-endpoint>/v1/docs`
- Built-in self-hosted raw spec path: `/<public-api-endpoint>/v1/openapi.yml`

## Raw Spec Summary

- Format: bundled OpenAPI JSON converted from the official upstream `packages/cli/src/public-api/v1/openapi.yml`
- Path count: `41`
- Operation count: `66`
- Schema count: `63`
- Canonical source quality: official OpenAPI plus repo summary

## Auth, Versioning, And Pagination

- n8n authenticates public API calls with the `X-N8N-API-KEY` header.
- Self-hosted instances can move the public API base path from `api` by setting `N8N_PUBLIC_API_ENDPOINT`.
- The current published public API version is `v1`.
- Cursor pagination uses `limit` and `cursor`, with a default page size of `100`, a maximum page size of `250`, and `nextCursor` in paginated responses.
- Self-hosted operators can disable the public API with `N8N_PUBLIC_API_DISABLED=true` and disable the Swagger UI separately with `N8N_PUBLIC_API_SWAGGERUI_DISABLED=true`.

## Full Endpoint Group Inventory

The inventory below is taken from the mirrored official OpenAPI snapshot.

### Audit

- `1` operation: generate a security audit for the instance.

### Credentials

- `6` operations: list, create, update, delete, transfer, and inspect credential schemas.

### Executions

- `8` operations: list, fetch, delete, retry, stop one, stop many, list execution tags, and update execution tags.

### Tags

- `5` operations: list, fetch, create, update, and delete workflow tags.

### Workflows

- `13` operations: list, fetch, create, update, delete, fetch a version, activate, deactivate, archive, unarchive, transfer, list tags, and update tags.

### Users

- `5` operations: list, fetch, create, delete, and change global role.

### Source Control

- `1` operation: pull source control changes.

### Variables

- `4` operations: list, create, update, and delete variables.

### Data Tables

- `10` operations: list, fetch, create, update, delete, list rows, insert rows, update rows, upsert a row, and delete rows.

### Projects

- `8` operations: list, create, update, delete, list users, add users, delete a user, and change user role within a project.

### Community Packages

- `4` operations: list installed packages, install, update, and uninstall.

### Discover

- `1` operation: inspect available API capabilities and discover the instance `specUrl`.

## Repo Utility Surface

`ghostship-n8n` exposes:
- one dedicated snake_case CLI command for every operation in the mirrored official n8n public API contract
- one dedicated client method and one dedicated `build_...` dry-run builder for every mirrored operation
- generic repeated `--path-param name=value` and `--query-param key=value` options so the full public API can be covered without hand-maintaining per-endpoint flag sets
- `--body-json` for JSON request bodies where upstream operations accept one
- `request` as the escape hatch for debugging or temporary upstream drift

The repo persists the stable upstream contract in [n8n-openapi.json](./n8n-openapi.json). The self-hosted `openapi.yml` and Swagger UI endpoints remain useful runtime references, but they do not replace the committed repo snapshot.

## Source Material

- Local mirrored raw spec: [n8n-openapi.json](./n8n-openapi.json)
- Upstream docs: <https://docs.n8n.io/api/>
- Upstream API reference page: <https://docs.n8n.io/api/api-reference/>
- Upstream source-of-truth path: `packages/cli/src/public-api/v1/openapi.yml`
- Upstream repository: <https://github.com/n8n-io/n8n>
