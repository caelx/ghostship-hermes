## 1. Refactor Router Exhaustion State

- [ ] 1.1 Separate model exhaustion cooldown state from provider-wide cooldown state in the router state store and data model.
- [ ] 1.2 Add persisted state for provider exhaustion evidence, suspect-window tracking, and provider recovery or probe mode.
- [ ] 1.3 Add configurable exhaustion ladder, suspect-window, provider-disable, and probe-recovery settings to router configuration.

## 2. Tighten Provider Classification

- [ ] 2.1 Update the OpenRouter adapter so exhaustion-class failures are classified precisely enough for the new model and provider breaker rules.
- [ ] 2.2 Update the OpenCode Zen adapter so explicit balance or spend-limit exhaustion is classified separately from ordinary throttling.
- [ ] 2.3 Ensure non-exhaustion failures such as `model_missing`, endpoint-family mismatch, and bad requests do not contribute to provider exhaustion trips.

## 3. Rework Transparent Failover

- [ ] 3.1 Change request failure handling so a retryable exhaustion failure applies the per-model cooldown ladder without immediately disabling the whole provider.
- [ ] 3.2 Recompute remaining candidates from the ranked priority list after each retryable exhaustion failure and continue the same request transparently.
- [ ] 3.3 Trip provider-wide disablement only after distinct-model zero-output exhaustion evidence is recorded within the suspect window, including when attempts switched providers in between.
- [ ] 3.4 Add probe-style provider recovery after disablement expiry and re-disable escalation on failed probe attempts.

## 4. Expose Breaker State

- [ ] 4.1 Extend debug and state surfaces to expose model exhaustion cooldowns, provider disablement state, suspect-window evidence, and probe mode.
- [ ] 4.2 Extend router metrics so operators can observe exhaustion trips, active provider disablement, and recovery or probe behavior.

## 5. Validate Behavior

- [ ] 5.1 Add unit tests for the model exhaustion cooldown ladder, including `30s`, `1m`, `5m`, and `10m` escalation and reset on success.
- [ ] 5.2 Add routing tests that verify the next attempt still comes from the ranked priority list after a retryable exhaustion failure.
- [ ] 5.3 Add provider-breaker tests for distinct-model zero-output exhaustion on the same provider, including cross-provider attempts between the two failures.
- [ ] 5.4 Add recovery tests for six-hour provider disablement and probe-mode re-disable behavior.
