---
name: cloakbrowser
description: Operate CloakBrowser Manager from the Hermes image with `ghostship-cloakbrowser`. Use when inspecting profile health, authenticating to the manager, creating or updating browser profiles, launching or stopping sessions, managing clipboard state, or retrieving CDP connection details for browser automation.
---

# CloakBrowser Skill

Use `ghostship-cloakbrowser` when you need to manage CloakBrowser profiles and hand browser sessions off to automation tools.

## Prerequisites

- `CLOAKBROWSER_URL`
- `CLOAKBROWSER_TOKEN` when the manager requires bearer-token auth

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.
- `get_system_status` is unauthenticated health; manager auth uses bearer-token workflows.

## Start Here

- Basic health: `ghostship-cloakbrowser get_system_status`
- Auth check: `ghostship-cloakbrowser auth_status`
- Inventory existing profiles: `ghostship-cloakbrowser list_profiles`
- Inspect one profile before launch or mutation: `ghostship-cloakbrowser get_profile <profile-id>`

## Common Workflows

- Prepare a profile for automation:
  - `list_profiles`
  - `get_profile <profile-id>` to confirm the target profile and settings.
  - `launch_profile <profile-id>` after confirming the profile is the one you want.
  - `get_profile_status <profile-id>` and `get_cdp_info <profile-id>` to verify the launched browser and capture CDP details.
- Create or revise a reusable profile:
  - `list_profiles` to avoid duplicates.
  - `create_profile --dry-run ...`, then `create_profile ...` for new profiles.
  - `update_profile --dry-run ...`, then `update_profile ...` for existing ones.
  - `get_profile <profile-id>` to confirm the persisted profile shape.
- Manage in-browser state:
  - `get_clipboard <profile-id>` to inspect current clipboard content.
  - `set_clipboard --dry-run ...`, then `set_clipboard ...` only after confirming the right active profile.
  - Re-read `get_clipboard <profile-id>` or `get_profile_status <profile-id>` after the change.
- Stop a session cleanly:
  - `get_profile_status <profile-id>`
  - `stop_profile --dry-run <profile-id>`, then `stop_profile <profile-id>`
  - `get_profile_status <profile-id>` to verify the session is really down.

## Mutation Guardrails

- Confirm the exact profile ID before any launch, stop, update, or delete operation.
- Use `--dry-run` for `create_profile`, `update_profile`, `delete_profile`, `launch_profile`, `stop_profile`, and `set_clipboard`.
- Treat CDP details as sensitive session data; fetch them only for the profile you intend to automate.
- Re-check profile status after any lifecycle mutation.

## Fallback

- Use `ghostship-cloakbrowser request` only when a dedicated command does not exist.
