## 1. NVIDIA Provider Integration

- [x] 1.1 Extend router configuration to read NVIDIA Build API credentials and provider settings.
- [x] 1.2 Add a native `nvidia-build` provider adapter for the hosted chat-completions API.
- [x] 1.3 Define the curated free-only NVIDIA model inventory and wire it into router refresh behavior.

## 2. Routing Policy Updates

- [x] 2.1 Make provider-priority policy explicit so `nvidia-build` outranks `opencode-zen` and `openrouter` by default.
- [x] 2.2 Enforce the top-3-per-provider-per-bucket shortlist rule consistently in alias candidate selection.
- [x] 2.3 Update provider-prefix normalization, alias pin handling, and ranking-worker selection so NVIDIA participates as a first-class provider.

## 3. Discord Router Channel Changes

- [x] 3.1 Change the managed `ghostship-router` custom-provider default model from `agentic` to `coding`.
- [x] 3.2 Update the managed Discord forced-channel route patch and `/model` rejection messaging to pin the router channel to `coding`.

## 4. Validation

- [x] 4.1 Add or update router tests for NVIDIA provider registration, curated inventory loading, free-only routing, and provider-priority ordering.
- [x] 4.2 Add or update router tests for the top-3-per-provider-per-bucket shortlist behavior.
- [x] 4.3 Add or update image/runtime validation for the Discord router channel’s `coding` pin.

## 5. Docs And Contract Updates

- [x] 5.1 Update router docs for NVIDIA credential input, curated free-only inventory, provider priority, and shortlist policy.
- [x] 5.2 Update runtime and Discord documentation to reflect the router channel’s `coding` pin.
- [x] 5.3 Reconcile any affected OpenSpec/runtime contract references so the new router and Discord behavior matches the checked-in specs and validation language.
