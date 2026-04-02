---
name: hermes-nix
description: Use Nix inside the Hermes container with flake-first workflows for repo tools, image builds, one-off commands, and persistent user installs without sudo.
---

# Hermes Nix Skill

Hermes runs in a container with no `sudo`, but `/nix` persists across restarts. Prefer flake-native Nix commands first: use repo outputs for repo-managed tools and images, use `nix shell` or `nix run` for one-off packages, and reserve `nix profile install` for tools that must persist for the current user across restarts.

## Core Rules

- Prefer repo flake outputs first: `nix run .#...`, `nix build .#...`, `nix develop`.
- Prefer `nix shell nixpkgs#pkg -c cmd` for one-off commands that are not already in the repo flake.
- Prefer `nix run nixpkgs#pkg -- args` for app-style packages from nixpkgs.
- Use `nix profile install` only for explicit persistent user installs.
- Never use `apt`, `dnf`, `apk`, or `sudo`.
- If a command exists in the container image, use it directly; otherwise install or run it with Nix.
- Use `/nix` as the durable store for user-scoped packages. Runtime changes elsewhere are not durable unless they live in `/home/hermes/.hermes`.

## Flake-First Workflow

1. Check `command -v`.
2. If the tool or image is repo-managed, use a repo flake output first.
3. If the tool is missing but available in nixpkgs, use `nix shell` or `nix run`.
4. If you need it every session, install it with `nix profile install`.
5. If you are changing a repo-managed package, rebuild the relevant flake output instead of patching the running container by hand.
6. If still missing, inspect `nix search nixpkgs <name>`.

## Repo Output Workflow

Use this when the tool, skills tree, or image belongs to this repo.

- Enter the repo dev shell:
  - `nix develop`
- Run a repo-managed tool that is not already installed in the image:
  - `nix run .#ghostship-cloakbrowser -- list_profiles`
- Build a repo-managed package:
  - `nix build .#packages.x86_64-linux.ghostship-hermes-runtime`
  - `nix build .#packages.x86_64-linux.ghostship-hermes-skills`
  - `nix build .#packages.x86_64-linux.ghostship-hermes-image`

If a tool is already bundled in the image, use it directly. For example, use `gws --help` inside the Hermes container instead of `nix run .#gws`.

If the change affects the published container, rebuild the image output. Do not treat `nix profile install .#...` as the default for repo development.

## User Install Workflow

Use this only when a package should be available every time Hermes starts for the current user, but it does not need to be baked into the image.

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

Use this when the tool is missing and it is not already available as a repo flake output.

- `nix shell nixpkgs#ripgrep -c rg "pattern" .`
- `nix shell nixpkgs#jq -c jq '.profiles' /run/ghostship-hermes/www/api/profiles.json`
- `nix shell nixpkgs#python3 -c python3 script.py`
- `nix run nixpkgs#gh -- auth status`

This avoids mutating the container image and avoids asking for root.

## Repo-Owned Utility Workflow

- Edit the package source.
- Test with the repo’s utility workflow or targeted package command.
- Build with `nix build .#packages.<arch>.<name>` or run with `nix run .#<app>`.
- Keep repo changes flake-first. Only use `nix profile install .#<package>` when you intentionally want a persistent user install outside the normal build workflow.
- If the change affects the published container, update `packages/hermes-image/` and rebuild the image instead of trying to patch the running container by hand.

## Common Examples

```bash
nix develop
nix build .#packages.x86_64-linux.ghostship-hermes-skills
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

- If you need the bundled Google Workspace CLI:
  - `gws gmail users getProfile --params '{"userId":"me"}'`
- If you need the repo development environment:
  - `nix develop`
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
