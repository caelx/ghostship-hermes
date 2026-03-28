# ghostship-hermes

`ghostship-hermes` is a Nix-first monorepo for building and publishing an arm64 OCI image that runs Hermes behind `ttyd`, ships a curated operator tool bundle, seeds repo-managed default skills, and hosts small API-wrapper utilities under the `ghostship-` prefix.

The current implementation deliberately separates:

- the base image and operator tooling, which come from stable nixpkgs
- Hermes itself, which is installed at container runtime from a pinned upstream release using the documented `uv` plus `npm` flow
- repo-managed utilities, which live in this repo and are packaged independently

For the standardized Python utility workflow, see [docs/python-utilities.md](/home/nixos/dev/personal/nixos-hermes/docs/python-utilities.md).

## Current Status

The repository is in initial bootstrap.

Implemented today:

- flake-based repository structure pinned to `nixos-25.11`
- a non-root Hermes runtime wrapper
- Hermes bootstrap logic based on the official upstream installation flow
- `ttyd` plus `tmux` entrypoint wiring
- the first Python utility scaffold: `ghostship-searxng`
- default skill seeding into the Hermes runtime skill directory
- CI, arm64 publish workflow, and Hermes release updater scaffolding
- standard open source repository files and templates

Not yet fully proven in this session:

- a full end-to-end arm64 image build on an arm64 runner
- first container boot against the live upstream Hermes release
- GHCR publish run

Those are the next practical verification steps once the repository is pushed to GitHub.

## What This Image Does

- exposes Hermes through `ttyd` on port `7681`
- starts as root only long enough to initialize mounted volumes, then drops to the non-root `hermes` user
- persists Hermes state in `/home/hermes/.hermes`
- persists Nix state in `/nix`
- installs Hermes from a pinned upstream release on first start using the documented `uv` plus `npm` flow
- seeds repo-managed default skills into `~/.hermes/skills`
- makes `agent-browser` available through the Hermes-managed `node_modules/.bin` path after bootstrap

## Architecture

### Image Model

The image is package-built rather than NixOS-module-driven.

Why:

- the current goal is a focused application container, not a full service-heavy NixOS system image
- the base tool bundle fits naturally in a `dockerTools.buildLayeredImage` output
- Hermes is not present on the inspected stable nixpkgs branch, so packaging it as part of the image bootstrap is simpler than forcing a different nixpkgs policy

### Hermes Installation Model

Hermes is installed at runtime, not baked into the image as a stable nixpkgs package.

On first start, the runtime wrapper:

1. creates the expected `~/.hermes` directory layout
2. clones `NousResearch/hermes-agent` at the pinned release tag with submodules
3. creates a Python 3.11 virtual environment with `uv`
4. installs Hermes with `uv pip install -e ".[all]"` using the venv interpreter
5. runs `npm install` in the Hermes checkout
6. copies `cli-config.yaml.example` to `~/.hermes/config.yaml` if needed
7. creates an empty `~/.hermes/.env` if one does not already exist
8. seeds repo-managed skills into `~/.hermes/skills`
9. launches Hermes inside a persistent `tmux` session and serves that session through `ttyd`

This means the image stays reproducible for the base system while still following the official Hermes installation path.

### Utility Naming

Repo-owned utilities should use a `ghostship-` prefix.

That avoids collisions with:

- upstream project binaries
- packages that may already exist in nixpkgs
- future OS or distro package names

Current example:

- `ghostship-searxng`

## Repository Layout

- `flake.nix`: top-level flake and package outputs
- `flake.lock`: pinned nixpkgs revision
- `packages/hermes-image/`: runtime wrapper, pinned Hermes release, and OCI image definition
- `packages/searxng-cli/`: first Python utility package
- `skills/`: default skills that get seeded into the Hermes runtime
- `scripts/update_hermes_release.py`: scheduled release updater
- `.github/workflows/`: CI, publish, and Hermes release update automation
- `AGENTS.md`: repository-specific memory, conventions, and lessons learned

## Flake Outputs

Current outputs:

- `packages.x86_64-linux.ghostship-searxng`
- `packages.x86_64-linux.ghostship-hermes-runtime`
- `packages.aarch64-linux.ghostship-hermes-image`
- `packages.aarch64-linux.default`
- `devShells.<system>.default`

The arm64 image is the intended production artifact. The x86_64 outputs are there to keep local development and validation practical on an x86 workstation.

## Local Development

Enter the shell:

```fish
direnv allow
```

The dev shell is intentionally smaller than the image. It is tuned for editing, testing, and flake work rather than reproducing the full operator runtime bundle locally.

### Useful Commands

The standardized Python utility workflow is:

1. lock dependencies
2. run tests
3. build the wheel and sdist

