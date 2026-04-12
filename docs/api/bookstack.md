# BookStack API Spec Sheet

Canonical artifacts:

- Raw docs capture: [bookstack-api-docs.html](./bookstack-api-docs.html)
- Normalized docs snapshot: [bookstack-docs.json](./bookstack-docs.json)
- Companion reference: this file

## Service Identity

- Product: BookStack REST API
- Capture date: `2026-04-12`
- Base API URL: `http(s)://<host>/api`
- Primary auth: `Authorization: Token <token_id>:<token_secret>`
- Built-in self-hosted docs UI: `/api/docs`
- Machine-readable docs endpoint observed in official docs: `/api/docs.json`
- Repo capture note: the live `docs.json` endpoint returned `401 Unauthorized` during anonymous repo capture, so the committed normalized snapshot is derived from the official HTML docs page instead of a direct JSON export.

## Raw Spec Summary

- Format: repo-owned normalized JSON derived from the official BookStack docs HTML
- Group count: `16`
- Operation count: `77`
- Canonical source quality: official docs plus repo-owned normalized snapshot

## Auth, Request Format, And Listing Rules

- BookStack authenticates API calls with `Authorization: Token <token_id>:<token_secret>`.
- The official docs state that request bodies may be sent as `application/json`, `application/x-www-form-urlencoded`, or `multipart/form-data`.
- The official docs also state that form requests only work for `POST` requests in PHP request parsing; `PUT` and `DELETE` form submissions need an override such as `_method=PUT` or `_method=DELETE`.
- Listing endpoints return `data` plus `total` and support `count`, `offset`, `sort`, and `filter[<field>]` query parameters.

## Full Endpoint Group Inventory

### Docs

- `2` operations: display, json.

### Pages

- `10` operations: list, create, read, update, delete, export-html, export-pdf, export-plain-text, export-markdown, export-zip.

### Chapters

- `10` operations: list, create, read, update, delete, export-html, export-pdf, export-plain-text, export-markdown, export-zip.

### Books

- `10` operations: list, create, read, update, delete, export-html, export-pdf, export-plain-text, export-markdown, export-zip.

### Shelves

- `5` operations: list, create, read, update, delete.

### Attachments

- `5` operations: list, create, read, update, delete.

### Audit-Log

- `1` operations: list.

### Comments

- `5` operations: list, create, read, update, delete.

### Content-Permissions

- `2` operations: read, update.

### Image-Gallery

- `7` operations: list, create, read-data-for-url, read, read-data, update, delete.

### Imports

- `5` operations: list, create, read, run, delete.

### Recycle-Bin

- `3` operations: list, restore, destroy.

### Roles

- `5` operations: list, create, read, update, delete.

### Search

- `1` operations: all.

### System

- `1` operations: read.

### Users

- `5` operations: list, create, read, update, delete.

## Repo Utility Surface

`ghostship-bookstack` is intended to expose:
- one snake_case CLI command for every verified upstream BookStack operation in the committed snapshot
- one client method and one `build_...` dry-run builder for every verified operation
- generic repeated `--path-param` and `--query-param` options for the full REST surface
- multipart-aware form and file options for operations that require uploads
- explicit binary-output handling for exports and image-data endpoints while still emitting JSON metadata by default
- `request` as the escape hatch for temporary upstream drift or debugging

## Source Material

- Local raw docs capture: [bookstack-api-docs.html](./bookstack-api-docs.html)
- Local normalized snapshot: [bookstack-docs.json](./bookstack-docs.json)
- Official docs UI: <https://demo.bookstackapp.com/api/docs>
- Official docs export path listed by BookStack itself: `/api/docs.json`
