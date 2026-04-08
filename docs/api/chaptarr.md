# Chaptarr API Spec Sheet

Canonical artifacts:
- Raw spec mirror: `docs/api/chaptarr-openapi.json`
- Companion reference: this file

## Service Identity

- Product: Chaptarr (Readarr fork for audiobooks and ebooks)
- Version mirrored in repo: 1.0.0 (OpenAPI `info.version`)
- Base API URL: `http(s)://<host><CHAPTARR_API_PATH:-/api>/<CHAPTARR_API_VERSION:-v1>`
- Primary auth: `X-Api-Key` header (set via `CHAPTARR_API_KEY`)

## Auth + Env contract

- `CHAPTARR_URL` defaults to `http://localhost:8789` when unspecified.
- `CHAPTARR_API_PATH` can override the `/api` prefix; `CHAPTARR_API_VERSION` defaults to `v1`.
- Every request from `ghostship-chaptarr` sends `X-Api-Key: <CHAPTARR_API_KEY>` and respects the shared `--timeout`/`--dry-run` CLI options that cache the request before mutating.

## Pagination and Patterns

- Most list endpoints follow the Readarr pagination model (`page`, `pageSize`, `sortKey`, `sortDirection`).
- The API supports filtering via query params (e.g., `authorId`, `status`, `upcomingReleaseDate`) and path parameters for specific resources.
- Command names pair with HTTP verbs: `GET` for `get_` helpers, `POST` for `create_`, `PUT`/`PATCH` for `update_`, `DELETE` for `delete_`.

## Endpoint Coverage Summary

The OpenAPI spec covers the following tags (among others):

- `System`: `/system/status`, `/system/jobs`, `/system/heartbeat`
- `Book`: `/book`, `/book/{id}`, `/book/manual-import`
- `Author`, `Series`, `Edition`, `Import`, `Task`, `File`, `CustomFormat`
- `Notification`, `Queue`, `Release`: automatic tasks queued for downloads and metadata
- `Settings`: config endpoints under `/config/*` for host, indexer, quality, naming, etc.

Every operation listed in `docs/api/chaptarr-openapi.json` is mirrored by a snake_case `ghostship-chaptarr` command, with a `request` escape hatch when the spec evolves faster than the CLI generator.

## Tooling Notes

- Use `CHAPTARR_API_KEY` to authenticate; the default key in the official image is stored in `/config/config.xml` and can be discovered there when booting the container.
- For deep automation, inspect `ghostship_chaptarr.catalog.OperationDef` to see which path/query params each command exposes.
