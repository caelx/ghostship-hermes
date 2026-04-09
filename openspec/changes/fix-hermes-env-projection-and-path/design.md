## Context

The current Hermes image already installs the fast-moving user CLIs into persisted user-owned locations under `/home/hermes`, and the live container confirms that `codex`, `gemini`, `opencode`, and `agent-browser` exist under `/home/hermes/.local/bin`. The current profile gateway wrapper and bootstrap script also prepend `/home/hermes/.local/bin`, but that path is not expressed as a consistent default-path contract across every Hermes-user execution path, which creates mismatches between normal service behavior and ad hoc operator invocations such as `podman exec` diagnostics.

The image also treats each managed profile `.env` file as the operator-facing source of truth for profile runtime configuration, but the live bootstrap service does not receive any `DISCORD_*` environment variables because its `PassEnvironment` list only includes `sharedHermesEnvKeys`. The bootstrap writer is already designed to project Discord values into profile `.env`, so the current behavior is not a missing feature in the writer itself; it is a contract break between the container env and the bootstrap unit.

This change is cross-cutting because it touches the Hermes-user PATH contract, the bootstrap projection contract, profile-facing operator configuration, and doctor-visible supported-runtime behavior.

## Goals / Non-Goals

**Goals:**
- Make `/home/hermes/.local/bin` an explicit part of the Hermes user's default command-discovery contract.
- Ensure supported profile-facing env is written into each managed profile `.env`, with Discord included when present on the container.
- Keep profile `.env` as the single operator-facing source of truth for profile-facing configuration instead of relying on hidden service-only env layering.
- Align docs and validation with the actual runtime contract so supported doctor warnings are reduced for the intended Hermes surface.

**Non-Goals:**
- Expanding the supported feature surface to every optional Hermes integration.
- Making unset optional credentials appear in profile `.env` when they are not provided at the container level.
- Redesigning the profile model, gateway topology, or provider choices.
- Replacing the persisted npm tool prefix model with a different packaging strategy.

## Decisions

### Keep `/home/hermes/.local/bin` as the user-facing mutable tool layer and make it part of the default Hermes-user PATH contract

The repo already uses `/home/hermes/.local/bin` for the npm-managed CLIs and expects Hermes to discover them there. The right fix is to codify that location as part of the Hermes-user PATH contract rather than treating it as a special-case wrapper detail.

This preserves the existing mutable tool layout and aligns ad hoc operator commands with the same discovery path that the long-running services already intend to use.

Alternatives considered:
- Move the npm-managed CLIs into the managed Nix profile only.
  Rejected because the current runtime model intentionally separates fast-moving npm tools from the managed Nix profile.
- Leave service wrappers alone and accept that ad hoc Hermes invocations may differ.
  Rejected because it produces misleading doctor results and weakens the documented runtime contract.

### Split env projection into shared profile-facing env and explicit Discord pass-through instead of relying on hidden container env

The bootstrap writer already knows how to emit both shared env keys and the profile-specific Discord mapping. The missing piece is the systemd pass-through contract. The design should therefore extend the bootstrap-visible env list to include the supported Discord inputs and keep the generated profile `.env` as the operator-facing record.

This keeps profile-facing configuration visible, reviewable, and restart-triggering through the existing `.env`-watch path units.

Alternatives considered:
- Inject Discord only into the gateway services at runtime without writing it into profile `.env`.
  Rejected because it breaks the repo’s stated “single source of truth” rule for profile-facing configuration.
- Copy every container environment variable into profile `.env`.
  Rejected because it would over-project infrastructure-only env and make the profile contract noisy and ambiguous.

### Treat supported doctor cleanliness as a consequence of the runtime contract, not as a separate ad hoc fix

The PATH and `.env` fixes should reduce supported doctor warnings because they correct the underlying runtime contract. The design should not special-case doctor itself; it should make supported Hermes runtime discovery and env projection correct, then let doctor reflect that state naturally.

Alternatives considered:
- Patch only the doctor checks or doctor invocation path.
  Rejected because it would hide a real runtime inconsistency instead of fixing it.

## Risks / Trade-offs

- [Risk] Expanding the Hermes-user default PATH could make command precedence less obvious. -> Mitigation: keep `/home/hermes/.local/bin` explicitly ahead of the managed profile bin only for the supported mutable-tool layer, and document that ordering.
- [Risk] Projecting more env into profile `.env` could blur the line between profile-facing config and infrastructure config. -> Mitigation: limit projection to supported profile-facing keys and keep router/boot plumbing outside profile `.env`.
- [Risk] Operators may expect every optional Hermes integration to become doctor-clean after this change. -> Mitigation: keep the docs explicit that only the supported runtime surface is covered, while optional unsupported integrations may still warn.

## Migration Plan

1. Update the Hermes image module so the Hermes-user PATH contract always includes `/home/hermes/.local/bin` for the intended runtime surfaces.
2. Extend the bootstrap unit’s pass-through env contract to include the supported Discord variables alongside the existing shared profile-facing keys.
3. Rebuild or update the image, rerun bootstrap, and let the existing profile restart watchers reload the gateways after `.env` changes.
4. Verify that each managed profile `.env` contains the projected Discord values when present, and that `hermes doctor` no longer reports `codex CLI not found` under the intended runtime PATH.

Rollback:
- Revert the module change and rebuild the image. The prior runtime behavior will return, with Discord remaining container-only and `.local/bin` remaining wrapper-only.

## Open Questions

- Should the explicit pass-through list include other profile-facing env beyond Discord right now, or should this change stay limited to the already-supported documented keys plus Discord?
- Do we want a dedicated validation script assertion for profile `.env` Discord projection, or is extending the existing doctor/runtime smoke coverage sufficient?
