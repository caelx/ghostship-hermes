## Context

The live `chill-penguin` deployment exposed a split runtime state after image replacement. The container booted with newer image-layer state expected by the repo, including the profile-local `.managed` markers added for managed gateway detection, but the interactive `hermes` binary still resolved from the persisted managed user profile under `/home/hermes/.local/state/nix/profiles/ghostship-managed`.

That managed profile still contained `hermes-agent-wrapped` from commit `ee7003b`, which predates `36fd79d fix(hermes-image): align managed gateway status`. Because the service and shell PATH order prefer the managed profile bin directory ahead of the baked system layer, the older profile-installed wrapper shadowed the newer image-baked wrapper. The result was a mixed runtime:

- bootstrap/runtime state from the newer image
- interactive Hermes CLI behavior from the older persisted wrapper

That is why the managed profile services and `gateway.pid` files were healthy while `hermes -p <profile> gateway status` and `hermes doctor` still reported false negatives.

The same class of problem can also affect repo-owned managed profile scaffold/config stored in the persisted user layer. Discord auto-threading is a current example: the repo now wants auto-thread creation disabled for all managed profiles, and that expectation should converge through the same persisted-state contract rather than remaining stuck behind older scaffolded config.

## Goals / Non-Goals

**Goals:**

- Ensure repo-managed persisted user-layer system state used after boot converges to the current image/runtime generation rather than stale persisted revisions.
- Ensure the interactive `hermes` binary used after boot converges to the current image/runtime generation rather than a stale persisted wrapper.
- Preserve the repo's mutable managed profile model for approved user-facing tooling while treating the Hermes wrapper as a compatibility-critical component that must stay aligned with the booted image.
- Ensure repo-owned managed profile scaffold values that are meant to track the current image, including Discord auto-thread defaults, also converge predictably across replacement.
- Add validation that proves image replacement updates the active Hermes wrapper generation and preserves correct managed gateway/doctor behavior.

**Non-Goals:**

- Removing the managed user tooling profile entirely.
- Reverting to a fully immutable runtime with no persisted user-facing tool updates.
- Reworking unrelated runtime tooling such as the npm-managed CLIs beyond whatever is necessary to keep Hermes wrapper convergence correct.
- Changing the optional provider/tool warnings that are unrelated to the managed wrapper split-brain.

## Decisions

### 1. Treat repo-managed persisted system state as a converged runtime surface

The current bug was exposed through `hermes-agent-wrapped`, but the broader issue is that repo-owned persisted system state can outlive the image generation that is supposed to define it. The runtime should explicitly distinguish between:

- operator-owned mutable state that must persist untouched
- repo-owned managed state in the user layer that must converge to the current image/runtime contract

Alternative considered: continue treating all persisted user-layer content as equally authoritative once it exists. Rejected because it lets repo-managed runtime behavior and config drift away from the booted image indefinitely.

### 2. Treat `hermes-agent-wrapped` as a converged runtime component, not a missing-only bootstrap dependency

The current `ghostship-hermes-user-tooling` boot path runs in `bootstrap` mode, which only installs missing managed profile entries. That is sufficient for additive tools, but it is not sufficient for the Hermes wrapper because stale persisted versions can shadow newer baked runtime behavior indefinitely.

The runtime should explicitly converge the managed profile's `hermes-agent-wrapped` entry to the expected current ref or store path during the boot/update path that already owns user-tooling reconciliation.

Alternative considered: rely on operators to run a separate manual refresh command after image replacement. Rejected because the bug manifests during normal unattended rollouts and leaves the active runtime in a misleading state until someone intervenes.

### 3. Keep the managed profile bin path first, but make its Hermes package deterministic

The repo intentionally uses the managed profile as the normal invocation source for `hermes` and related user-facing tools. Changing PATH precedence to bypass the managed profile would fight that design and create a second, ambiguous Hermes resolution path.

Instead, the managed profile should continue to win on PATH, but the Hermes package inside that profile must be updated to the expected current wrapper generation whenever the image/runtime contract changes.

Alternative considered: reorder PATH so the system-layer Hermes wins over the managed profile. Rejected because it would make the managed profile partially authoritative for some tools and not others, which is a different kind of drift.

### 4. Converge repo-owned Discord scaffold defaults through bootstrap

Discord auto-thread creation should be disabled for all managed profiles in the repo-owned scaffold. Because these profile config files live under persisted `/home/hermes`, the change must be treated as part of the same convergence contract: a newly booted image should not leave older repo-owned Discord defaults in place just because the home volume already exists.

Alternative considered: treat Discord scaffold changes as a one-off manual cleanup. Rejected because it repeats the same split-brain failure mode in config form instead of CLI-wrapper form.

### 5. Make convergence verifiable through revision-aware validation

The existing validation focused on service health and gateway-status behavior, but it did not prove that the active `hermes` executable came from the expected wrapper generation after replacement. The validation should assert both:

- the resolved `hermes` path for the Hermes user
- the managed gateway and doctor behavior that depends on that wrapper
- the managed profile scaffold/config values that are expected to track the current image, including Discord auto-thread defaults

Alternative considered: validate only output behavior and ignore binary provenance. Rejected because the root cause here is precisely that the wrong binary won on PATH despite the rest of the image being updated.

## Risks / Trade-offs

- [Risk] Forcing wrapper convergence at boot could slow startup or add network sensitivity if it always reaches GitHub. → Mitigation: converge only the Hermes wrapper entry and prefer deterministic refs/upgrade paths over broad profile churn.
- [Risk] Updating repo-managed persisted state automatically may surprise operators who expect all user-layer content to remain untouched. → Mitigation: scope convergence explicitly to repo-owned runtime components and scaffolded config, not operator-authored content.
- [Risk] Duplicate profile entries or stale references may accumulate in the managed profile during repeated refreshes. → Mitigation: normalize the Hermes wrapper entry as part of convergence and validate the resulting profile state.
- [Risk] Config convergence could overwrite operator edits if the ownership boundary is unclear. → Mitigation: apply convergence only to repo-owned managed settings whose source of truth is the image/bootstrap contract.

## Migration Plan

1. Update the managed user tooling/bootstrap convergence path so repo-owned persisted system state, including the Hermes wrapper and Discord scaffold defaults, is reconciled to the current runtime generation.
2. Validate locally that image replacement updates the active `hermes` resolution to the current wrapper generation and disables Discord auto-threading in the managed profile scaffold.
3. Re-run live validation against a persisted-home deployment and confirm `gateway status` and `doctor` match the healthy managed services after replacement while the profile Discord config reflects the new defaults.
4. Roll back by restoring the previous bootstrap-only behavior if the convergence path causes unacceptable startup regressions.

## Open Questions

- Should the convergence path pin the managed profile's Hermes wrapper to the baked store path from the image build, or continue using the repo flake ref and force a refresh to the current commit?
- Should startup normalize duplicate `hermes-agent-wrapped` entries in the managed profile as part of the same change, or leave that as cleanup once the active resolution issue is fixed?
- Which persisted config surfaces besides the Hermes wrapper and Discord scaffold should be treated as explicitly repo-owned convergence targets in this pass?
