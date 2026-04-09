## Context

The current image already has the right high-level structure for this fix: bootstrap owns managed profile creation and `.env` generation, `/etc/ghostship-hermes-release` is the authoritative image-scoped release marker, and each managed profile gateway runs through a repo-owned wrapper script under systemd. The deployed `chill-penguin` image showed that these pieces are close but not fully aligned in persisted state: the authoritative release file and the persisted home marker diverged, and Hermes status surfaces did not consistently see a `gateway.pid` file even when the managed gateway process was live.

The investigation also showed that Discord itself is not currently broken. The current boot connected all three bots successfully, so the design should focus on deterministic runtime-state ownership rather than replacing the Discord integration path. The existing profile `.env` contract should remain the operator-facing configuration surface.

## Goals / Non-Goals

**Goals:**
- Make the persisted home release marker match the currently booted image release on every managed boot.
- Keep managed profile `.env` generation deterministic so current Discord env remains projected into each profile when present on the container.
- Make `gateway.pid` reliable for the three managed profile gateways so Hermes doctor/status sees the same liveness that systemd sees.
- Preserve the current whole-home persistence model and existing router/dashboard/profile startup graph.

**Non-Goals:**
- Change the named-profile model/provider scaffold away from the current `openai-codex/gpt-5.4` contract.
- Publish the dashboard on the host or change the non-host-exposed deployment posture.
- Rework upstream Hermes gateway internals beyond the minimum repo-owned wrapper/state handling needed for stable health markers.

## Decisions

### Keep bootstrap as the single writer for persisted static runtime metadata
Bootstrap already refreshes managed profile config and `.env` files. The persisted home release marker should be treated the same way: copy the authoritative image release from `/etc/ghostship-hermes-release` into `/home/hermes/.ghostship-hermes-release` during managed bootstrap every boot.

Why this approach:
- It matches the existing ownership boundary for persisted runtime scaffolding.
- It repairs stale persisted home state without introducing a second background sync path.
- It keeps `/etc/ghostship-hermes-release` as the immutable source of truth and `/home/hermes/.ghostship-hermes-release` as the operator-visible persisted mirror.

Alternative considered: only write the home marker on first boot. Rejected because it preserves exactly the stale-version drift we saw on reused `/home/hermes`.

### Keep profile `.env` as the only operator-facing gateway env surface
The existing contract in `hermes-profile-env-contract` is correct: Discord and other profile-facing env should stay in each profile `.env`, and the managed systemd units should continue loading that file through `EnvironmentFile`.

Why this approach:
- It preserves the documented operator workflow.
- It keeps the restart path watchers on `.env` meaningful.
- It avoids hiding live configuration in service-only overrides that users cannot inspect.

Alternative considered: inject Discord env directly into systemd units while leaving `.env` best-effort. Rejected because it would make the visible `.env` file diverge from the effective runtime configuration.

### Make the repo-owned gateway wrapper own `gateway.pid`
Hermes doctor/status uses `gateway.pid` as a primary liveness signal, but the deployed runtime showed inconsistent `gateway.pid` creation even while the actual profile gateway processes were alive. The managed systemd wrapper should write the current process PID into the profile `gateway.pid` path before `exec`-ing Hermes, and the service lifecycle should clear stale pidfiles before start and after stop.

Why this approach:
- The wrapper is already repo-owned and profile-specific.
- Writing the PID before `exec` keeps the pidfile aligned with the long-running Hermes gateway process ID.
- Pre/post cleanup avoids stale files from earlier runs and removes dependence on upstream marker behavior.

Alternative considered: rely entirely on upstream Hermes to manage `gateway.pid`. Rejected because the deployed image already demonstrated that the upstream behavior is not reliable enough for this repo's managed-health expectations.

### Treat `gateway_state.json` as informational and `gateway.pid` as the liveness contract
The current runtime already produces `gateway_state.json`, but the user-facing health problem came from missing `gateway.pid`. The repo should continue to preserve `gateway_state.json` for detail, while making `gateway.pid` the managed liveness contract that must always match the live systemd-owned process.

Why this approach:
- It aligns with the repo's existing durable lesson that Hermes doctor/status trusts `gateway.pid`.
- It minimizes change surface by fixing the file that actually drives health reporting.

Alternative considered: patch all health consumers to ignore `gateway.pid` and trust `gateway_state.json` or process tables instead. Rejected because it broadens the change and fights existing upstream/CLI expectations.

## Risks / Trade-offs

- [Bootstrap rewrites persisted metadata on every boot] → Limit the rewrite to repo-owned files (`.ghostship-hermes-release` and managed profile `.env`) and keep user-managed files untouched.
- [Wrapper-owned pidfiles can still be stale after abnormal termination] → Clear pidfiles in service pre/post hooks and overwrite them on every managed restart.
- [Manual, non-systemd gateway invocations may still produce different logs or state files] → Scope the fix to the managed image services and document that health guarantees apply to the Nix-managed gateways.

## Migration Plan

1. Update the image module so bootstrap refreshes `/home/hermes/.ghostship-hermes-release` from `/etc/ghostship-hermes-release`.
2. Update the managed profile gateway service/wrapper lifecycle to clean and rewrite `gateway.pid`.
3. Rebuild and deploy the image.
4. On the next boot, verify the persisted home release marker matches the image release and all three profiles expose a live `gateway.pid`.
5. Confirm `hermes doctor` and per-profile gateway status no longer report false negatives for the managed gateways.

## Open Questions

- None for proposal scope. The runtime evidence is sufficient to implement the repo-owned state fixes without changing the higher-level Hermes profile or Discord model.
