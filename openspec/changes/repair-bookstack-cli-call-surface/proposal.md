## Why

Live validation on `chill-penguin` shows that the deployed `ghostship-*` CLI fleet is mostly healthy, but the current proposal is scoped too narrowly around BookStack alone. The repo now needs a fleet-level live CLI audit contract so broken passthrough paths, wrapper ergonomics, and runtime/config failures are identified systematically instead of one utility at a time.

## What Changes

- Expand the change from a BookStack-only call-surface repair into a live audit and remediation pass across every `ghostship-*` CLI shipped in the Hermes image.
- Keep the existing BookStack fixes in scope, specifically the broken `request` passthrough and text-response path.
- Add a live validation matrix for the deployed utility fleet so each installed CLI is checked with a safe boot/help probe and, where applicable, one read-only runtime call.
- Distinguish implementation defects from runtime configuration gaps and known upstream service conditions in the resulting remediation work.
- Repair additional CLI surfaces that fail the live audit, including non-service wrappers that do not honor standard help/usage behavior.

## Capabilities

### New Capabilities
- `bookstack-cli-call-surface`: Validates and repairs the shipped BookStack command and client paths across typed, passthrough, and text-response operations.
- `shared-cli-redirect-failure-handling`: Defines shared transport behavior for redirect responses and other non-JSON success ambiguities that should be reported as failures.
- `live-cli-fleet-validation`: Defines the live Hermes-image audit surface for every shipped `ghostship-*` CLI and requires failure classification between code defects and runtime/service conditions.
- `runtime-wrapper-help-surface`: Defines expected operator-facing help/usage behavior for repo-owned runtime wrapper binaries such as `ghostship-hermes-router` and `ghostship-hermes-runtime`.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/bookstack-cli`, `packages/ghostship-cli-contract`, runtime wrapper entrypoints, and any additional CLI packages implicated by the live audit.
- Affected validation: local package tests plus a live smoke matrix against the deployed Hermes image on `chill-penguin`.
- Current live findings that shape this proposal:
  - `ghostship-bookstack request GET /books` still fails in the deployed image.
  - `ghostship-hermes-router --help` starts the server and collides with the bound router port instead of printing help.
  - `ghostship-pyload-ng get_server_status` returns `401 Invalid API credentials`, which must be classified as either runtime config debt or a client/auth bug.
  - Most other service CLIs passed a safe live read-only smoke call.