Use the shared helper so all `ghostship-` utilities are handled the same way.

Lock a utility:

```fish
python3 scripts/python_utility.py lock packages/searxng-cli
```

Test a utility:

```fish
python3 scripts/python_utility.py test packages/searxng-cli
```

Build a utility:

```fish
python3 scripts/python_utility.py build packages/searxng-cli
```

If you need direct commands for debugging, the helper currently expands to:

```fish
uv lock --project packages/searxng-cli
env PYTHONPATH=packages/searxng-cli/src uv run --with pytest --with typer --with rich --with httpx pytest packages/searxng-cli/tests -q
uv build --project packages/searxng-cli
```

Build the runtime wrapper package:

```fish
nix build .#packages.x86_64-linux.ghostship-hermes-runtime
```

Evaluate the arm64 image derivation:

```fish
nix eval .#packages.aarch64-linux.ghostship-hermes-image.drvPath --raw
```

Build the arm64 image:

```fish
nix build .#packages.aarch64-linux.ghostship-hermes-image
```

Format Nix files:

```fish
nix fmt
```

### Python Utility Conventions

Python utilities in this repo should follow these rules:

- package names and entrypoints are prefixed with `ghostship-`
- code uses `src/` layout
- metadata lives in `pyproject.toml`
- every utility includes `package.nix`, `pyproject.toml`, `uv.lock`, `src/`, and `tests/`
- tests include both unit tests and integration test scaffolding
- CLIs prefer stable, machine-readable interfaces with `--json`
- no interactive prompts
- dependency locking, testing, and building are done through `python3 scripts/python_utility.py <lock|test|build> <package-dir>`

The current SearXNG utility implements:

- `ghostship-searxng search web <query>`
- `--base-url`
- `--category`
- `--limit`
- `--language`
- `--safe-search`
- `--json`

## Image Contents

The arm64 image currently includes:

- Hermes runtime bootstrap wrapper: `ghostship-hermes-runtime`
- Python utility package: `ghostship-searxng`
- operator tooling: `git`, `curl`, `jq`, `yq-go`, `ripgrep`, `fd`, `gh`, `uv`, `python311`, `bash`, `nodejs`, `coreutils`, `wget`, `lsof`, `strace`, `psmisc`, `file`, `tree`, `bubblewrap`, `binutils`, `tmux`, `zip`, `unzip`, `p7zip`, `ripgrep-all`, `codex`, `gemini-cli`, `opencode`
- runtime Nix CLI

The image exposes the repo skill tree through the immutable Nix store and points `GHOSTSHIP_DEFAULT_SKILLS` at that store path, which is then copied into the user-managed Hermes skill directory on first start.

## Runtime Behavior

### Entrypoint

The container entrypoint is:

- `${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime entrypoint`

That entrypoint:

- bootstraps Hermes if the pinned release is not already installed
- seeds repo-managed skills
- ensures a `tmux` session exists
- starts `ttyd` attached to that session

### Ports And Volumes

Exposed port:

- `7681/tcp`

Expected persistent volumes:

- `/home/hermes/.hermes`
- `/nix`

Why both matter:

- `/home/hermes/.hermes` preserves Hermes sessions, config, skills, and the Hermes source/venv install
- `/nix` preserves ad hoc runtime Nix downloads and prevents repeated package fetches

### Runtime Environment Variables

Current important environment variables:

- `HOME=/home/hermes`
- `HERMES_HOME=/home/hermes/.hermes`
- `GHOSTSHIP_HERMES_REF=<tag from packages/hermes-image/hermes-release.txt>`
- `GHOSTSHIP_DEFAULT_SKILLS=<immutable Nix store path for the repo skill tree>`
- `TTYD_PORT=7681` by default
- `TTYD_SESSION_NAME=hermes` by default
- `TTYD_TITLE=Hermes` by default
- `TERMINAL_CWD=/home/hermes` by default

Useful override:

- `GHOSTSHIP_HERMES_REPO` if you need to test against a fork instead of the upstream repo

## Running The Container

### Minimal Run

Expose `ttyd` and mount persistent volumes:

```fish
docker run \
  --rm \
  --publish 7681:7681 \
  --volume ghostship-hermes-home:/home/hermes/.hermes \
  --volume ghostship-hermes-nix:/nix \
  ghcr.io/<owner>/ghostship-hermes:latest
```

### Run With Local Config

Mount an existing Hermes config and env file:

```fish
docker run \
  --rm \
  --publish 7681:7681 \
  --volume ghostship-hermes-home:/home/hermes/.hermes \
  --volume ghostship-hermes-nix:/nix \
  --volume (pwd)/config.yaml:/home/hermes/.hermes/config.yaml:ro \
  --volume (pwd)/.env:/home/hermes/.hermes/.env:ro \
  ghcr.io/<owner>/ghostship-hermes:latest
```

