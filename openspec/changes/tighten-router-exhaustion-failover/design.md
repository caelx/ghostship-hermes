## Context

The Ghostship router is intentionally optional in `#freedom`: operators should be able to force-pick it when desired, and the advisory warning should teach that path. In the live image, the warning hook was recording a session as warned even when Discord rejected the message, and the Discord `/model` picker was passing only `cfg.get("providers")` into Hermes' provider-list helper. Because the managed runtime declares `ghostship-router` under `custom_providers`, the modal never showed it.

## Decisions

### 1. Patch Hermes picker behavior in the wrapped package

The image already wraps upstream Hermes to patch a few runtime behaviors. Extend that wrapper to:

- make `gateway/run.py` pass `custom_providers` into the picker path when no legacy `providers` dict exists
- make `hermes_cli/model_switch.py` treat a `custom_providers` list as a valid provider source for `list_authenticated_providers`
- probe custom-provider `/models` when possible so the Discord modal can display concrete model choices instead of an empty provider row

This keeps the fix local to the shipped image without requiring a fork of the upstream Hermes source tree.

### 2. Make channel warnings delivery-aware and periodic

The router-channel advisory hook should:

- mark a session as warned only after Discord accepts the message
- retry on the next `agent:start` if delivery failed
- repeat at most once per 60 seconds for an active session that is still not router-backed

This preserves the advisory nature of the hook while avoiding silent one-shot suppression.

### 3. Converge managed config away from stale router auth and mention gating

The managed scaffold and boot-time config reconciliation should treat the following as image-owned state:

- `custom_providers.ghostship-router` has no `api_key` field
- `discord.require_mention` is `false`
- stale router `api_key` or old model `base_url` fields are removed during convergence

The fallback model should remain `openai-codex / gpt-5.4-mini`, matching the desired live contract rather than the older router-fallback experiment.

## Risks

- Probing a custom provider during picker construction can add a small delay. Keep the existing short timeout and fall back to configured models if probing fails.
- Repeating warnings too aggressively would be noisy. Use a fixed 60-second minimum interval.
- Config convergence must stay narrow so it only removes stale image-owned router fields and does not clobber unrelated user config.
