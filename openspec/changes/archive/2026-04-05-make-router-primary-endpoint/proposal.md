## Why

The image currently ships a local model router, but Hermes profiles still bootstrap around direct upstream model identifiers and the dashboard still treats OpenRouter-specific environment values as the main source of truth. That leaves the deployed container validating the wrong path: the router may be healthy, but Hermes and the dashboard are not yet centered on it.

## What Changes

- Configure the Hermes image runtime to use `ghostship-hermes-router` as the primary OpenAI-compatible model endpoint.
- Set the root Hermes model default to `lightweight`, the `operations` profile default to `heavyweight`, and the `coder` profile default to `coding`.
- Make the managed Hermes profile services depend on the local router being available before they start.
- Replace direct-upstream test assumptions with router-first validation that checks router health, alias discovery, and per-profile model defaults.
- Update the dashboard environment view to report generic model endpoint configuration for any provider and enrich that view with live router data when Hermes is pointed at the local router.

## Capabilities

### New Capabilities
- `router-primary-hermes-runtime`: Defines the image runtime contract where Hermes uses the local router as its primary OpenAI-compatible endpoint and assigns the approved alias defaults for root, `operations`, and `coder`.

### Modified Capabilities
- `mmx-hermes-dashboard`: Expand the dashboard environment contract so it reports generic endpoint and model configuration for every provider shape, while surfacing router aliases and provider health when the local router is in use.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, `packages/hermes-dashboard/src/hermes_dashboard/*`, `tests/hermes-image/profiles-dashboard.sh`, `scripts/validate_workstation_persistence.sh`, and related docs.
- Affected systems: Hermes bootstrap, managed profile gateway services, local router validation, and the browser dashboard environment view.
- Affected runtime contract: root Hermes uses `lightweight`, `operations` uses `heavyweight`, and `coder` uses `coding` through `http://127.0.0.1:8788/v1`.
