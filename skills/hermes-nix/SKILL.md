---
name: hermes-nix
description: Use Nix inside the Hermes container to run missing tools, install durable user packages, build repo outputs, and choose the right path between one-off shells, persistent profiles, and image rebuilds without sudo.
---

# Hermes Nix Skill

Use this skill when a tool is missing, when a package should survive container restarts, or when repo outputs need to be built or run through the flake.

## Start Here

- Missing command for a one-off task: `command -v <tool>`, then `nix shell nixpkgs#<pkg> -c <tool> ...`
- Need the tool again later: `nix profile install nixpkgs#<pkg>`
- Need a repo-owned utility or image change: use the repo flake outputs with `nix build` or `nix run`
- Need durable behavior across deployments: update the repo and rebuild instead of patching the container by hand

## Operating Rules

- Prefer `nix shell nixpkgs#pkg -c cmd` for one-off use.
- Prefer `nix run nixpkgs#pkg -- args` for app-style invocations.
- Prefer `nix profile install nixpkgs#pkg` for packages that should survive restarts.
- Use repo outputs for repo-owned tools: `nix build .#...`, `nix run .#...`.
- Do not use `apt`, `dnf`, `apk`, or `sudo`.
- If a tool already exists in the image, use it directly instead of reinstalling it.

## Missing Tool Workflow

1. `command -v <tool>`
2. If absent, use `nix shell nixpkgs#<pkg> -c <tool> ...`
3. If the task will recur, `nix profile install nixpkgs#<pkg>`
4. If the tool is repo-owned, build or run the repo flake output instead
5. If package discovery is the blocker, `nix search nixpkgs <name>`

## Durable Install Workflow

- Install user-scoped packages that should survive restarts:
  - `nix profile install nixpkgs#ripgrep`
  - `nix profile install nixpkgs#ripgrep nixpkgs#jq nixpkgs#gh`
- Audit or clean up the user profile:
  - `nix profile list`
  - `nix profile upgrade --all`
  - `nix profile remove <name-or-index>`
- Use this path for convenience tools, not for repo changes that belong in the image.

## Repo Output Workflow

- Build a packaged utility:
  - `nix build .#packages.x86_64-linux.<name>`
- Run a repo app directly:
  - `nix run .#<app> -- <args>`
- Rebuild image-related outputs when the container behavior should change:
  - `nix build .#packages.x86_64-linux.ghostship-hermes-image`
- If the task changes the published environment, land it in the repo rather than relying on local profile installs.

## Common Examples

```bash
nix shell nixpkgs#ripgrep -c rg --version
nix shell nixpkgs#jq -c jq --version
nix shell nixpkgs#python3 -c python3 --version
nix shell nixpkgs#gh -c gh --version
nix profile install nixpkgs#ripgrep nixpkgs#jq nixpkgs#gh
nix build .#packages.x86_64-linux.ghostship-hermes-image
nix run .#ghostship-cloakbrowser -- list_profiles
```

## Container Notes

- `/nix` is the durable store for user-scoped Nix installs in the intended deployment model.
- `/home/hermes/.hermes` is for Hermes config, skills, and profile state.
- `/tmp` is ephemeral.
- Do not mount an empty Docker volume over `/nix` unless you intentionally preserve the image store behavior.
