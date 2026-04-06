## Context

The image already runs `ghostship-hermes-router` as a first-class systemd service and exposes a stable OpenAI-compatible localhost API, but the Hermes bootstrap path still writes direct upstream model defaults and the dashboard still infers provider state from OpenRouter-specific environment variables. That creates a mismatch between the documented deployment model and the runtime that local validation actually exercises.

This change crosses the image bootstrap, managed profile services, dashboard environment console, and container validation scripts. It also has one intentional asymmetry: the root Hermes default remains `lightweight`, while the sticky default profile `operations` uses `heavyweight` and `coder` uses `coding`. The dashboard therefore needs to represent both root and profile defaults clearly instead of collapsing them into a single “provider” assumption.

## Goals / Non-Goals

**Goals:**
- Make Hermes use `http://127.0.0.1:8788/v1` as its primary OpenAI-compatible model endpoint.
- Set the approved alias defaults across all three configured entry points: root `lightweight`, `operations` `heavyweight`, and `coder` `coding`.
- Ensure the managed profile gateway services do not start ahead of the router they now depend on.
- Make container validation prove the router-first path by checking router health, alias discovery, and the configured root/profile defaults.
- Make the dashboard environment view provider-agnostic by default and router-aware when the configured endpoint is the local router.

**Non-Goals:**
- Introduce a Hermes `custom_providers` configuration block for the router.
- Redesign router alias semantics, ranking policy, or provider adapters.
- Add new long-lived Hermes profiles beyond `operations` and `coder`.
- Turn the dashboard into a full router administration surface.

## Decisions

### Use the router as a generic OpenAI-compatible endpoint

Hermes should use the router through `model.base_url = http://127.0.0.1:8788/v1` with logical aliases as `model.default`, rather than through a Hermes-specific custom provider definition.

Rationale:
- the router already exposes the OpenAI-compatible endpoints Hermes needs
- a single `model.base_url` path is smaller and easier to validate than a `custom_providers` block
- it keeps the runtime contract aligned with the same API shape used by external clients

Alternative considered:
- configure the router as a Hermes custom provider. Rejected because it adds configuration surface without solving a problem the existing OpenAI-compatible API does not already solve.

### Generate distinct root and per-profile model settings

The root Hermes config should default to `lightweight`, while generated profile configs should override `operations` to `heavyweight` and `coder` to `coding`.

Rationale:
- the user wants all three router aliases represented in the shipped runtime
- root/default remains the least expensive generic entry point
- `operations` gets the stronger default without forcing `coder` onto the same tier

Alternative considered:
- make root follow the sticky default profile. Rejected because it would lose direct coverage of one alias and collapse the intended three-endpoint test matrix.

### Make the dashboard generic first, router-aware second

The dashboard should stop inferring the environment solely from `OPENROUTER_*` variables. Instead, it should read generic Hermes model settings from config files, expose root/profile endpoint and model details, and optionally query router runtime surfaces when the configured endpoint is the local router.

Rationale:
- this supports any provider shape Hermes can express through `model.base_url`
- it avoids hardcoding one card layout per vendor
- it lets the dashboard show richer runtime truth when the router is active

Alternative considered:
- continue to model provider state primarily from environment variables. Rejected because it is OpenRouter-specific and does not describe the real runtime once Hermes points at the local router.

### Treat router-first validation as part of the runtime contract

The image smoke test and persistence validation should assert router service health, alias discovery from `/v1/models`, and the expected root/profile model defaults both before and after replacement.

Rationale:
- current validation can pass while Hermes still points at direct upstream model identifiers
- the repo’s deployment contract depends on the router path, not just on the router service existing

Alternative considered:
- keep tests focused on dashboard reachability and profile creation only. Rejected because that would not prove the router-primary behavior the image is expected to deploy.

## Risks / Trade-offs

- [Risk] Root `lightweight` and default profile `operations` `heavyweight` can look contradictory in the dashboard. -> Mitigation: show root model and default-profile model as separate facts, not as one collapsed “default model”.
- [Risk] Router startup delay could block managed profile gateways. -> Mitigation: add explicit service ordering and validation checks around router readiness and active status.
- [Risk] Authenticated router endpoints could complicate dashboard enrichment later. -> Mitigation: keep the initial dashboard enrichment path read-only and local-router-specific; if router auth is enabled, carry the token explicitly instead of inferring it from OpenRouter env.
- [Risk] Existing docs and scripts refer to `OPENROUTER_TEST_MODEL`, which can drift from the new contract. -> Mitigation: replace that variable in validation docs and tests with router alias assertions and router health checks.

## Migration Plan

1. Update the image bootstrap to write router-first root and profile configs.
2. Add router dependency ordering for managed profile gateway services.
3. Update the dashboard environment payload to expose generic endpoint/model data and local-router enrichment.
4. Replace direct-upstream validation assumptions with router-first checks.
5. Update README guidance to document the new runtime contract and validation path.

Rollback:
- restore direct upstream model defaults in bootstrap
- remove router-first assertions from validation scripts
- leave the router service installed but non-primary

## Open Questions

- Should the dashboard fetch router enrichment only when the configured base URL exactly matches `127.0.0.1:8788`, or also when it resolves to equivalent localhost forms such as `localhost:8788`?
- If router auth is enabled in a later deployment, should the dashboard consume the same `OPENAI_API_KEY` path used by Hermes, or should it stay unauthenticated and show only config-derived data?
