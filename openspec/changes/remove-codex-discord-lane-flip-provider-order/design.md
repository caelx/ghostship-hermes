## Context

The current managed runtime contract is split across multiple layers:

- bootstrap defaults in `packages/hermes-image/build/init_home.py`
- Nix-owned managed config in `packages/hermes-image/nixos-module.nix`
- repo-owned upstream Hermes patching in `packages/hermes-image/build/prepare_upstream_hermes.py`
- smoke and persistence validation
- operator-facing docs and repo memory

Today those layers agree on the wrong behavior for the requested outcome: the main runtime is `opencode-go/minimax-m2.7`, the fallback is `openai-codex/gpt-5.4-mini`, and Discord has a second forced Codex lane keyed by `GHOSTSHIP_CODEX_CHANNEL`.

There is also a migration constraint. The managed home initializer only merges missing defaults into persisted `config.yaml`; it does not replace existing `model`, `fallback_model`, or `agent.reasoning_effort` values. A source-only default flip would therefore leave older persisted homes on the retired provider order unless the managed convergence path explicitly rewrites those repo-owned fields.

## Goals / Non-Goals

**Goals:**
- Remove the managed Discord Codex lane from the runtime contract, patch layer, validation, and docs.
- Make the managed primary model lane `openai-codex/gpt-5.4`.
- Make the managed fallback model lane `opencode-go/minimax-m2.7`.
- Lower the shared managed agent default `reasoning_effort` to `medium`.
- Ensure boot-time convergence migrates persisted managed config away from the retired provider order and reasoning default.
- Keep validation and documentation aligned with the new contract.

**Non-Goals:**
- Removing the local router from the image or from the router-pinned Discord free-response lane.
- Changing the router-pinned Discord alias selection.
- Changing auxiliary Gemini wiring, memory defaults, browser defaults, or the broader workstation persistence contract.
- Solving unrelated in-flight router-provider work such as NVIDIA prioritization.

## Decisions

### Remove the Codex Discord lane at the upstream patch boundary
The repo-owned Hermes patcher should stop recognizing `GHOSTSHIP_CODEX_CHANNEL`, stop forcing a dedicated Codex route, and stop advertising a second forced `/model` pin message. The router-pinned Discord lane remains the only repo-owned forced-channel override.

This keeps the patch surface narrow and matches the requested removal at the only place where Discord message source metadata is converted into hard routing behavior.

Alternative considered: leave the patch in place and simply stop documenting the env. Rejected because it preserves hidden behavior and leaves a dead contract path that operators could still trigger accidentally.

### Treat Codex primary, fallback model, and reasoning default as repo-owned migratable config
The managed config contract should define the following repo-owned values together:

- `model.provider = openai-codex`
- `model.default = gpt-5.4`
- `fallback_model.provider = opencode-go`
- `fallback_model.model = minimax-m2.7`
- `agent.reasoning_effort = medium`

Boot-time convergence should actively rewrite those fields in persisted managed `config.yaml` when they still match or retain the retired managed values. This should happen in the managed reconciliation path, not only in first-boot seed generation.

This is necessary because the initializer merges missing defaults but does not replace existing managed values, so old homes would otherwise silently keep `opencode-go` primary and high reasoning forever.

Alternative considered: rely on operators to delete `config.yaml` or edit it manually. Rejected because the repo already treats these fields as image-owned managed contract and needs deterministic migration for persisted homes.

### Keep router auth and custom-provider scaffolding independent from the fallback flip
Switching fallback away from the router should not remove the existing `ghostship-router` custom provider entry or the internal router auth normalization. The router remains mandatory for the dashboard/runtime contract and for the remaining Discord router-pinned lane.

This avoids coupling the provider-order change to broader router removal or redesign work.

Alternative considered: delete the custom router provider at the same time. Rejected because the user asked to remove the Codex channel and flip primary/fallback order, not to retire router availability.

### Update validation to prove the new primary/fallback order rather than just static config text
Smoke and persistence validation should assert the new managed config shape and continue checking that runtime behavior does not silently drift back to the retired order. Validation should prove:

- managed config now seeds Codex `gpt-5.4` as primary
- managed config now seeds `opencode-go/minimax-m2.7` as fallback
- convergence removes retired managed values from persisted config
- Discord deployment no longer requires or references `GHOSTSHIP_CODEX_CHANNEL`

Alternative considered: limit validation to doc/config assertions. Rejected because this repo has already had contract drift where persisted config kept stale provider wiring despite source defaults changing.

## Risks / Trade-offs

- [Persisted config rewrite is too broad] → Limit convergence rewrites to the repo-owned managed keys and the known retired values instead of clobbering arbitrary user edits.
- [Codex primary depends on persisted OAuth rather than a simple env key] → Keep docs explicit that Codex auth lives in `/home/hermes/.hermes/auth.json` and update validation assumptions accordingly.
- [Active in-flight router-channel work touches nearby files] → Keep this proposal scoped to provider order and Codex-lane removal so implementation can be rebased cleanly against router-lane changes.
- [Operators still set `GHOSTSHIP_CODEX_CHANNEL` out of habit] → Remove it from required env docs/tests and make the gateway ignore it entirely so stale env no longer has behavioral effect.

## Migration Plan

1. Update the managed bootstrap defaults in both `init_home.py` and `nixos-module.nix` to the new primary/fallback order and `medium` reasoning default.
2. Remove the Codex forced-channel branch from the upstream Hermes patcher and keep only the router-pinned Discord override.
3. Extend managed config convergence so persisted managed homes are rewritten away from the retired primary/fallback order and high managed reasoning default.
4. Update the OpenSpec deltas, README, workstation/runtime docs, repo memory, and changelog to remove `GHOSTSHIP_CODEX_CHANNEL` from the supported contract.
5. Update smoke and persistence validation to assert the new primary/fallback config and Discord env inventory.
6. Implement, test, and then verify on a persisted-home upgrade path.

Rollback is straightforward: restore the Codex Discord lane patch and revert the managed primary/fallback/reasoning defaults plus their convergence rules.

## Open Questions

- Should convergence rewrite only exact retired managed values, or always enforce the repo-owned primary/fallback/reasoning fields even if an operator changed them manually in `config.yaml`?
- Should validation include a direct managed Codex invocation proof, or is config-shape plus existing gateway/runtime health coverage sufficient for the first pass?
