## ADDED Requirements

### Requirement: Live Hermes image validation SHALL cover every shipped ghostship CLI
The repo SHALL define a repeatable live validation pass for every `ghostship-*` CLI shipped in the Hermes image.

#### Scenario: Each shipped CLI receives a boot or help probe
- **WHEN** operators validate a deployed Hermes image
- **THEN** every shipped `ghostship-*` binary SHALL be exercised with a non-destructive boot/help probe
- **AND** the validation output SHALL record whether the CLI exposed an operator-facing command surface successfully

#### Scenario: Service CLIs receive a safe live read-only command
- **WHEN** a shipped `ghostship-*` binary is a service API CLI with sufficient runtime configuration present
- **THEN** the live validation pass SHALL run one safe read-only command against the configured service
- **AND** the result SHALL distinguish a healthy service call from a CLI or contract failure

### Requirement: Live CLI audit results SHALL classify failures by cause
The live audit SHALL classify failures so remediation work targets the right layer.

#### Scenario: Failure report distinguishes code defects from runtime conditions
- **WHEN** a live CLI smoke check fails
- **THEN** the audit result SHALL classify the failure as a CLI/code defect, runtime configuration gap, upstream/known service condition, or probe mismatch
- **AND** the resulting change tasks SHALL only require code fixes for failures that are attributable to the repo-owned implementation or wrapper surface
