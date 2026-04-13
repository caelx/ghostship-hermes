## Context

The initial change targeted the BookStack call surface after live validation showed that typed JSON operations worked while `ghostship-bookstack request` and `docs_display` failed. A broader live audit of the deployed Hermes image on `chill-penguin` now shows that the BookStack defect is real but not unique enough to justify a one-utility-only proposal shape.

The current live fleet picture is:
- safe read-only smoke calls succeeded for Bazarr, BookStack typed reads, changedetection.io, Chaptarr, CloakBrowser, FlareSolverr, Grimmory, n8n, NZBGet, Plex, PriceBuddy, Prowlarr, qBittorrent, Radarr, RomM, RSS-Bridge, SearXNG, Sonarr, Synology, and Tautulli
- `ghostship-bookstack request GET /books` still fails with the BookStack client signature mismatch
- `ghostship-hermes-router --help` starts the router process, attempts to bind `127.0.0.1:8788`, and times out instead of displaying usage
- `ghostship-hermes-runtime --help` returns usage text but behaves like a thin wrapper rather than a normal help surface
- `ghostship-pyload-ng get_server_status` fails with `401 Invalid API credentials`, matching an already documented service-side caveat that still needs explicit classification in the live audit

This means the repo needs both targeted code fixes and a durable validation contract for the CLI fleet.

## Goals / Non-Goals

**Goals:**
- Keep the BookStack call-surface repair in scope.
- Add a repeatable live validation matrix for every `ghostship-*` CLI shipped in the Hermes image.
- Classify live failures into implementation defects, runtime configuration gaps, wrapper ergonomics issues, and known upstream service conditions.
- Repair any confirmed code defects uncovered by the fleet audit, starting with BookStack passthrough/text paths and router help behavior.
- Capture the audit methodology in repo docs or change notes so future image validation is consistent.

**Non-Goals:**
- Build a full remote integration harness for every upstream service.
- Treat every runtime credential problem as a code defect without first validating the configured auth contract.
- Rename the current change or split it into multiple concurrent proposals.

## Decisions

### Use a two-stage live audit for every shipped CLI
Each installed CLI will be checked with:
1. a boot/help probe to verify that the binary starts and exposes an operator-facing surface
2. one safe live read-only command where the runtime provides enough configuration to do so

This catches both import/bootstrap defects and real API-path failures without mutating external services.

Alternative considered: only running `--help` across the fleet. Rejected because BookStack proved that a CLI can load fine while its live call surface is still broken.

### Separate implementation defects from runtime/service failures
The audit output will explicitly categorize failures as:
- CLI/code defect
- runtime configuration gap
- upstream/known service condition
- probe mismatch requiring a better read-only command

This prevents the repo from overfitting code changes to issues such as missing pyLoad API auth while still surfacing those failures to operators.

Alternative considered: treating every non-zero smoke result as a CLI bug. Rejected because several services have known auth or deployment caveats that are not fixable in the client package alone.

### Extend the current change instead of opening a second proposal
The BookStack repair remains part of the work, and the new fleet audit findings build directly on that initial validation. Keeping one change avoids splitting related validation and remediation work across multiple branches and OpenSpec records.

### Bring runtime wrapper help behavior under the same operator contract
`ghostship-hermes-router --help` currently behaves like a server launch and collides with the running router port. Wrapper-style binaries that ship in the image need an explicit operator-facing help contract so they can be audited consistently with the API CLIs.

## Risks / Trade-offs

- [Fleet validation increases change scope and implementation time] → Mitigation: keep the audit non-destructive, focus first on confirmed failures, and leave service-side auth anomalies classified when they are not repo code bugs.
- [Some live smoke commands may be poor probes for generated full-surface CLIs] → Mitigation: document the chosen safe commands and adjust the matrix when a better read-only endpoint exists, as with Chaptarr `get_api_v1_system_status` replacing `get_ping`.
- [Wrapper help fixes may touch startup code paths] → Mitigation: keep wrapper changes isolated to argument parsing and verify they do not alter the normal service entrypoint behavior.
- [Remote validation depends on the currently deployed image revision] → Mitigation: use the live audit to shape the proposal now, and repeat the same matrix after redeploy to confirm remediation.

## Migration Plan

1. Preserve the in-flight BookStack and shared transport fixes already implemented locally.
2. Add a documented live CLI smoke matrix covering every shipped `ghostship-*` command.
3. Repair confirmed code defects uncovered by the matrix.
4. Re-run the full matrix against a redeployed image built from this branch.
5. Document any remaining known service-side failures that are not addressed by repo code.

## Open Questions

- Should the fleet smoke matrix live as a checked-in script after this change, or remain a documented operator workflow?
- Is `ghostship-pyload-ng` failing because the runtime lacks valid API credentials, or because the client is using the wrong auth contract for the deployed pyLoad variant?
- Should runtime wrappers like `ghostship-hermes-runtime` support a richer `--help` UX than the current usage-only output?
