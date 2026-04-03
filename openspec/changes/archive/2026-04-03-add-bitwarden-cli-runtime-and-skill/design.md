## Context

The Hermes image currently bundles operator tools directly in `packages/hermes-image/image.nix` and seeds repo-managed skills into `~/.hermes/skills` on first start without overwriting existing content. The container does not yet include a password-manager client, so agents have no standard way to receive shared secrets from an operator.

The user wants the official Bitwarden CLI, not an unofficial wrapper. That means the design has to work with Bitwarden's documented model: API-key login, explicit unlock, ephemeral `BW_SESSION`, and local CLI state under `BITWARDENCLI_APPDATA_DIR`. The important design work is therefore not packaging complexity, but deciding how Hermes should present a stable, noninteractive workflow to agents without baking secrets into the image itself.

## Goals / Non-Goals

**Goals:**
- Add the official `bw` executable to the Hermes image through the repo's normal Nix/image wiring.
- Keep the integration compatible with stateless, noninteractive use driven by environment variables.
- Seed a repo-managed Bitwarden skill that teaches agents the supported login, unlock, sync, and retrieval workflow.
- Document how a dedicated Bitwarden account and shared collections are expected to supply credentials to the agent.
- Keep the integration aligned with the repo's preference for direct bundled tools on `PATH` rather than `nix run` wrappers inside the container.

**Non-Goals:**
- Auto-login or auto-unlock Bitwarden during container startup.
- Store Bitwarden credentials, master passwords, or sessions in the repo or image defaults.
- Build a Ghostship-specific wrapper CLI around `bw`.
- Implement profile-aware secret orchestration beyond the documented environment-variable workflow.

## Decisions

### Use the official nixpkgs `bitwarden-cli` package directly in the image

The Hermes image will bundle `bitwarden-cli` directly in `imageContents`, the same way it already bundles other operator tools. This keeps `bw` available on `PATH` inside the container without asking agents to run `nix run` or install the CLI manually.

Alternative considered: install Bitwarden CLI at runtime with `npm` or a downloaded release artifact. Rejected because it adds a second packaging path outside the repo's flake-managed image composition and weakens reproducibility.

### Standardize on env-driven login and unlock rather than persisted sessions

The supported workflow will assume operators provide `BW_CLIENTID`, `BW_CLIENTSECRET`, and `BW_PASSWORD` through the environment, then agents run `bw login --apikey` and derive `BW_SESSION` from `bw unlock --passwordenv BW_PASSWORD --raw`. `BW_SESSION` remains ephemeral and shell-scoped; the system should treat it as re-creatable state, not as a durable configuration value.

Alternative considered: prefer `rbw` or another wrapper that keeps an in-memory agent. Rejected because the user explicitly chose the official Bitwarden client and wants the environment-variable-driven stateless model.

### Keep Bitwarden's local appdata in Hermes-managed persistent state, but leave secret env injection to the operator

The docs and skill should standardize a writable `BITWARDENCLI_APPDATA_DIR` under the Hermes home so Bitwarden's local config database persists with Hermes state. The image should not set `BW_CLIENTID`, `BW_CLIENTSECRET`, `BW_PASSWORD`, or `BW_SESSION` itself; those belong to operator-managed environment injection or per-shell setup.

Alternative considered: export all Bitwarden-related environment variables globally from the runtime entrypoint. Rejected because secret values do not belong in image defaults, and forcing a single global session model would create surprising cross-shell behavior.

### Add a local Bitwarden skill instead of relying on README guidance alone

The repo should add a local `skills/bitwarden/` skill and seed it with the rest of the default skill tree. That keeps the official workflow close to the agent, allows shared-secret conventions to be documented where the model can follow them directly, and matches how other repo-managed integrations are taught.

Alternative considered: document Bitwarden only in `README.md`. Rejected because the user explicitly asked for a skill, and a seeded skill is the most reliable place to encode the operating contract for agents.

### Use shared collections and JSON-friendly retrieval patterns as the supported operator workflow

The docs and skill should assume the operator shares credentials with a dedicated agent Bitwarden account through shared collections or equivalent supported sharing primitives, then the agent runs `bw sync` before retrieval and prefers JSON/raw-capable commands for downstream scripting.

Alternative considered: treat direct manual item entry into the agent's personal vault as the primary path. Rejected because the user explicitly described a shared-password workflow, and shared collections are the cleaner operational model.

## Risks / Trade-offs

- [Bitwarden's official CLI requires explicit unlock and ephemeral `BW_SESSION`] -> Encode the unlock/export flow in the skill and docs so agents regenerate sessions on demand instead of assuming persistent login state.
- [Operators could accidentally leak secrets by exporting env vars carelessly] -> Keep secret env vars out of image defaults and document that they should be injected intentionally per container or per shell.
- [Bitwarden CLI stores local state outside the session token] -> Standardize a writable `BITWARDENCLI_APPDATA_DIR` under Hermes-managed state so the local cache/config behaves predictably across restarts.
- [A local skill could drift from Bitwarden's official workflow] -> Keep the skill narrowly focused on the official CLI commands and refresh it when the packaged CLI version changes materially.

## Migration Plan

1. Add `bitwarden-cli` to the repo's image package wiring and verify it evaluates as part of the normal flake outputs.
2. Add a repo-managed Bitwarden skill to the default seeded skill inventory.
3. Update README and support docs to describe the supported env vars, the stateless login/unlock flow, and the shared-collection operating model.
4. Verify `bw` is present on `PATH`, the seeded skill appears in a fresh Hermes profile, and the documented workflow matches the shipped CLI.
5. If rollback is needed, remove the image package wiring and the seeded skill together so the image returns to its previous tool inventory cleanly.

## Open Questions

- Should the repo set a non-secret default `BITWARDENCLI_APPDATA_DIR` in the runtime environment, or should the skill/docs be the only place that defines the recommended path?
- Do we want the Bitwarden skill to include concrete `bw get` and `bw list` examples for item IDs, or keep it focused on the authentication/session contract plus high-level retrieval guidance?
