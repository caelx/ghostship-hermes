## Context

The Hermes image scaffolds three managed profiles, `assistant`, `operations`, and `supervisor`, and runs one long-lived gateway service per profile. Upstream Hermes webhook support is implemented as a per-gateway HTTP listener, with a default port of `8644` and startup failure on port conflicts. In the current repo shape, enabling webhook support without additional scaffold would cause multiple managed profile gateways to compete for the same socket and would leave webhook secrets unmanaged by the per-profile `.env` contract.

This change touches both the generated profile config surface and the managed bootstrap env projection path. It also affects deployment expectations because the repo will define stable per-profile webhook ports while leaving the corresponding secrets to external secret management.

## Goals / Non-Goals

**Goals:**
- Enable the Hermes webhook adapter on all three managed profiles by default.
- Assign distinct repo-owned webhook ports so all managed profile gateways can run concurrently.
- Define a profile-specific secret env contract that writes the correct `WEBHOOK_SECRET` only into the matching managed profile `.env`.
- Keep secret material out of the repo while making the runtime contract explicit for downstream deployment config.
- Document the resulting per-profile webhook listener contract.

**Non-Goals:**
- Introducing a repo-owned shared webhook fan-out service in front of Hermes.
- Generating, storing, rotating, or validating secret values inside this repo.
- Defining static webhook routes for operators or pre-seeding dynamic webhook subscriptions.
- Changing the current three-profile gateway supervision model.

## Decisions

### Use one webhook listener per managed profile

Each managed profile gateway will run its own webhook listener instead of centralizing inbound webhook handling in a single process.

Rationale:
- This matches the user's intended operating model.
- It preserves the current repo pattern of one long-lived Hermes gateway per managed profile.
- It keeps webhook-triggered sessions naturally bound to the profile that received the request.

Alternative considered: one shared webhook listener for the whole image. Rejected because it would concentrate all inbound webhook flows into a single profile or require an extra routing layer that the current image does not own.

### Fix a stable per-profile port map in repo-owned scaffold

The scaffold will assign:
- `assistant` -> `8644`
- `operations` -> `8645`
- `supervisor` -> `8646`

Rationale:
- Upstream Hermes defaults the webhook adapter to `8644`, so keeping `assistant` on that port minimizes surprise.
- Fixed ports are simpler for documentation, reverse-proxy rules, and downstream deployment config.
- Distinct ports avoid startup conflicts between the three managed gateway services.

Alternative considered: leaving ports entirely deployment-defined. Rejected because webhook enablement is repo-owned here, and enabling it without repo-owned distinct ports would produce an invalid default runtime.

### Project webhook runtime settings through the existing per-profile `.env` contract

Bootstrap will write `WEBHOOK_ENABLED`, `WEBHOOK_PORT`, and `WEBHOOK_SECRET` into each profile's managed `.env`, and the existing `EnvironmentFile` wiring will continue to feed those values to the matching gateway service.

Rationale:
- The repo already treats the managed profile `.env` as the operator-facing source of truth for profile runtime env.
- Upstream Hermes already honors `WEBHOOK_ENABLED`, `WEBHOOK_PORT`, and `WEBHOOK_SECRET`, so env projection is lower risk than inventing a second declarative path.
- This keeps webhook runtime behavior aligned with other profile-facing integrations already projected by bootstrap.

Alternative considered: embedding webhook settings directly in generated `config.yaml`. Rejected because the current image standard is to place profile-facing runtime inputs in the managed `.env`, and the secret specifically should remain external to the repo.

### Use profile-specific source env names for secret import

The repo-owned contract will expect:
- `WEBHOOK_ASSISTANT_SECRET`
- `WEBHOOK_OPERATIONS_SECRET`
- `WEBHOOK_SUPERVISOR_SECRET`

Bootstrap will map each one to that profile's Hermes-facing `WEBHOOK_SECRET`.

Rationale:
- The upstream Hermes webhook adapter consumes one generic `WEBHOOK_SECRET` per process, but this image runs three processes.
- Profile-specific source names let downstream deployment config manage secrets independently without ambiguity.
- The resulting profile `.env` stays Hermes-native while the container-level secret inputs stay deployment-safe.

Alternative considered: sharing one secret across all profiles. Rejected because the requested deployment model requires profile-local listener isolation and separate secret material.

## Risks / Trade-offs

- [Three listeners require external ingress coordination] -> Mitigate by documenting the fixed port map and making the repo-owned defaults stable.
- [Missing profile-specific secrets could leave a listener enabled but unusable for real webhook traffic] -> Mitigate by documenting that downstream deployment must provide all three secret env vars and by omitting unset secrets rather than inventing placeholders.
- [Dynamic webhook subscriptions may still be shared at the Hermes home level] -> Mitigate by documenting that this change scaffolds listeners and env wiring, not per-profile subscription-store isolation.
- [Future changes to the managed profile `.env` writer could drift from the webhook contract] -> Mitigate by extending the existing env-contract spec rather than treating webhook projection as an undocumented implementation detail.

## Migration Plan

1. Extend the managed profile scaffold with webhook enablement, fixed per-profile ports, and profile-specific secret source env names.
2. Update bootstrap `.env` generation so each managed profile receives `WEBHOOK_ENABLED=true`, its assigned `WEBHOOK_PORT`, and a projected `WEBHOOK_SECRET` when the matching source env is present.
3. Update README/runtime docs to describe the fixed per-profile webhook listener contract and external secret requirements.
4. Roll out matching deployment-side secret configuration in `nixos-config`.

Rollback:
- Disable the scaffolded webhook env projection and rebuild the image.
- Because the change is repo-owned bootstrap output rather than a persistent migration, reverting the scaffold removes the managed webhook listener contract on the next bootstrap.

## Open Questions

- None for the repo-owned scaffold itself; the remaining work is downstream deployment wiring in `nixos-config`.
