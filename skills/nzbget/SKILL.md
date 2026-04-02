---
name: nzbget
description: Operate NZBGet from the Hermes image with `ghostship-nzbget`. Use when checking NZBGet status, queue, files, history, config, or logs, or when appending URLs, editing the queue, changing rate limits, or pausing and resuming subsystems through exact snake_case CLI operations.
---

# NZBGet Skill

Use `ghostship-nzbget` for queue-first download operations and controlled daemon actions.

## Prerequisites

- `NZBGET_URL`
- `NZBGET_USER`
- `NZBGET_PASS`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `call` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.

## Start Here

- Daemon health: `ghostship-nzbget get_status`, `ghostship-nzbget get_version`
- Queue state: `ghostship-nzbget list_groups`, `ghostship-nzbget list_files`
- Completed jobs: `ghostship-nzbget get_history`
- Troubleshooting: `ghostship-nzbget get_log`, `ghostship-nzbget get_config`

## Common Workflows

- Diagnose queue problems:
  - `get_status`
  - `list_groups`
  - `list_files`
  - `get_log`
- Add a new download:
  - Inspect current queue state first.
  - `append_url --dry-run ...`, then `append_url ...`
  - Re-read `list_groups` to verify enqueue.
- Edit queue behavior:
  - Confirm the target IDs in `list_groups` or `list_files`.
  - `edit_queue --dry-run ...`, then execute.
  - Re-read queue state afterward.
- Control subsystem pauses or rate:
  - Inspect `get_status` first.
  - `set_rate --dry-run ...`, `pause_download`, `resume_download`, `pause_post`, or related commands.
  - Re-read `get_status` to confirm the new daemon state.

## Mutation Guardrails

- Confirm group or file IDs before queue edits.
- Use `--dry-run` for queue mutations, rate changes, and config saves.
- Treat `shutdown` and `reload` as explicit operator actions after diagnosis, not default recovery steps.

## Fallback

- Use `ghostship-nzbget call` only for uncovered JSON-RPC methods.
