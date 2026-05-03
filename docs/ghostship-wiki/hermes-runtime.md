# Hermes Runtime

## Managed Defaults

Hermes is configured as a local workstation container:

- Dashboard web surface: `0.0.0.0:7681`.
- Internal upstream dashboard listener: localhost.
- Terminal: same-origin `/terminal/`, backed by `ttyd` and `tmux`.
- Browser provider: local.
- Web backend: `firecrawl`.
- Memory provider: holographic memory store.
- Agent defaults: `max_turns: 500`, `reasoning_effort: xhigh`.
- Sessions do not reset automatically; the managed config omits `session_reset`.

## Config Files

- Main config: `/home/hermes/.hermes/config.yaml`.
- Runtime env: `/home/hermes/.hermes/.env`.
- Skills: `/home/hermes/.hermes/skills`.
- Transcripts/session state: under `/home/hermes/.hermes`.

The image boot code converges managed defaults without removing unrelated user
config. If behavior looks wrong, inspect `config.yaml` first, then the container
logs for the relevant s6 service.

## Gateway Notes

Discord routing uses runtime env such as `DISCORD_HOME_CHANNEL`,
`DISCORD_WEBHOOK_CHANNEL`, and `GHOSTSHIP_CODEX_CHANNEL`. Do not commit concrete
Discord snowflake IDs into the repo.
