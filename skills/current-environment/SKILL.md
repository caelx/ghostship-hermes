---
name: current-environment
description: Describe how Hermes runs in this container, what persists, what resets, and how to recover safely.
---

# Current Environment

Hermes runs in a container behind a Caddy dashboard that proxies profile-specific `ttyd` terminals. `s6` supervises the web and background processes. Treat the runtime as non-root, ephemeral outside mounted volumes, and recoverable without restarting the container.

## What You Can Access

- Hermes state in `/home/hermes/.hermes`
- Persistent Nix state and profiles in `/nix` in the intended deployment model
- Bundled tools from the image
- The browser dashboard on port `7681`
- The profile terminals exposed through same-origin iframe routes like `/profiles/default/`
- The Hermes CLI and gateway inside the container
- Browser automation through CloakBrowser-backed profiles when a CDP endpoint is available

## What You Cannot Assume

- `sudo` is not available
- Host filesystem access is not available unless mounted
- Host-level package managers are not available
- Container-level runtime edits are not durable unless baked into the repo/image
- `tmux` sessions do not survive container restarts
- `s6` service tweaks made interactively do not survive restarts unless encoded in the image
- Direct access to the per-profile `ttyd` backends is not the public contract; they are meant to stay behind the Caddy proxy

## Persistence

- Persists: `/home/hermes/.hermes`, `/nix`
- Ephemeral: `/tmp`, live processes, `ttyd` sessions, `tmux` sessions, interactive `s6` changes
- If a tool install should survive restarts, use Nix user installs or update the image
- Do not mount an empty Docker volume over `/nix` on a fresh image unless you know how that deployment preserves the Nix store. Replacing `/nix` blindly can hide or trigger a copy of the image store.

## `ttyd` Nuances

- `ttyd` is the terminal transport behind each profile iframe; it is not the process manager.
- Caddy serves the main dashboard and proxies `/profiles/<slug>/` to loopback-only `ttyd` processes.
- Reconnecting to `ttyd` is not the same as resuming a killed process.
- If the foreground command exits, the browser can land on a dead session or a plain shell.
- If Hermes is unconfigured, the browser terminal should fall back to a shell.
- A visible iframe is not proof that the profile process is healthy; verify behavior in the terminal itself.

## Safe Self-Restart

- Save work first.
- Stop the foreground Hermes command cleanly.
- Start a new `hermes chat` session in the same terminal, or reopen the profile route in the dashboard.
- Do not restart the container for ordinary config or session recovery.
- Do not rely on `tmux` or `s6` tweaks to persist.
- If a profile-specific terminal is unhealthy, prefer restarting the Hermes command in that terminal over touching Caddy or the whole container.

## Runtime Identity

- The runtime UID/GID is configurable.
- Do not assume `1000:1000`.
- The container may run as your default app user, likely `3000:3000`.
- Use the configured UID/GID when reasoning about file ownership and permissions.

## Service Model

- `s6` is the supervisor for the dashboard and profile watchers.
- Caddy is the only public HTTP service.
- Profile `ttyd` services and profile gateway services are generated dynamically from Hermes profile state.
- Runtime `s6` changes and running `tmux` sessions are transient; make durable changes in the repo or in persistent profile files.
