---
name: bitwarden
description: Use the Bitwarden Secrets Manager CLI `bws` in the Hermes image to fetch operator-shared service secrets with a machine-account access token, repo-managed config path, and project or secret workflows.
---

# Bitwarden Skill

Use `bws` when you need project-scoped secrets from Bitwarden Secrets Manager.

## Prerequisites

- `BWS_ACCESS_TOKEN`
- Optional `BWS_SERVER_URL` for self-hosted Bitwarden
- `BWS_CONFIG_FILE` defaults to `/home/hermes/.hermes/bws/config`
- Hermes persists `bws` state under `/home/hermes/.hermes/bws/state`

## Operating Model

- Prefer project and secret commands, not Password Manager vault workflows.
- `bws` already defaults to JSON output.
- Discover the right project and secret ids first, then fetch only the values you need.
- Do not use `bw`, `BW_SESSION`, vault unlock flows, shared collections, or TOTP/item retrieval patterns here.

## Start Here

```fish
set -x BWS_ACCESS_TOKEN <machine-account-access-token>

bws project list
bws secret list <project-id>
bws secret get <secret-id>
```

If you use a self-hosted Bitwarden server, set the base URL before the first request:

```fish
set -x BWS_SERVER_URL https://vault.example.com
```

## Common Workflows

- Discover a project:
  - Run `bws project list`.
  - Pick the project that owns the service secrets you need.
- Discover secret ids:
  - Run `bws secret list <project-id>`.
  - Read the JSON and identify the secret ids you actually need before fetching values.
- Read a secret value:
  - Run `bws secret get <secret-id>`.
  - Extract the `value` field only when a downstream command needs the raw secret.
- Export a service env var for a downstream CLI:
  - `set -x CHANGEDETECTION_API_KEY (bws secret get <secret-id> | jq -r '.value')`

## Guardrails

- Keep `BWS_ACCESS_TOKEN` out of committed files and image defaults.
- Avoid dumping broad secret lists once the target ids are known.
- Prefer per-command exports over leaving many secret values resident in the shell longer than needed.
