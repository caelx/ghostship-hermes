## Context

The managed single-agent image currently uses a user-level path unit to restart `hermes-gateway.service` when files under `/home/hermes/.hermes` change. The implementation watches `config.yaml`, `.env`, `auth.json`, and `SOUL.md`, and the docs repeat that broader watch list.

That behavior is too eager for the current runtime contract. The managed gateway reads its operator-facing env from `/home/hermes/.hermes/.env` and its declarative runtime config from `/home/hermes/.hermes/config.yaml`, but `auth.json` is runtime OAuth state and `SOUL.md` is persisted prompt content. Both files are expected to change during normal operation or operator tuning, and bouncing the gateway for those changes creates avoidable interruption without improving correctness.

The repo already has a narrower spec story around `.env`: canonical specs describe `.env` as the watched restart surface, and the bootstrap writer is explicitly idempotent so unchanged env does not cause pointless restarts. The source code, validation, and docs need to converge on that narrower contract and prove that routine mutable-state updates do not destabilize the image.

## Goals / Non-Goals

**Goals:**
- Restrict managed gateway restart triggers to file changes that are actually part of live gateway reload behavior.
- Make the watched-file contract explicit in spec and docs for the single-agent image.
- Preserve restart behavior for managed `.env` and managed config updates.
- Add image validation that proves `auth.json` and `SOUL.md` changes do not restart the managed gateway.
- Keep bootstrap idempotence and restart visibility aligned so the image does not flap services during normal convergence or runtime mutations.

**Non-Goals:**
- Redesign the managed gateway service topology.
- Change where `auth.json` or `SOUL.md` live in the managed runtime.
- Introduce live reload for `SOUL.md` or auth state without restart.
- Rework unrelated dashboard, router, or publication behavior beyond the validation and docs needed for restart stability.

## Decisions

### 1. Treat `config.yaml` and `.env` as the only managed restart triggers
The user-level restart path should watch only `/home/hermes/.hermes/config.yaml` and `/home/hermes/.hermes/.env`.

Rationale:
- Those files are the managed gateway's declarative runtime inputs.
- `.env` is already the documented `EnvironmentFile` surface and is rewritten idempotently.
- `config.yaml` is the other managed file whose changes are expected to affect gateway startup behavior.

Alternatives considered:
- Keep watching `auth.json` and `SOUL.md`. Rejected because those files are mutable runtime state, not the intended service-control surface, and normal edits should not disrupt conversations.
- Watch only `.env`. Rejected because the repo still owns managed config convergence in `config.yaml`, so removing config-triggered restarts would leave a real runtime input outside the restart contract.

### 2. Classify `auth.json` and `SOUL.md` as stable managed state, not restart signals
The managed runtime contract should explicitly treat OAuth state and seeded/live prompt content as persistent files that survive boot, refresh, and edits without automatically restarting the gateway.

Rationale:
- `auth.json` may change due to OAuth login or token refresh.
- `SOUL.md` is intentionally operator- or agent-editable after seed convergence.
- Treating these files as non-restarting reduces avoidable service churn while preserving their durable-state role.

Alternatives considered:
- Add content-aware restart logic for parts of `auth.json` or `SOUL.md`. Rejected because it adds fragility and complexity without a clear runtime need.

### 3. Stabilize the image with explicit negative validation
The validation suite should not only prove that restart-triggering files still restart the gateway; it should also prove that safe file mutations do not.

Rationale:
- The current drift happened because the broader watch set was never pinned down by a contract test.
- Negative validation around `auth.json` and `SOUL.md` directly protects the intended runtime behavior.

Alternatives considered:
- Rely on docs/spec review alone. Rejected because the repo already drifted between spec, docs, and implementation.

### 4. Align docs and changelog with the narrowed restart surface
Operator-facing docs and release notes should describe the exact managed restart triggers and call out the stability improvement.

Rationale:
- The current README matches the overly broad implementation instead of the intended contract.
- This repo relies on runtime docs for live validation and operator debugging, so ambiguity here causes repeated confusion.

## Risks / Trade-offs

- [Some runtime path unexpectedly needs restart after `auth.json` changes] -> Mitigation: keep the change scoped to managed restart wiring, add validation around supported auth flows, and leave room to reintroduce a targeted explicit restart if a concrete case appears.
- [Prompt edits no longer take effect in a long-running gateway until a later restart] -> Mitigation: document that `SOUL.md` is durable runtime state but not an automatic restart trigger; explicit restart remains available when an operator wants prompt changes applied immediately.
- [Validation becomes flaky if restart detection relies on timing alone] -> Mitigation: compare stable gateway pid/service identity before and after each mutation and use bounded waits rather than fragile sleeps.
- [Docs/spec drift again later] -> Mitigation: couple the contract change with both delta specs and image-level validation so future drift is easier to detect.

## Migration Plan

1. Update the managed gateway restart path unit so it watches only `config.yaml` and `.env`.
2. Adjust the image validation flow to assert that `.env` and `config.yaml` still trigger restart-visible behavior.
3. Add negative validation that `auth.json` and `SOUL.md` mutations preserve the running gateway process.
4. Update README and changelog entries so the published single-agent contract describes the narrowed restart surface.
5. Rebuild and validate the image. Rollback is straightforward: restore the previous watch list if a concrete runtime dependency is discovered, though the expected steady-state contract is the narrower watch set.

## Open Questions

- Whether operators want an explicit documented note that `SOUL.md` edits require a manual gateway restart if they need immediate effect during an already-running session.
- Whether Hermes runtime behavior around `auth.json` refresh needs a dedicated smoke test beyond “no restart occurred” in the image suite.
