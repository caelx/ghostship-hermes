# Utilities

## Default Commands

The image-managed default utility set includes:

- `bw`: Bitwarden Password Manager CLI.
- `gh`: GitHub CLI.
- `gcloud`: Google Cloud CLI.
- `gws`: Google Workspace CLI.
- `blogwatcher-cli`: RSS/feed monitoring.
- `agent-browser`: local browser automation CLI.
- `codex`, `gemini`, `opencode`: userland model/agent CLIs installed through npm.
- `rg`, `fd`, `jq`, `yq`, `git`, `tmux`, `ttyd`, `uv`.

## Bitwarden

Bitwarden CLI state is stored under:

`/home/hermes/.local/state/bitwarden-cli`

The image exports `BITWARDENCLI_APPDATA_DIR` so raw `bw` commands use the managed
state path. Higher-level Bitwarden workflows are agent-authored. Use `BW_CLIENTID`,
`BW_CLIENTSECRET`, and `BW_PASSWORD` from `.env` when present, but never print
their values.

## Google Workspace And Google Cloud

Generated Google Workspace skills use `gws` when available and fall back to the
Hermes Python wrapper. Common locations:

- Hermes legacy token: `/home/hermes/.hermes/google_token.json`
- `gws` config: `/home/hermes/.config/gws`
- `gcloud` config: `/home/hermes/.config/gcloud`

For `gws`, generated API paths are explicit, for example:

```bash
gws gmail users messages list --params '{"userId":"me","maxResults":10}' --format json
```

For `gcloud`, prefer non-interactive commands and JSON output:

```bash
gcloud projects list --format=json
gcloud config get-value project
```
