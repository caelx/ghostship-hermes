---
name: changedetection
description: Manage changedetection.io with `ghostship-changedetection`. Use when you need full API coverage for watches, tags, notifications, search/import, history, or the live merged instance spec, and when service credentials are stored in Bitwarden Secrets Manager.
---

# changedetection Skill

Use `ghostship-changedetection` for the full stable changedetection.io API surface.

## Prerequisites

- `BWS_ACCESS_TOKEN`
- Bitwarden secrets for `CHANGEDETECTION_URL` and `CHANGEDETECTION_API_KEY`
- `ghostship-changedetection` reads `CHANGEDETECTION_URL` and `CHANGEDETECTION_API_KEY`

## Operating Model

- Fetch changedetection credentials from `bws` first.
- Prefer dedicated snake_case commands before `request`.
- Follow the normal flow: inspect, `--dry-run`, mutate, verify.
- `get_full_api_spec` returns the live merged YAML for the running instance. The repo’s stable upstream snapshot lives in `docs/api/changedetection-openapi.json`.

## Start Here

```fish
set -x CHANGEDETECTION_URL (bws secret get <changedetection-url-secret-id> | jq -r '.value')
set -x CHANGEDETECTION_API_KEY (bws secret get <changedetection-api-key-secret-id> | jq -r '.value')

ghostship-changedetection get_system_info --pretty
ghostship-changedetection list_watches --pretty
```

## Common Workflows

- Inspect watches, tags, and notifications:
  - `list_watches`, `get_watch`, `list_tags`, `get_tag`, `get_notifications`
- Search or import:
  - `search_watches --query <text>`
  - `import_watches <url>... --tag <name> --dry-run --pretty`
- Work history or debug rendering:
  - `get_watch_history`, `get_watch_snapshot`, `get_watch_history_diff`, `get_watch_favicon`
- Mutate safely:
  - Run `create_*`, `update_*`, `delete_*`, or notification write commands with `--dry-run` first.
  - Re-run without `--dry-run` only after the rendered request looks correct.
  - Verify with a matching `get_*` or list command.

## Mutation Guardrails

- Keep `--body-json` payloads aligned with the upstream schema or a fresh `get_watch` or `get_tag` response.
- Use `request` only for future or deployment-specific parameters the typed command does not expose yet.
- Treat `get_full_api_spec` as instance-specific introspection; do not replace the repo’s stable spec snapshot with it.
