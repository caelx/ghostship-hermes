## Context

The managed Ghostship Hermes runtime currently uses direct `opencode-go/minimax-m2.7` as its primary lane and the local router alias `agentic` as its configured fallback. The new Discord workflow needs a different split: keep the direct primary lane for normal runtime behavior, move fallback to Codex, expose the local router as a named manual provider, and give one Discord channel advisory guidance when the session is not using a router-backed free model.

The main constraint is that the user only wants supported Hermes interfaces. The installed Hermes plugin API is agent-side and centered on tool and LLM lifecycle hooks, while the gateway hook system is explicitly non-blocking. That means the router-only Discord channel can use supported hooks to warn, but not to enforce. The design therefore treats the Discord policy as guidance rather than hard admission control.

## Goals / Non-Goals

**Goals:**
- Keep the managed primary model contract on direct `opencode-go/minimax-m2.7`.
- Move the managed fallback contract to `openai-codex/gpt-5.4-mini`.
- Keep auxiliary and compression tasks on the existing direct Gemini Flash-Lite path.
- Expose the local router as one named manual custom provider, `ghostship-router`, so Discord `/model` can target any router-exposed model id without duplicating provider entries.
- Add one managed env, `GHOSTSHIP_ROUTER_CHANNEL`, to identify the Discord channel that should receive router-only guidance.
- Use supported Hermes hook surfaces to send a bold warning in that channel when the session is not using a `ghostship-router` model, including after `/reset`.
- Render one copy-paste `/model custom:ghostship-router:<model>` command per currently exposed router model.

**Non-Goals:**
- Block requests or modify gateway dispatch behavior.
- Add one custom provider per router model.
- Add a new dedicated router alias solely for the Discord channel.
- Reintroduce `DISCORD_FREE_RESPONSE_CHANNELS` as the primary contract for this dedicated router-only workflow.

## Decisions

### Use one named custom provider for the router

The managed config will add a single `custom_providers` entry named `ghostship-router` that points at `http://127.0.0.1:8788/v1`.

Rationale:
- Hermes already supports named custom providers that probe the endpoint's live `/models` list and allow manual model selection.
- A single provider keeps the operator-visible contract stable even when router-exposed model ids change.
- Creating one provider per router model would duplicate config and require image changes whenever router inventory changes.

Alternatives considered:
- Create one custom provider per router model. Rejected because it couples Hermes config churn to router inventory churn.
- Keep using the router only through `fallback_model`. Rejected because the user wants the router exposed for manual `/model` use, not as the configured fallback lane.

### Treat the Discord router channel as advisory guidance only

The router-channel behavior will use supported gateway hooks to send warnings, not to block or reroute messages.

Rationale:
- Hermes's plugin API can inject context into model calls, but it is not a supported pre-dispatch policy enforcement surface.
- Gateway hooks are supported, but explicitly non-blocking.
- Advisory warnings still satisfy the updated user requirement and fit the supported interface boundary.

Alternatives considered:
- Patch the gateway to enforce routing or block requests. Rejected because the user explicitly does not want gateway modifications.
- Do nothing automatically and rely only on documentation. Rejected because the warning meaningfully reduces operator mistakes after `/reset` or session drift.

### Build the warning message from live router inventory

The warning hook should fetch the allowed router model ids from the local router `/v1/models` endpoint and render a full `/model custom:ghostship-router:<model>` command for each exposed model.

Rationale:
- This keeps the warning aligned with the actual router inventory instead of a stale hardcoded list.
- It supports the user's requirement that `GHOSTSHIP_ROUTER_PROFILE` or manual model selection may target any router-exposed model id.
- Full commands make the remediation copy-paste friendly.

Alternatives considered:
- Hardcode `agentic`, `coding`, `auxiliary`, `vision`, and `tts`. Rejected because the router can expose additional model ids and the warning should stay accurate automatically.
- Show only a short subset of models. Rejected because the user explicitly wants a full command for every supported model.

### Warn on both normal message start and reset boundaries

The supported-interface guidance should run when a message begins agent execution in the configured router channel and again after `/reset` so the user is reminded before the next turn proceeds under the default model.

Rationale:
- Session-scoped `/model` overrides normally persist, so this warning should be infrequent.
- `/reset` is the most likely moment for a channel-specific model expectation to be lost.
- Using the same warning content in both places keeps behavior predictable.

Alternatives considered:
- Warn only on `agent:start`. Rejected because `/reset` would still drop the user back into the default lane without immediate guidance.
- Warn only after `/reset`. Rejected because sessions can still drift for other reasons.

## Risks / Trade-offs

- [Gateway hooks may not expose enough context to identify the active model override directly] -> Mitigation: read the same session-scoped model override state the gateway already persists in memory or the nearest supported session state available to the hook, and validate that path during implementation before expanding the hook behavior.
- [The hook warning may race with the normal reply because hooks are non-blocking] -> Mitigation: document this as advisory-only behavior and keep the message direct and actionable.
- [Live `/v1/models` fetches could add latency or fail intermittently] -> Mitigation: cache the router model list briefly inside the hook implementation and degrade to a short failure message if live inventory is unavailable.
- [Discord does not support arbitrary red text in normal messages] -> Mitigation: use a bold warning header and a fenced command block so the guidance remains visually prominent.

## Migration Plan

1. Update the managed runtime model contract to use `openai-codex/gpt-5.4-mini` as fallback and add the `ghostship-router` custom provider.
2. Extend the managed env projection to include `GHOSTSHIP_ROUTER_CHANNEL` and remove this workflow's dependence on `DISCORD_FREE_RESPONSE_CHANNELS`.
3. Stage the advisory Discord hook in the managed Hermes home so the gateway loads it through the supported hook system.
4. Validate that `/model custom:ghostship-router:<model>` works in Discord, that session overrides persist as expected, and that warnings appear in the configured router channel on both message start and after `/reset`.
5. Update runtime docs so operators know the new fallback contract, the named custom provider, and the router-channel warning semantics.

Rollback:
- Remove the staged hook and revert the managed model/env config changes. The runtime will fall back to the prior direct-primary plus router-fallback contract without affecting persisted session history.

## Open Questions

- Which supported event pair is the cleanest for the reset reminder: `command:reset`, `session:reset`, or a small combination of both?
- Does the hook need a small shared helper module to query the router and format commands, or is a self-contained hook easier to maintain in the managed home seed layout?
