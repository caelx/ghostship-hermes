## 1. Runtime Contract

- [x] 1.1 Update the managed Hermes defaults in `packages/hermes-image/build/init_home.py` and `packages/hermes-image/nixos-module.nix` so the primary model is `openai-codex/gpt-5.4`, the fallback model is `opencode-go/minimax-m2.7`, and the managed agent default reasoning effort is `medium`
- [x] 1.2 Remove the managed Discord Codex lane from `packages/hermes-image/build/prepare_upstream_hermes.py` so only the router-pinned forced Discord route remains
- [x] 1.3 Keep the router custom-provider scaffolding intact while ensuring the retired Codex-channel env no longer has repo-owned routing behavior

## 2. Migration And Validation

- [x] 2.1 Extend managed config convergence in `packages/hermes-image/nixos-module.nix` so persisted homes are rewritten away from the retired primary/fallback order and high managed reasoning default
- [x] 2.2 Update `tests/hermes-image/single-agent-dashboard.sh` to assert the new primary/fallback order and the removed `GHOSTSHIP_CODEX_CHANNEL` contract
- [x] 2.3 Update `scripts/validate_workstation_persistence.sh` to verify persisted-home migration to the new provider order and managed reasoning default without relying on the retired Codex lane

## 3. Docs And Contract Cleanup

- [x] 3.1 Update `README.md`, `docs/runtime-env.md`, and `docs/workstation-image.md` to remove `GHOSTSHIP_CODEX_CHANNEL` and describe Codex-primary runtime plus OpenCode fallback
- [x] 3.2 Update `AGENTS.md` durable lessons and invariants so repo memory matches the new provider order and Discord contract
- [x] 3.3 Add a `CHANGELOG.md` entry describing the provider-order flip, Codex-lane removal, and persisted-config migration behavior

## 4. Verification

- [ ] 4.1 Run the relevant image/runtime validation paths and confirm the managed config, Discord contract, and persisted-home migration all match the new spec
- [x] 4.2 Review the final diff against the new OpenSpec artifacts and confirm no retired Codex-channel contract references remain in active runtime docs or tests
