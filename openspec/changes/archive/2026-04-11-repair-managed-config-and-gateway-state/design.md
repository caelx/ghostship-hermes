## Context

The managed Hermes image changed from a router-primary contract to a direct `opencode-go/minimax-m2.7` primary lane with router `agentic` fallback. The live host still retains the old repo-owned `model.base_url = http://127.0.0.1:8788/v1` in `/home/hermes/.hermes/config.yaml`, and Hermes runtime resolution intentionally reuses that key for API-key providers when the configured provider matches. As a result, the supposed direct primary lane is silently routed back into the local router until fallback rescues the request.

The same image family still diverges from Hermes’ expected gateway topology. Repo-managed runtime services currently use a system unit that runs as `hermes`, and the wrapper patches Hermes CLI to pretend that repo-owned system-unit contract is the supported gateway model. Upstream Hermes already has a complete Linux user-service flow around `systemd --user` `hermes-gateway.service`, linger, and status/control behavior. The live container already has a running Hermes user manager (`/run/user/3000`, user bus, `systemctl --user` works), so the remaining gap is our repo wiring rather than container feasibility.

## Goals / Non-Goals

**Goals:**
- Reconcile repo-owned managed config on boot so stale contract keys do not survive image replacement.
- Remove stale router-primary `model.base_url` from the root managed config when the current image contract uses direct `opencode-go` primary.
- Move the managed gateway onto the upstream-style Hermes user service `hermes-gateway.service` while keeping the container boot contract reliable.
- Make Hermes operator-facing gateway status and control flows use upstream `systemctl --user` semantics instead of the Ghostship-specific system-unit shim.
- Extend validation so maintainers prove the direct primary lane actually works without fallback masking the bug.

**Non-Goals:**
- Rework the full Hermes config merge model or take ownership of every on-disk user-edited key.
- Change the direct primary provider or fallback model contract again.
- Reintroduce a fleet of named-profile gateway services; the target remains one managed root agent and one upstream-style user gateway service.

## Decisions

### Managed config convergence will remove only retired repo-owned keys
The bootstrap/convergence path will treat a small set of image-owned config fields as migratable contract state and will prune them when the current image no longer owns them. For this change, that specifically means removing `model.base_url` when the current managed contract sets `model.provider = opencode-go` and uses router fallback through `fallback_model` instead.

This is narrower than fully rewriting `config.yaml`, which would risk deleting legitimate operator-owned settings. It is broader than leaving config untouched, which is what caused the primary-lane breakage.

### The migration will run in the repo-owned managed bootstrap path
The repo already converges `.env`, `SOUL.md`, skills, and other managed state during boot. The stale-key cleanup belongs in the same managed bootstrap path so image replacement with persisted `/home/hermes` repairs old config automatically before services rely on it.

Doing this only in tests or by one-off manual cleanup would not solve the persistent-volume drift that caused the live bug.

### The gateway will align to upstream `hermes-gateway.service`
The managed gateway should be supervised by the Hermes user manager instead of a root/system unit that impersonates the user. The image should ensure the Hermes user manager is available during boot, install or materialize the gateway as `systemd --user` `hermes-gateway.service`, and let Hermes’ normal Linux gateway status/control behavior work against that unit.

That means the repo should stop steering operators toward `ghostship-hermes-gateway.service` and should remove or minimize the wrapper patch that currently overrides upstream gateway behavior with Ghostship-specific system-unit guidance.

### Boot must still be deterministic in a container without interactive login
Using a user service inside the container means the image must explicitly guarantee the Hermes user manager exists during boot and across replacement. The design can rely on repo-owned boot wiring for the Hermes user manager, but it should not require a shell login to make `hermes-gateway.service` available.

### Validation must prove direct primary execution and truthful user-service state
A successful Hermes response is not enough because fallback can hide a broken primary. Likewise, a running gateway process is not enough if Hermes still reports the wrong service state. Validation must prove the direct primary path works and that Hermes gateway/status surfaces agree with the live `systemctl --user` `hermes-gateway.service` state.

## Risks / Trade-offs

- [Managed config cleanup removes a user-owned setting] -> Limit migration to a narrowly defined repo-owned stale key and gate it on the current managed contract.
- [User service does not start reliably in the container] -> Use the existing Hermes user-manager capability already present in the container and validate cold boot plus restart behavior on the live image.
- [Wrapper removal exposes more upstream assumptions than expected] -> Prefer reverting to upstream behavior incrementally and keep only the smallest repo-specific patch surface that remains necessary.
- [Validation still passes via fallback or stale status output] -> Add assertions that prove primary execution and user-service status directly instead of inferring health from a successful reply.

## Migration Plan

1. Update managed bootstrap/config convergence to remove the stale router-primary `model.base_url` from root managed config when the direct `opencode-go` contract is active.
2. Move the managed gateway unit and restart wiring onto the Hermes user manager as upstream `hermes-gateway.service`.
3. Remove or reduce the Ghostship-specific wrapper patch so Hermes gateway status/control uses upstream user-service behavior wherever possible.
4. Extend image validation to prove primary-lane execution and truthful managed gateway state through the user-service topology.
5. Publish the image, deploy it onto persisted `/home/hermes`, and verify that the migrated config no longer contains `model.base_url` and that Hermes gateway/status surfaces report `hermes-gateway.service` correctly.

## Open Questions

- Whether any wrapper patch is still needed after the gateway moves to upstream `hermes-gateway.service`, or whether the right answer is to delete the gateway override entirely.
- What the smallest repo-owned watcher/restart mechanism is for config/env/auth/SOUL changes once the gateway lives purely under `systemd --user`.