### Operational Notes

- The first startup is slower because Hermes is cloned and installed into the persistent runtime home.
- Later starts reuse the pinned release if `~/.ghostship-hermes-release` matches the configured tag.
- The image does not enable built-in `ttyd` auth.
- Put the service behind your own reverse proxy, VPN, Tailscale, or comparable access control layer.
- Hermes itself runs in a persistent `tmux` session, so browser disconnects should not tear down the agent process.

## CI And Release Automation

### CI

Workflow: `.github/workflows/ci.yml`

Current CI does three things:

1. checks out the repo
2. installs Nix
3. runs:
   - `nix flake check`
   - Python utility tests via the shared helper
   - `nix build .#packages.x86_64-linux.ghostship-hermes-runtime`
   - `nix eval .#packages.aarch64-linux.ghostship-hermes-image.drvPath --raw`

The CI job runs on x86_64, so it verifies the arm64 image still evaluates but leaves the full image build to the dedicated arm64 publish workflow.

### Image Publish

Workflow: `.github/workflows/publish-image.yml`

Current publish flow:

1. runs on `main` and on manual dispatch
2. builds the arm64 image on an arm64 GitHub runner
3. uploads the resulting Docker archive tarball as an artifact
4. publishes to GHCR using `skopeo`

Current tag strategy:

- `latest`
- `sha-<commit>`
- `hermes-<upstream-release-tag>`

### Hermes Release Updates

Workflow: `.github/workflows/update-hermes-release.yml`

This scheduled workflow:

1. queries `https://api.github.com/repos/NousResearch/hermes-agent/releases/latest`
2. compares it with `packages/hermes-image/hermes-release.txt`
3. updates the pinned file and `CHANGELOG.md` if the tag changed
4. commits and pushes the update

That workflow does not publish directly. It updates the repo state so the normal `main` publish flow can build and ship the new pinned release.

## Skills

Default skills in this repo are stored under `skills/` and are seeded into the Hermes runtime path `~/.hermes/skills`.

Current seeded skill:

- `skills/searxng/SKILL.md`

The intended pattern is:

- utility provides a stable CLI
- skill teaches Hermes or other agents how to use that CLI consistently

## Security And Access Model

Current choices:

- Hermes and `ttyd` run as a non-root `hermes` user after a short root-only init step
- no in-container `sudo`
- external network protection is expected for `ttyd`
- secrets are expected through mounted config and env files

Why this matters:

- the image is meant to be operator-facing, not publicly exposed directly
- `ttyd` without an external boundary is not an acceptable default internet-facing deployment
- persistent Hermes state means you should treat mounted volumes as sensitive

## Known Constraints

- Hermes is not available on the inspected stable `nixos-25.11` nixpkgs branch, so it is bootstrapped from upstream releases instead of being installed from nixpkgs.
- The intended production artifact is arm64 only.
- This session verified the arm64 image derivation evaluates, but not a full arm64 image build on local hardware.
- The current README documents the repository as it exists now, not a finished product surface.

## Roadmap

Near-term follow-up work:

- finish end-to-end arm64 image build verification
- run the first container boot against the pinned Hermes release
- tighten image/runtime tests
- add more `ghostship-` utilities and paired skills
- decide whether Discord gateway mode should be added as an alternative runtime path later

## Related Files

- [flake.nix](/home/nixos/dev/personal/nixos-hermes/flake.nix)
- [packages/hermes-image/runtime.nix](/home/nixos/dev/personal/nixos-hermes/packages/hermes-image/runtime.nix)
- [packages/hermes-image/image.nix](/home/nixos/dev/personal/nixos-hermes/packages/hermes-image/image.nix)
- [packages/hermes-image/hermes-release.txt](/home/nixos/dev/personal/nixos-hermes/packages/hermes-image/hermes-release.txt)
- [packages/searxng-cli/pyproject.toml](/home/nixos/dev/personal/nixos-hermes/packages/searxng-cli/pyproject.toml)
- [packages/searxng-cli/src/ghostship_searxng/cli.py](/home/nixos/dev/personal/nixos-hermes/packages/searxng-cli/src/ghostship_searxng/cli.py)
- [.github/workflows/ci.yml](/home/nixos/dev/personal/nixos-hermes/.github/workflows/ci.yml)
- [.github/workflows/publish-image.yml](/home/nixos/dev/personal/nixos-hermes/.github/workflows/publish-image.yml)
- [.github/workflows/update-hermes-release.yml](/home/nixos/dev/personal/nixos-hermes/.github/workflows/update-hermes-release.yml)
- [scripts/update_hermes_release.py](/home/nixos/dev/personal/nixos-hermes/scripts/update_hermes_release.py)
