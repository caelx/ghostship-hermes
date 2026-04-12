## Why

Live validation on `chill-penguin` shows that `ghostship-bookstack` only partially satisfies the intended API-surface contract. Typed JSON operations now work against the deployed BookStack service, but the generic `request` escape hatch and text-response paths still fail, and the shared HTTP layer can silently treat redirect-based auth failures as success.

## What Changes

- Repair the BookStack client call surface so generic passthrough requests and text-response operations use the shared transport contract correctly.
- Tighten shared HTTP response handling so non-followed redirects and other unexpected success-like responses are surfaced as actionable errors instead of empty-body `{"status": "success"}` payloads.
- Add regression coverage for typed JSON commands, the generic `request` command, text-response commands such as `docs_display`, and redirect/error classification in the shared client layer.
- Document and validate the supported runtime topology for BookStack so live checks confirm the utility is pointed at a reachable API origin instead of an auth gateway.

## Capabilities

### New Capabilities
- `bookstack-cli-call-surface`: Validates and repairs the shipped BookStack command and client paths across typed, passthrough, and text-response operations.
- `shared-cli-redirect-failure-handling`: Defines shared transport behavior for redirect responses and other non-JSON success ambiguities that should be reported as failures.

### Modified Capabilities
- None.

## Impact

- Affected code: `packages/bookstack-cli`, `packages/ghostship-cli-contract`, and their tests.
- Affected runtime behavior: `ghostship-bookstack request`, `ghostship-bookstack docs_display`, and any utility path that currently misclassifies redirect responses.
- Affected validation: local package tests plus BookStack live smoke checks against the deployed Hermes image.
