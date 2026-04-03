---
name: bitwarden
description: Use the official Bitwarden CLI `bw` in the Hermes image to receive operator-shared credentials through a dedicated Bitwarden account, with env-driven login, unlock, sync, and retrieval workflows.
---

# Bitwarden Skill

Use `bw` when you need to authenticate to Bitwarden, sync shared collections, and retrieve passwords, notes, TOTP codes, or full items noninteractively.

## Required Environment

- `BW_CLIENTID`
- `BW_CLIENTSECRET`
- `BW_PASSWORD`
- `BITWARDENCLI_APPDATA_DIR`
- `BW_SESSION`

The image defaults `BITWARDENCLI_APPDATA_DIR` to `/home/hermes/.hermes/bitwarden-cli`. Keep secret values out of the image and inject them per container or per shell.

## Start Here

- Check current state first: `bw status --response`
- If the account uses a self-hosted Bitwarden server, configure it once before login: `bw config server https://vault.example.com`
- Log in with the API key, not an interactive email/password prompt.
- Unlock with `BW_PASSWORD` and export a fresh `BW_SESSION`.
- Run `bw sync` before reading newly shared credentials.

## Noninteractive Login Flow

```fish
set -x BW_CLIENTID <client-id>
set -x BW_CLIENTSECRET <client-secret>
set -x BW_PASSWORD <master-password>
set -x BITWARDENCLI_APPDATA_DIR /home/hermes/.hermes/bitwarden-cli

bw login --apikey --nointeraction
set -x BW_SESSION (bw unlock --passwordenv BW_PASSWORD --raw --nointeraction)
bw sync --session "$BW_SESSION" --response
```

`BW_SESSION` is ephemeral. Regenerate it with `bw unlock --passwordenv BW_PASSWORD --raw --nointeraction` whenever a shell loses its session.

## Shared Secret Workflow

- Use a dedicated Bitwarden account for the agent.
- Share credentials to that account through Bitwarden shared collections or the equivalent supported organization-sharing flow.
- Sync before reading newly shared items: `bw sync --session "$BW_SESSION" --response`
- Discover available shared collections: `bw list collections --response --session "$BW_SESSION"`
- Filter items by collection when you know the target scope: `bw list items --collectionid <collection-id> --response --session "$BW_SESSION"`

## Retrieval Patterns

- Full item JSON: `bw get item <item-id-or-search-term> --response --session "$BW_SESSION"`
- Password only: `bw get password <item-id-or-uri> --raw --session "$BW_SESSION"`
- Notes only: `bw get notes <item-id-or-uri> --raw --session "$BW_SESSION"`
- TOTP only: `bw get totp <item-id-or-uri> --raw --session "$BW_SESSION"`
- Search before reading when the item id is unknown: `bw list items --search <term> --response --session "$BW_SESSION"`

Prefer `--response` for structured output and `--raw` only when a downstream command needs the bare secret value.

## Guardrails

- Prefer `--nointeraction` so the agent fails fast instead of hanging on prompts.
- Do not write Bitwarden credentials into repo files, image defaults, or committed `.env` files.
- Lock the vault and clear the session when you are done:

```fish
bw lock
set -e BW_SESSION
```
