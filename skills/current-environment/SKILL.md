---
name: current-environment
description: Understand how Hermes runs in this container, what persists, what resets, and which recovery path is safe before changing runtime behavior, files, terminals, or browser-exposed profile sessions.
---

# Current Environment

Use this skill when you need to reason about what is durable in the Hermes container and which recovery path is safe.

## Start Here

- Need to know whether a file or install survives restart: check the persistence model first.
- Need to recover a dead terminal or Hermes session: use the profile-terminal recovery flow, not a container restart.
- Need to change runtime behavior durably: prefer repo or persistent-profile changes over interactive tweaks.

## Persistence Model

- Persistent:
  - `/home/hermes/.hermes`
  - `/nix` in the intended deployment model
- Ephemeral:
  - `/tmp`
  - live processes
  - `ttyd` sessions
  - `tmux` sessions
  - interactive `s6` changes
- If something should survive restart, put it in persistent profile state, install it via Nix, or bake it into the image.

## Runtime Boundaries

- Hermes runs as a non-root user.
- `sudo` is not available.
- Host filesystem access only exists for mounted paths.
- Container-level ad hoc edits are not durable unless encoded in the repo or persistent storage.
- Browser automation is expected to use CloakBrowser-backed profiles when CDP details are needed.

## Profile Terminal Recovery

- Treat `/profiles/<slug>/` routes as browser access to `ttyd`, not as proof that Hermes itself is healthy.
- If a foreground Hermes command exits, reconnecting to the iframe may only give you a dead session or a plain shell.
- Recover a broken profile session by restarting the Hermes command in that profile terminal.
- Prefer restarting the profile-specific foreground process over touching Caddy or the whole container.
- Restart the container only for container-level failures, not ordinary session recovery.

## Durable Change Workflow

- For Hermes config, skills, and profile state: work under `/home/hermes/.hermes`.
- For missing tools or persistent user installs: use Nix under `/nix`.
- For service layout, supervisor behavior, or default bundled tooling: change the repo and rebuild the image.
- Do not rely on interactive `s6` or `tmux` tweaks to persist.

## Service Model

- `s6` supervises the dashboard and profile watcher services.
- Caddy is the only public HTTP surface.
- Profile `ttyd` terminals and gateway services are generated dynamically from Hermes profile state.
- Direct `ttyd` loopback backends are implementation details; the Caddy routes are the intended interface.

## Identity And Permissions

- Runtime UID and GID are configurable.
- Do not assume `1000:1000`.
- Use the configured runtime identity when reasoning about ownership problems.
