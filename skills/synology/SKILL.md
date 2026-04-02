---
name: synology
description: Operate Synology DSM File Station from the Hermes image with `ghostship-synology`. Use when inspecting shares, browsing or searching files, reading file metadata, uploading or downloading content, or performing guarded folder and file mutations through exact CLI operations.
---

# Synology Skill

Use `ghostship-synology` for File Station workflows that begin with share discovery and end with explicit path verification.

## Prerequisites

- `SYNOLOGY_URL`
- `SYNOLOGY_USER`
- `SYNOLOGY_PASS`
- `SYNOLOGY_VERIFY_SSL` when you need to override TLS verification behavior

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `call` only for uncovered API methods.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.
- Path safety matters more than speed: inspect the target share and exact path before any mutation.

## Start Here

- Service and auth sanity check: `ghostship-synology get_info`, then `ghostship-synology login`
- Discover available roots: `ghostship-synology list_shares`
- Inspect a target directory before write activity: `ghostship-synology list_files <path>`
- Inspect one object before rename, move, copy, or delete: `ghostship-synology get_file_info <path>`

## Common Workflows

- Browse and verify a target location:
  - `get_info`
  - `login`
  - `list_shares`
  - `list_files <path>` until you have the exact working path.
- Upload or download content:
  - `list_files <path>` or `get_file_info <path>` before transfer.
  - `upload_file --dry-run ...`, then `upload_file ...` for uploads.
  - `download_file <path> ...` only after confirming the exact source path.
  - Re-run `list_files <path>` or `get_file_info <path>` after upload to confirm the result.
- Reorganize files safely:
  - `get_file_info <path>` for the source object.
  - Inspect the destination with `list_files <target-dir>`.
  - `copy --dry-run ...` or `move --dry-run ...`, then the real command.
  - `rename --dry-run ...` or `delete --dry-run ...` only after confirming the full path.
  - Verify both source and destination state after the mutation.
- Search for a file before acting on it:
  - `search_start ...`
  - `search_list <task-id>` until the results stabilize.
  - `get_file_info <path>` on the selected result before any copy, move, or delete.

## Mutation Guardrails

- Never mutate a path you have not just confirmed with `list_files` or `get_file_info`.
- Use `--dry-run` for `create_folder`, `rename`, `delete`, `upload_file`, `copy`, and `move`.
- Prefer copy over move when the workflow allows recovery from mistakes.
- Verify post-state after every transfer or filesystem mutation.

## Fallback

- Use `ghostship-synology call` only when a dedicated command does not exist.
