## 1. Discord Picker

- [x] 1.1 Patch the wrapped Hermes gateway to feed `custom_providers` into the Discord `/model` picker path.
- [x] 1.2 Patch the wrapped Hermes model-switch helper so named `custom_providers` can surface models in the picker.

## 2. Router Channel Guidance

- [x] 2.1 Make the router-channel warning hook record warnings only after a successful Discord post.
- [x] 2.2 Change warning throttling from once-per-session to once per 60 seconds for active non-router chats.
- [x] 2.3 Add regression tests for failed delivery retry and 60-second re-warning.

## 3. Managed Config Contract

- [x] 3.1 Remove repo-managed `OPENAI_API_KEY` usage from the `ghostship-router` custom-provider scaffold.
- [x] 3.2 Keep `discord.require_mention = false` in the managed scaffold and boot-time config convergence.
- [x] 3.3 Keep the configured fallback on `openai-codex / gpt-5.4-mini` and update runtime validation coverage.

## 4. Validation

- [x] 4.1 Update image/dashboard tests for the new managed config contract.
- [x] 4.2 Validate the router-channel hook tests locally.
- [x] 4.3 Validate the wrapped Hermes package build and final image publication path.
