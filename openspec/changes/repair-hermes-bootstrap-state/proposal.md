## Why

The deployed `ghostship-hermes` image on `chill-penguin` exposed two runtime-state gaps that make validation noisy and operational state misleading: the persisted home-scoped release marker drifted behind the image's authoritative release file, and Hermes gateway health/status files did not consistently reflect the live managed gateway processes. The same investigation also showed intermittent bootstrap runs where managed profiles started without Discord platforms enabled even though the current deployment has valid Discord env and connected bots.

## What Changes

- Sync the persisted home-scoped Hermes release marker from the image's authoritative release file during managed runtime bootstrap so reused `/home/hermes` state reflects the currently booted image version.
- Tighten managed profile bootstrap so supported Discord env remains present in profile `.env` whenever the corresponding container env is available during bootstrap and restart flows.
- Define and implement a stable managed-gateway runtime-state contract for profile gateway marker files so Hermes doctor/status surfaces see the same running state that systemd and process inspection see.
- Preserve existing whole-home persistence behavior and non-host-published dashboard deployment behavior.

## Capabilities

### New Capabilities
- `hermes-runtime-state-markers`: Covers persisted release-marker synchronization and managed gateway marker files that must match the live runtime state used by operator health checks.

### Modified Capabilities
- `hermes-profile-env-contract`: Tighten the managed profile `.env` contract so Discord-related runtime inputs remain visible to bootstrap and managed gateway restart flows when present on the container.

## Impact

- Affected code: [nixos-module.nix](/home/nixos/dev/personal/ghostship-hermes/packages/hermes-image/nixos-module.nix), [runtime.nix](/home/nixos/dev/personal/ghostship-hermes/packages/hermes-image/runtime.nix), and any managed bootstrap/gateway helper paths that own profile env or state-marker generation.
- Affected systems: Hermes image bootstrap, managed profile gateways, Hermes doctor/status observability, and persisted `/home/hermes` runtime metadata.
- Operational impact: makes deployed release/version reporting trustworthy and reduces false-negative gateway health signals during validation and day-2 operations.
