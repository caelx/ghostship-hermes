## Why

The current NixOS-managed image owns too much of Hermes itself: runtime config projection, service topology, tooling convergence, and a custom dashboard. That conflicts with the desired contract of treating the container like a native Ubuntu workstation where Hermes is managed in place, state survives container replacement, and only the minimum product-specific deltas stay repo-owned.

## What Changes

- **BREAKING** Replace the current NixOS/module-managed runtime with a custom `ubuntu:24.04` workstation image supervised by `s6`.
- **BREAKING** Stop treating bootstrap-generated managed config and `.env` rewrites as the source of truth for Hermes runtime configuration; downstream-owned persisted home state becomes authoritative instead.
- Keep Hermes core immutable and image-owned under `/opt/hermes`, while persisting `/home/hermes`, `/workspace`, and `/nix` across restarts and container replacement.
- Use the upstream Hermes dashboard as the main browser surface, but keep a small repo-owned frontend patch that adds a `Terminal` entry while `ttyd` runs as a separate supervised sidecar behind the published `/terminal/` path.
- Keep the local router as a mandatory core service in the image, and preserve the repo-owned Discord forced-channel patch set: the router-pinned free-response channel plus a `#deepthink` channel pinned to Codex `gpt-5.4` with high reasoning.
- Split the old utility bundle into three layers: minimal immutable core utilities, native-package-manager tooling such as npm-installed agent CLIs, and optional persisted Nix tooling for downstream or Hermes-installed extras.
- Rewrite downstream docs, examples, and GitHub Actions build/publication flows around the new workstation image, including explicit guidance for persisting `/home/hermes`, seeding and reusing `/nix`, and supplying operator-facing environment variables.

## Capabilities

### New Capabilities

- `discord-free-channel-router`: Preserve the repo-owned Discord forced-channel contract as a first-class requirement in the new host-native workstation runtime, including the router-pinned free-response channel and the `#deepthink` Codex lane.

### Modified Capabilities

- `agent-workstation-runtime`: Replace the NixOS/systemd-user managed runtime with an Ubuntu 24.04 workstation image that runs Hermes locally from `/opt/hermes`, supervises core services with `s6`, keeps the router mandatory, defaults Hermes terminal execution to the container-local backend, and avoids repo-owned service/doctor compatibility patches beyond the explicitly approved dashboard/Discord deltas.
- `agent-workstation-home-state`: Change the persisted state contract to `/home/hermes`, `/workspace`, and `/nix`, and require clear downstream guidance for safe `/nix` reuse across rebuilds and container replacement.
- `managed-runtime-tooling`: Move most operator-facing tools out of the immutable image into native package-manager layers or optional persisted Nix installs, while keeping only the minimum package-manager/runtime tools in the base image.
- `mmx-hermes-dashboard`: Replace the repo-owned dashboard implementation with the upstream Hermes dashboard while retaining a small repo-owned terminal-entry patch backed by a separate `ttyd` sidecar.
- `live-image-runtime-gaps`: Validate the new runtime, dashboard, router, persistence, and environment contract directly in the published image and deployment workflow.
- `hermes-profile-env-contract`: Make operator-facing environment configuration downstream-owned and documented, and remove the old bootstrap projection contract.
- `image-publication-contract`: Update CI/publication to build and publish the Ubuntu 24.04 workstation image and keep operator docs/examples aligned with the new image contract.
- `true-hermes-base-image`: Realign the reusable base/final image boundary around Ubuntu, image-owned Hermes core, baked-in Nix, and repo-owned overlays.
- `github-and-ssh-cli-runtime`: Treat `gh` and the OpenSSH client tools as optional userland installs instead of default seeded image tools, while documenting their persisted install/config contract.
- `google-cloud-cli-runtime`: Treat `gcloud` as an optional userland install instead of a default seeded image tool, while documenting its persisted install/config contract.
- `google-workspace-cli-runtime`: Treat the pinned `gws` CLI as an optional userland install instead of a default seeded image tool, while keeping its pinned-install guidance.
- `bitwarden-cli-runtime`: Treat `bws` as an optional userland install instead of a default seeded image tool, while keeping its persisted config contract.

## Impact

- Affected runtime code: `packages/hermes-image/*`, `packages/hermes-agent-wrapped/*`, router/dashboard wiring, boot/runtime env handling, and any code that still assumes NixOS or `systemd --user`.
- Affected image/build systems: Dockerfile/image assembly, multi-arch publication, smoke tests, and GitHub Actions workflows that currently build or publish the NixOS image contract.
- Affected operator docs: `README.md`, deployment examples, persistence docs, environment-variable docs, release notes, and AGENTS durable guidance.
- Affected runtime behavior: service supervision moves to `s6`, Hermes runtime config becomes downstream-owned, default tools move out of the immutable image, and the browser surface becomes the upstream dashboard with a minimal repo-owned terminal entry backed by a separate `ttyd` sidecar.
