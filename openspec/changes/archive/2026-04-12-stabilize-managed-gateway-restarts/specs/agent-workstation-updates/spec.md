## ADDED Requirements

### Requirement: Image validation proves safe managed-state edits do not restart the gateway
The workstation SHALL validate that routine mutable-state updates under the managed Hermes home do not trigger avoidable managed gateway restarts.

#### Scenario: Validation proves auth updates are non-disruptive
- **WHEN** maintainers run the Hermes image validation suite against the managed single-agent image
- **THEN** the suite mutates `/home/hermes/.hermes/auth.json` in a non-destructive test flow
- **AND** the suite verifies that the running `hermes-gateway.service` process identity does not change solely because of that mutation

#### Scenario: Validation proves SOUL edits are non-disruptive
- **WHEN** maintainers run the Hermes image validation suite against the managed single-agent image
- **THEN** the suite mutates `/home/hermes/.hermes/SOUL.md` in a non-destructive test flow
- **AND** the suite verifies that the running `hermes-gateway.service` process identity does not change solely because of that mutation

#### Scenario: Validation still proves actual restart triggers work
- **WHEN** maintainers run the Hermes image validation suite against the managed single-agent image
- **THEN** the suite still verifies restart-visible behavior for managed `.env` or `config.yaml` changes
- **AND** the narrowed non-restart checks do not replace coverage for the intended restart-triggering paths
