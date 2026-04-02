---
name: flaresolverr
description: Operate FlareSolverr from the Hermes image with `ghostship-flaresolverr`. Use when checking solver health, making one-shot Cloudflare-bypassing requests, creating or destroying browser-backed sessions, or comparing session-based versus stateless retrieval flows.
---

# FlareSolverr Skill

Use `ghostship-flaresolverr` when direct HTTP access is blocked and you need browser-assisted request handling.

## Prerequisites

- `FLARESOLVERR_URL`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `command` only when you need an API action that has no direct wrapper.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Session lifecycle mutations support `--dry-run`.
- Choose one-shot requests for isolated fetches and named sessions for repeated access to the same protected site.

## Start Here

- Quick one-off retrieval: `ghostship-flaresolverr request_get <url>`
- Session inventory: `ghostship-flaresolverr sessions_list`
- Session bootstrap for repeated work: `ghostship-flaresolverr sessions_create <name>`

## Common Workflows

- Fetch a single protected page:
  - `request_get <url>` for simple reads.
  - `request_post <url> ...` when the target requires form or API submission.
  - Re-run the request only after inspecting the first result for challenge failures or missing cookies.
- Run repeated requests against one site:
  - `sessions_list`
  - `sessions_create --dry-run <name>`, then `sessions_create <name>`
  - `request_get <url> --session <name>` or `request_post <url> --session <name> ...`
  - `sessions_destroy --dry-run <name>`, then `sessions_destroy <name>` when the session is no longer needed.
- Diagnose a failing protected fetch:
  - Compare `request_get <url>` without a session against the same URL with a named session.
  - `sessions_list` to confirm the expected session exists.
  - Use `command` only if you need a raw API call not covered by the dedicated request or session commands.

## Mutation Guardrails

- Use `--dry-run` for `sessions_create` and `sessions_destroy`.
- Reuse sessions intentionally; avoid creating throwaway sessions for every request unless isolation matters.
- Destroy only the named session you inspected first.
- Verify post-state with `sessions_list` after session lifecycle changes.

## Fallback

- Use `ghostship-flaresolverr command` only when a dedicated command does not exist.
