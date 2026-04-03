---
name: current-environment
description: Understand how Hermes runs in this container, what persists, what resets, and which recovery path is safe before changing runtime behavior, files, terminals, or browser-exposed profile sessions.
---

# Current Environment

Use this skill when you need to reason about what is durable in the Hermes workstation container and which recovery path is safe.

## Start Here

- Need to know whether a file or install survives restart: check the persistence model first.
- Need to recover a dead terminal or Hermes session: use the profile-terminal recovery flow, not a container restart.
- Need to change runtime behavior durably: prefer repo or persistent-profile changes over interactive tweaks.

## Persistence Model

- Persistent:
  - `/opt/data`
  - `/opt/data/home` via symlinks from `/home/hermes`
  - `/workspace`
  - `/nix` in the intended deployment model for user-installed Nix software
- Ephemeral:
  - `/tmp`
  - live processes
  - `ttyd` sessions
  - interactive runtime-only changes outside `/opt/data`, `/workspace`, and `/nix`
- If something should survive restart, put it under `/opt/data`, under the symlinked home facade that resolves into `/opt/data/home`, under `/workspace`, persist `/nix` for Nix-managed installs, or bake it into the image.

## Runtime Boundaries

- Hermes runs as a non-root user.
- `sudo` is not available.
- Host filesystem access only exists for mounted paths.
- Container-level ad hoc edits are not durable unless encoded in the repo or persistent storage.
- Browser automation is expected to use CloakBrowser-backed profiles when CDP details are needed.

## Profile Terminal Recovery

- Treat `/profiles/<slug>/` routes as browser access to `ttyd`, not as proof that Hermes itself is healthy.
- If a foreground Hermes command exits, reconnecting to the iframe may only give you a plain shell.
- Recover a broken profile session by restarting the Hermes command in that profile terminal.
- Prefer restarting the profile-specific foreground process over touching Caddy or the whole container.
- Restart the container only for container-level failures, not ordinary session recovery.

## Durable Change Workflow

- For Hermes config, skills, and default-profile state: work under `HERMES_HOME`, which is `/opt/data`.
- For persistent HOME-anchored agent config, shared prompts, OpenSpec skills, Codex/Gemini/Opencode state, named profiles, wrappers, and user systemd units: work under `/home/hermes`, which resolves into `/opt/data/home`.
- For repos, builds, downloads, and long-lived work products: work under `/workspace` or `/home/hermes/workspace`.
- For user-installed software with Nix: persist `/nix` and use `nix profile`, `nix shell`, or `nix run` from the workstation home.
- For service layout, default seeded tooling, or bootstrap/update logic: change the repo and rebuild the image.
- Do not rely on live process tweaks to persist.

## Service Model

- The workstation boots a `hermes` user `systemd` manager after a short root-owned setup phase.
- Caddy is the only public HTTP surface.
- Profile `ttyd` terminals are generated dynamically from Hermes profile state.
- Gateway persistence should prefer Hermes' own `gateway install` user-service flow instead of a repo-specific watcher.
- Direct `ttyd` loopback backends are implementation details; the Caddy routes are the intended interface.

## Identity And Permissions

- Runtime UID and GID are configurable.
- Do not assume `1000:1000`.
- Use the configured runtime identity when reasoning about ownership problems.
