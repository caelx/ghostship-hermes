---
name: bitwarden
description: Use the Bitwarden Secrets Manager CLI `bws` in the Hermes image to fetch operator-shared service and automation-compatible website secrets with a machine-account access token and narrow per-command materialization.
---

# Bitwarden Skill

Use `bws` when you need project-scoped secrets from Bitwarden Secrets Manager.

## Prerequisites

- `BWS_ACCESS_TOKEN`
- Optional `BWS_SERVER_URL` for self-hosted Bitwarden
- `bws` uses its normal HOME-based config and state locations
- Hermes persists that HOME state through the `/opt/data/home` symlinked home tree

## Operating Model

- Treat `BWS_ACCESS_TOKEN` as the bootstrap secret injected by the operator.
- Prefer project and secret commands, not Password Manager vault workflows.
- Treat Bitwarden Secrets Manager as the default source of truth for service credentials and website credentials that fit a machine-account or scripted workflow.
- Keep service URLs, hostnames, ports, profile names, and paths in local env/config by default unless the value itself contains credential material.
- `bws` already defaults to JSON output.
- Discover the right project and secret ids first, then fetch only the values you need.
- Export or inject only the secret values needed for the command you are about to run.
- Do not use `bw`, `BW_SESSION`, vault unlock flows, shared collections, or TOTP/item retrieval patterns here.
- Do not treat interactive-only auth models such as passkeys, WebAuthn prompts, or human SSO sessions as normal `bws` workflows.

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
- Keep local topology in env/config:
  - Example: `set -x CHANGEDETECTION_URL https://changedetection.example.com`
- Export a service secret env var for a downstream CLI:
  - `set -x CHANGEDETECTION_API_KEY (bws secret get <secret-id> | jq -r '.value')`
- Use website credentials when they fit automation:
  - Store usernames, passwords, bearer tokens, app passwords, or cookie seeds in Bitwarden.
  - Fetch only the values needed for the browser or CLI workflow you are about to run.

## Guardrails

- Keep `BWS_ACCESS_TOKEN` out of committed files and image defaults.
- Avoid dumping broad secret lists once the target ids are known.
- Prefer per-command exports over leaving many secret values resident in the shell longer than needed.
