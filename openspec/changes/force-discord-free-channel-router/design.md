## Context

The managed Hermes image currently projects Discord free-response channels into each profile `.env`, but the active managed profile model path still defaults to direct Codex runtime settings. Upstream Hermes also carries session-scoped model switching inside the gateway, and that upstream path is currently unreliable for Discord sessions when a custom endpoint should stay in effect. The repo therefore needs a narrow, repo-owned guard in its existing Hermes wrapper layer so Discord free-response sessions always execute against the local router without introducing new runtime env or auth contracts.

The repo already patches upstream Hermes through `packages/hermes-agent-wrapped/package.nix`, which is the smallest supported seam for this behavior. That same seam is also the right place to remove any leftover repo-owned Discord plugin logic that tried to influence model selection but never became part of the supported runtime behavior.

## Goals / Non-Goals

**Goals:**
- Force managed Discord free-response turns onto the local router path every time.
- Pin those turns to the repo-approved router alias instead of the profile's default direct model.
- Prevent `/model` or cached session overrides from reintroducing unsupported provider switches in Discord free-response sessions.
- Remove the dead repo-owned Discord plugin path from the supported managed runtime behavior.

**Non-Goals:**
- Changing the operator-facing Discord env contract.
- Adding new auth, API-key, or router credential requirements.
- Making the entire managed image router-primary in this change.
- Reworking Hermes upstream Discord behavior outside the minimum repo-owned guard needed here.

## Decisions

### Patch the Hermes wrapper instead of widening Nix or bootstrap contracts

The repo already carries targeted upstream Hermes shims in `packages/hermes-agent-wrapped/package.nix`. Extending that wrapper is smaller and safer than adding new Nix settings, new profile `.env` projections, or a forked upstream package just to force one Discord execution path.

Alternative considered: express this declaratively in managed profile config.
Rejected because the upstream gateway currently exposes no declarative Discord free-channel model override that would reliably beat session-scoped switches.

### Detect Discord free-response sessions from the existing source and env contract

The managed runtime already knows which channels are free-response channels through `DISCORD_FREE_RESPONSE_CHANNELS`, and Hermes session handling already builds a `SessionSource` with `platform`, `chat_type`, and `chat_id`. The wrapper patch should detect Discord free-response sessions using those existing fields rather than adding new per-channel metadata or bootstrap state.

Alternative considered: project a separate repo-specific env variable for router-pinned Discord channels.
Rejected because it duplicates the existing Discord free-response contract and widens operator inputs for no gain.

### Force the turn runtime directly instead of relying on upstream session switches

For matched Discord free-response sessions, the wrapper should override the turn configuration before agent creation so the gateway uses:
- router alias `coding`
- `base_url = http://127.0.0.1:8788/v1`

This keeps the fix local to the affected Discord lane and avoids depending on the broken upstream session-switch mechanism to preserve a custom endpoint.

Alternative considered: leave turn setup alone and only block `/model`.
Rejected because the reported bug is that Discord sessions fail to keep the custom model switch applied; blocking `/model` alone does not guarantee router usage for the actual turn.

### Treat `/model` as unsupported in Discord free-response channels

The managed Discord free-response channels should be pinned behavior, not operator-tunable session sandboxes. The wrapper should therefore clear any stale session override for that session and return a fixed guidance message instead of applying or persisting a model switch in that context.

Alternative considered: allow `/model` but try to re-force the router on the next message.
Rejected because it creates misleading user feedback and leaves stale per-session override state around the gateway cache.

### Remove the old repo-owned Discord plugin path from the supported runtime surface

Any leftover repo-owned Discord plugin logic that attempted to steer model selection should be removed as part of this change so the supported behavior is singular: free-response Discord traffic is pinned by the wrapper guard.

Alternative considered: leave the old path in place but undocumented.
Rejected because it preserves dead code and obscures which runtime behavior is authoritative.

## Risks / Trade-offs

- [Risk] The wrapper patch may miss one gateway-created execution path and leave an escape hatch around the router pin. → Mitigation: apply the guard anywhere the gateway resolves turn runtime for Discord sessions, and cover the expected command path in validation.
- [Risk] Pinning the free-response channel to one router alias reduces flexibility for ad hoc model experimentation in that context. → Mitigation: limit the pin only to Discord free-response sessions and leave other managed contexts unchanged.
- [Risk] The repo spec history currently describes router-primary behavior that does not match the live managed profile scaffold. → Mitigation: scope this change to the Discord free-channel guard and document the exact repo-owned runtime behavior being added now.

## Migration Plan

1. Update the wrapper patch so Discord free-response turns are forced to the router alias and unsupported session overrides are rejected in that context.
2. Remove the old repo-owned Discord plugin path during the same wrapper/runtime cleanup.
3. Extend managed validation to prove Discord free-response sessions stay pinned to the router path.
4. Roll back by reverting the wrapper patch if the forced Discord path causes regressions; the previous direct-profile behavior will resume without any env migration.

## Open Questions

- Which exact dead Discord plugin code path still exists in the repo-owned runtime, if any, once implementation starts? The proposal keeps removal in scope, but implementation should confirm the concrete write set before deleting anything.
