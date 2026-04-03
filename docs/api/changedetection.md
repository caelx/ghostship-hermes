# changedetection.io API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [changedetection-openapi.json](./changedetection-openapi.json)
- Companion reference: this file

## Service Identity

- Product: changedetection.io
- Version mirrored in repo: `0.1.6`
- Base API URL: `http(s)://<host>/api/v1`
- Primary auth: `x-api-key`
- Unauthenticated endpoint: `GET /full-spec`

## Raw Spec Summary

- Format: OpenAPI JSON converted from the upstream `docs/api-spec.yaml`
- Path count: `14`
- Operation count: `22`
- Schema count: `12`
- Canonical source quality: official OpenAPI plus repo summary

## Full Endpoint and Use-Case Inventory

The inventory below is taken directly from the mirrored upstream machine-readable specification.

### Watch Management

- `GET /watch`: list all watches, with optional `recheck_all=1` and `tag=<name>`
- `POST /watch`: create a watch from the `CreateWatch` schema; returns plain-text `OK`
- `GET /watch/{uuid}`: fetch the full watch JSON and optionally set `recheck`, `paused`, or `muted`
- `PUT /watch/{uuid}`: update a watch from the `UpdateWatch` schema; returns plain-text `OK`
- `DELETE /watch/{uuid}`: delete a watch and its history; returns plain-text `OK`
- `GET /watch/{uuid}/history`: list watch history snapshots
- `GET /watch/{uuid}/history/{timestamp}`: fetch a single snapshot; returns text or HTML when `html=1`
- `GET /watch/{uuid}/difference/{from_timestamp}/{to_timestamp}`: diff two snapshots; supports `format`, `word_diff`, `no_markup`, `type`, `changesOnly`, `ignoreWhitespace`, `removed`, `added`, and `replaced`
- `GET /watch/{uuid}/favicon`: fetch the current favicon; returns image bytes

### Tag Management

- `GET /tags`: list tags
- `POST /tag`: create a tag from the `CreateTag` schema
- `GET /tag/{uuid}`: fetch a tag and optionally set `muted` or `recheck`
- `PUT /tag/{uuid}`: update a tag from the `Tag` schema
- `DELETE /tag/{uuid}`: delete a tag

### Notifications

- `GET /notifications`: read the configured notification URLs
- `POST /notifications`: append notification URLs from the `NotificationUrls` schema
- `PUT /notifications`: replace all notification URLs
- `DELETE /notifications`: delete one or more notification URLs

### Search, Import, System, and Spec

- `GET /search`: search watches by `q`, with optional `tag` and `partial`
- `POST /import`: import line-separated URLs as `text/plain`, with shared watch configuration supplied through query parameters
- `GET /systeminfo`: read system and queue information
- `GET /full-spec`: fetch the live merged YAML spec for the running instance, including plugin-contributed processor schemas

## Repo Utility Surface

`ghostship-changedetection` exposes:
- dedicated snake_case commands for every stable upstream operation in the static spec
- `request` as the escape hatch for future or deployment-specific parameters
- JSON-wrapped text, YAML, and binary responses so the CLI still emits native JSON by default
- `--dry-run` request rendering for every write or delete command

The repo persists the stable upstream contract in [changedetection-openapi.json](./changedetection-openapi.json). The runtime `get_full_api_spec` command remains available for instance-specific merged schemas without replacing the stable repo snapshot.

## Source Material

- Local mirrored raw spec: [changedetection-openapi.json](./changedetection-openapi.json)
- Upstream repository: <https://github.com/dgtlmoon/changedetection.io>
- Upstream static source-of-truth path: `docs/api-spec.yaml`
