## Why

The live router behavior on `chill-penguin` shows two gaps in the current exhaustion proposal. First, startup inventory refresh still triggers worker-assisted ranking calls, and those calls immediately spend free-lane capacity before the first user request. Second, the provider disable policy is still too aggressive for temporary upstream `429` responses with explicit retry windows, especially on OpenRouter free lanes and OpenCode Zen free usage throttles.

The proposal also needs to lock down provider credential precedence. The router must always use `OPENROUTER_API_KEY` for OpenRouter, and it must prefer `OPENCODE_GO_API_KEY` over `OPENCODE_API_KEY` for OpenCode Zen when both are present.

## What Changes

- Stop worker-assisted ranking calls during startup inventory refresh and rely on the router's deterministic ranking order plus any persisted ranking data that already exists.
- Treat assisted ranking as a deferred or explicitly enabled path rather than part of cold-start routing readiness.
- Make provider credential precedence explicit so OpenRouter always uses `OPENROUTER_API_KEY` and OpenCode Zen prefers `OPENCODE_GO_API_KEY`.
- Soften provider disablement so temporary upstream throttles use provider-scoped pacing, short backoff ladders, and `Retry-After` hints first, while six-hour provider disablement is reserved for stronger exhaustion signals.
- Keep transparent ranked failover across OpenRouter and OpenCode Zen by ranking the top three models per provider per alias and alternating between provider lanes before revisiting the same provider.

## Capabilities

### Modified Capabilities

- `model-router-service`: Change startup ranking behavior, provider credential precedence, and provider-wide exhaustion suppression so cold start is cheaper and temporary throttles do not over-disable providers.

## Impact

- Affected code: `packages/hermes-router/src/hermes_router/{config,service,state}.py`, provider adapters, runtime wiring, and router tests.
- Affected systems: router startup behavior, candidate ordering, provider credential resolution, cooldown state, and failover behavior for OpenRouter and OpenCode Zen.
- External behavior: callers should still see transparent request failover, but startup should no longer burn free-model requests for ranking and temporary `429` bursts should result in narrower backoff than the current six-hour provider disable.
