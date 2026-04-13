## 1. Remove Startup Ranking Traffic

- [x] 1.1 Change startup inventory refresh so it does not invoke worker-assisted ranking during the `startup` refresh path.
- [x] 1.2 Ensure cold-start candidate ordering uses deterministic heuristic scoring plus any persisted ranking data already stored in the router state.
- [x] 1.3 Decide whether deferred assisted ranking remains scheduled after startup or becomes an explicit opt-in path, and wire the chosen behavior into configuration and service flow.

## 2. Lock Down Provider Credentials

- [x] 2.1 Keep OpenRouter credential loading pinned to `OPENROUTER_API_KEY`.
- [x] 2.2 Change OpenCode Zen credential precedence so `OPENCODE_GO_API_KEY` wins over `OPENCODE_API_KEY` when both are present.
- [x] 2.3 Add config tests that cover single-key and dual-key env combinations for Zen credential resolution.

## 3. Add Provider-Scoped Pacing

- [x] 3.1 Add provider-scoped request spacing with defaults of `3s` for OpenRouter and `2s` for OpenCode Zen.
- [x] 3.2 Parse provider `Retry-After` hints and feed them into temporary throttle pacing or cooldown handling.
- [x] 3.3 Distinguish temporary upstream throttles from hard exhaustion in the OpenRouter and OpenCode Zen adapters.
- [x] 3.4 Retune provider-wide suppression so temporary free-lane throttles prefer provider pacing and ranked reselection before any six-hour provider disablement.
- [x] 3.5 Preserve six-hour or longer provider disablement for explicit balance or quota exhaustion and failed probe recovery.

## 4. Keep Transparent Failover Working

- [x] 4.1 Rank the top three eligible models per provider for each alias.
- [x] 4.2 Verify request-time failover alternates between provider lanes after each retryable failure across both providers.
- [x] 4.3 Ensure softened suppression still prevents thrashing when both providers are temporarily throttled.
- [x] 4.4 Expose whether a model or provider is cooling down because of provider pacing, a temporary throttle, or a hard provider disable.

## 5. Validate the New Behavior

- [x] 5.1 Add startup tests that prove inventory refresh does not send assisted ranking requests.
- [x] 5.2 Add provider-adapter tests for `Retry-After`, temporary OpenRouter upstream throttles, and Zen `FreeUsageLimitError` handling.
- [x] 5.3 Add routing tests that show temporary throttles do not immediately blackhole both providers for six hours.
- [x] 5.4 Add routing tests for top-three-per-provider ranking and provider alternation during failover.
- [x] 5.5 Re-run the router test suite and confirm the revised policy still supports transparent failover.
