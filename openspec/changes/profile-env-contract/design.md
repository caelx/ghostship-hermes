## Context

The Hermes image already treats each managed profile `.env` file as the operator-facing source of truth for profile runtime configuration, and the gateway services load that state through `EnvironmentFile`. The current bootstrap writer, however, still relies on scattered implicit allowlists and ad hoc translations. That has made it too easy to drift between the container-wide environment supplied by `nixos-config` and the profile-local env that Hermes actually reads.

The repo guidance already defines the intended boundary: profile `.env` should contain the profile-facing runtime contract, including Hermes/provider secrets, browser config, Discord settings, Bitwarden access, and operator-facing `ghostship-*` CLI env, while image infrastructure, router-daemon internals, and container boot plumbing stay outside profile `.env`.

This change needs to lock down three things:

1. The exact inventory of env that belongs in each managed profile `.env`
2. The translation rules from repo-owned container env names into profile-local Hermes-facing env names
3. The exclusions that remain intentionally container-only

The browser contract also needs a correction: the managed three-profile contract is per-profile CDP, not one shared CDP default. The profile-scoped container env should therefore be:

- `BROWSER_ASSISTANT_CDP_URL`
- `BROWSER_OPERATIONS_CDP_URL`
- `BROWSER_SUPERVISOR_CDP_URL`

and each profile `.env` should receive only its own translated `BROWSER_CDP_URL`.

## Goals / Non-Goals

**Goals:**
- Define one explicit allowlist for profile-facing env persisted into managed profile `.env`
- Define one explicit translation table from container env to profile-local Hermes env names
- Keep router service env and other infrastructure-only env out of profile `.env`
- Make per-profile browser CDP part of the managed env contract using profile-scoped container inputs
- Keep managed `.env` writes idempotent so unchanged values do not rewrite files or trigger avoidable restarts
- Align proposal, specs, AGENTS guidance, and operator docs around the same env contract

**Non-Goals:**
- Copy every container environment variable into every profile `.env`
- Treat router-daemon configuration as profile-facing configuration
- Expand the image to support arbitrary upstream Hermes env toggles that this repo does not explicitly adopt
- Change the current managed profile set away from `assistant`, `operations`, and `supervisor`

## Decisions

### Persist only profile-facing env, not router-daemon or image-plumbing env

The managed profile `.env` contract should include only env that the profile runtime, profile-local Hermes tooling, or operator-facing profile workflows actually need. Router-daemon service configuration such as router ranking knobs, router state paths, and router listener auth belongs to the router service and remains container-only.

This keeps the profile contract readable and avoids conflating profile runtime state with service-specific infrastructure wiring.

Alternatives considered:
- Persist router vars into every profile `.env` for convenience.
  Rejected because those variables do not apply to the profile runtime contract and would make the operator-facing profile env noisy and misleading.
- Mirror all container env into every profile `.env`.
  Rejected because it would erase the boundary between profile-facing configuration and infrastructure plumbing.

### Use explicit profile-scoped browser CDP env names and translate them into profile-local `BROWSER_CDP_URL`

The managed three-profile contract should treat remote browser CDP as profile-scoped operator configuration. The container environment should therefore expose:

- `BROWSER_ASSISTANT_CDP_URL`
- `BROWSER_OPERATIONS_CDP_URL`
- `BROWSER_SUPERVISOR_CDP_URL`

Bootstrap should translate each one into only that profile's local `BROWSER_CDP_URL`.

This keeps the profile `.env` aligned with the upstream Hermes-facing name while still letting `nixos-config` express different browser targets per profile.

Alternatives considered:
- Keep one shared `BROWSER_CDP_URL`.
  Rejected because it cannot express the intended per-profile contract.
- Keep profile-scoped CDP vars in profile `.env` without translating them.
  Rejected because Hermes expects `BROWSER_CDP_URL` in the profile-local runtime environment.

### Keep translation as a first-class documented contract

The env writer should not merely “copy some keys.” It should apply a documented translation table:

- shared container env copied through unchanged when the profile-local name matches
- profile-scoped container env translated into the upstream Hermes-facing profile-local name
- compatibility aliases normalized into the canonical runtime name when the repo intentionally supports that alias

This makes the contract auditable and reduces drift when new supported env inputs are added.

Alternatives considered:
- Leave translation behavior implicit in shell code.
  Rejected because the current confusion came directly from undocumented implicit translation rules.

### Proposed persisted env inventory

The contract should define these groups.

Shared profile-facing env copied unchanged into every managed profile `.env` when set:

