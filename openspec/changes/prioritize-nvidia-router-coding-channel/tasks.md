## 1. NVIDIA Provider Integration

- [ ] 1.1 Extend router configuration to read NVIDIA Build API credentials and provider settings.
- [ ] 1.2 Add a native `nvidia-build` provider adapter for the hosted chat-completions API.
- [ ] 1.3 Define the curated free-only NVIDIA model inventory and wire it into router refresh behavior.

## 2. Routing Policy Updates

- [ ] 2.1 Make provider-priority policy explicit so `nvidia-build` outranks `opencode-zen` and `openrouter` by default.
- [ ] 2.2 Enforce the top-3-per-provider-per-bucket shortlist rule consistently in alias candidate selection.
- [ ] 2.3 Update provider-prefix normalization, alias pin handling, and ranking-worker selection so NVIDIA participates as a first-class provider.

## 3. Discord Router Channel Changes

- [ ] 3.1 Change the managed `ghostship-router` custom-provider default model from `agentic` to `coding`.
- [ ] 3.2 Update the managed Discord forced-channel route patch and `/model` rejection messaging to pin the router channel to `coding`.

## 4. Validation

- [ ] 4.1 Add or update router tests for NVIDIA provider registration, curated inventory loading, free-only routing, and provider-priority ordering.
- [ ] 4.2 Add or update router tests for the top-3-per-provider-per-bucket shortlist behavior.
- [ ] 4.3 Add or update image/runtime validation for the Discord router channel’s `coding` pin.

## 5. Docs And Contract Updates

- [ ] 5.1 Update router docs for NVIDIA credential input, curated free-only inventory, provider priority, and shortlist policy.
- [ ] 5.2 Update runtime and Discord documentation to reflect the router channel’s `coding` pin.
- [ ] 5.3 Reconcile any affected OpenSpec/runtime contract references so the new router and Discord behavior matches the checked-in specs and validation language.
