---
name: hermes-nix
description: Use Nix inside the Hermes container to run missing tools, install user packages, and update repo utilities without sudo.
---

# Hermes Nix Skill

Hermes runs in a container with no `sudo`, but `/nix` persists across restarts. Use Nix first when a command is missing, when a package should survive restarts, or when you need to update repo-owned tooling without rebuilding the whole container immediately.

## Core Rules

- Prefer `nix shell nixpkgs#pkg -c cmd` for one-off commands.
- Prefer `nix run nixpkgs#pkg -- args` for app-style packages.
- Use `nix profile install nixpkgs#pkg` for user installs that should survive restarts.
- Use repo flake outputs for repo-owned tools: `nix build .#...`, `nix run .#...`.
- Never use `apt`, `dnf`, `apk`, or `sudo`.
- If a command exists in the container image, use it directly; otherwise install or run it with Nix.
- Use `/nix` as the durable store for user-scoped packages. Runtime changes elsewhere are not durable unless they live in `/home/hermes/.hermes`.

## Missing Tool Workflow

1. Check `command -v`.
2. If absent and it is in nixpkgs, use `nix shell`.
3. If you need it repeatedly, install with `nix profile install`.
4. If the tool is repo-owned, rebuild the package or image.
5. If still missing, inspect `nix search nixpkgs <name>`.

## User Install Workflow

Use this when you need a package available every time Hermes starts, but it does not need to be baked into the image.

- Install a package for the current user:
  - `nix profile install nixpkgs#ripgrep`
- Install several packages at once:
  - `nix profile install nixpkgs#ripgrep nixpkgs#jq nixpkgs#python3 nixpkgs#gh nixpkgs#tmux`
- Show what is installed:
  - `nix profile list`
- Upgrade installed packages:
  - `nix profile upgrade --all`
- Remove a package:
  - `nix profile remove <name-or-index>`
- User profile installs persist because `/nix` persists.

## One-Off Tool Workflow

Use this when the tool is missing but you only need it for the current task.

- `nix shell nixpkgs#ripgrep -c rg "pattern" .`
- `nix shell nixpkgs#jq -c jq '.profiles' /run/ghostship-hermes/www/api/profiles.json`
- `nix shell nixpkgs#python3 -c python3 script.py`
- `nix run nixpkgs#gh -- auth status`

This avoids mutating the container image and avoids asking for root.

## Repo-Owned Utility Workflow

- Edit the package source.
- Test with the repo’s utility workflow.
- Build with `nix build .#packages.<arch>.<name>` or `nix run .#<app>`.
- If the tool should be persistent for Hermes, install it with `nix profile install .#<package>` or update the image bundle.
- If the change affects the published container, update `packages/hermes-image/` and rebuild the image instead of trying to patch the running container by hand.

## Common Examples

```bash
nix shell nixpkgs#ripgrep -c rg --version
nix shell nixpkgs#jq -c jq --version
nix shell nixpkgs#python3 -c python3 --version
nix shell nixpkgs#gh -c gh --version
nix shell nixpkgs#tmux -c tmux -V
nix profile install nixpkgs#ripgrep nixpkgs#jq nixpkgs#python3 nixpkgs#gh nixpkgs#tmux
nix build .#packages.x86_64-linux.ghostship-hermes-image
nix run .#ghostship-cloakbrowser -- list_profiles
```

## Common Agent Scenarios

- If `rg` is missing:
  - `nix shell nixpkgs#ripgrep -c rg "search-term" .`
- If `jq` is missing:
  - `nix shell nixpkgs#jq -c jq '.profiles' /run/ghostship-hermes/www/api/profiles.json`
- If `python` is missing:
  - `nix shell nixpkgs#python3 -c python3 --version`
- If `gh` is missing:
  - `nix shell nixpkgs#gh -c gh auth status`
- If `tmux` is missing:
  - `nix shell nixpkgs#tmux -c tmux -V`
- If a tool is useful long-term:
  - `nix profile install nixpkgs#<package>`

## Container Notes

- `/nix` is persistent in the intended deployment model; user installs and profile packages are durable there.
- `/home/hermes/.hermes` is also persistent; use it for Hermes config, skills, and profile state.
- `/tmp` is ephemeral.
- Do not assume root access or system package managers.
- Do not assume an empty Docker volume can safely replace `/nix`; that can hide or copy the image’s Nix store.