- `TERMINAL_CWD`
- `GOOGLE_AI_STUDIO_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_HTTP_REFERER`
- `OPENROUTER_TITLE`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENCODE_API_KEY`
- `OPENCODE_GO_API_KEY`
- `OPENCODE_BASE_URL`
- `GITHUB_TOKEN`
- `GH_TOKEN`
- `HASS_TOKEN`
- `HASS_URL`
- `BWS_ACCESS_TOKEN`
- `BROWSERBASE_API_KEY`
- `BROWSERBASE_PROJECT_ID`
- `BROWSER_USE_API_KEY`
- `BROWSERBASE_PROXIES`
- `BROWSERBASE_ADVANCED_STEALTH`
- `BROWSERBASE_KEEP_ALIVE`
- `BROWSERBASE_SESSION_TIMEOUT`
- `BROWSER_INACTIVITY_TIMEOUT`
- `CAMOFOX_URL`

Shared compatibility normalization written into every managed profile `.env` when applicable:

- `OPENCODE_GO_API_KEY` may also populate `OPENCODE_API_KEY` when the canonical var is unset

Per-profile translated env:

- `DISCORD_<PROFILE>_BOT_TOKEN` -> `DISCORD_BOT_TOKEN`
- `DISCORD_<PROFILE>_ALLOWED_USERS` -> `DISCORD_ALLOWED_USERS`
- `DISCORD_<PROFILE>_CHANNEL_ID` -> `DISCORD_FREE_RESPONSE_CHANNELS`
- `DISCORD_GENERAL_CHANNEL_ID` -> `DISCORD_HOME_CHANNEL`
- `WEBHOOK_<PROFILE>_SECRET` -> `WEBHOOK_SECRET`
- `BROWSER_<PROFILE>_CDP_URL` -> `BROWSER_CDP_URL`

Profile-local generated values:

- `WEBHOOK_ENABLED=true`
- `WEBHOOK_PORT=<profile port>`

Container-only exclusions:

- `HERMES_HOME`
- `HOME`
- `SSL_CERT_FILE`
- `NIX_SSL_CERT_FILE`
- `GHOSTSHIP_HERMES_PROJECT_ROOT`
- `GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF`
- `GHOSTSHIP_HERMES_PROFILES`
- `GHOSTSHIP_HERMES_DEFAULT_PROFILE`
- `GHOSTSHIP_HERMES_MANAGED_PROFILE`
- `GHOSTSHIP_DASHBOARD_HOST`
- `GHOSTSHIP_ROUTER_HOST`
- `GHOSTSHIP_ROUTER_PORT`
- `GHOSTSHIP_ROUTER_STATE_DIR`
- `GHOSTSHIP_ROUTER_DB_PATH`
- `GHOSTSHIP_ROUTER_REFRESH_INTERVAL`
- `GHOSTSHIP_ROUTER_API_KEY`
- `GHOSTSHIP_ROUTER_CORS_ORIGINS`
- `API_SERVER_HOST`
- `API_SERVER_PORT`
- `API_SERVER_KEY`
- `API_SERVER_CORS_ORIGINS`
- all router ranking and alias policy env

## Risks / Trade-offs

- [Risk] The explicit allowlist may miss a profile-facing env input the repo already relies on implicitly. -> Mitigation: define the inventory in one place and update docs/specs together whenever the contract expands.
- [Risk] Excluding router vars from profile `.env` may break any hidden profile-side workflow that was incorrectly depending on container-only router env. -> Mitigation: document the exclusion clearly and keep the router unit responsible for router-daemon configuration.
- [Risk] Per-profile CDP introduces more operator inputs to manage. -> Mitigation: keep the naming pattern regular and translate into one profile-local runtime name, `BROWSER_CDP_URL`.
- [Risk] Upstream Hermes may add more env-based browser or provider knobs later. -> Mitigation: treat this repo’s allowlist as explicit policy rather than trying to mirror all upstream env reads.

## Migration Plan

1. Define the persisted env allowlist and translation table in the image module.
2. Pass the full supported profile-facing container env inventory into bootstrap.
3. Update `write_profile_env()` so it emits the full allowlist, applies the profile translations, and keeps idempotent file writes.
4. Update AGENTS and operator docs to match the same contract, including the per-profile CDP variable names.
5. Verify that unchanged boot does not rewrite managed `.env`, that changed supported env does rewrite it, and that each profile receives only its own translated browser/Discord/webhook values.

Rollback:
- Revert the env contract change and rebuild. The previous narrower projection behavior returns, including the old shared-CDP documentation.

## Open Questions

- Should `OPENAI_BASE_URL` be part of the supported profile-facing contract wherever `OPENAI_API_KEY` is supported for router-compatible custom endpoints?
- Do we want a shared browser fallback after introducing per-profile CDP, or should the managed three-profile contract require explicit per-profile values only?
- Are there any additional operator-facing `ghostship-*` CLI env inputs that belong in the profile contract today but are not yet enumerated in the current runtime module?
