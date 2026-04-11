## MODIFIED Requirements

### Requirement: Managed gateway health reporting matches runtime truth
The workstation SHALL keep operator-facing gateway health output aligned with the actual managed single-agent runtime.

#### Scenario: Healthy managed gateway is reported as running after replacement
- **WHEN** the managed gateway service is active after an image replacement with persisted `/home/hermes`
- **THEN** operator-facing health output reports that gateway as running
- **AND** status output does not regress to a false stopped state because `/home/hermes/.hermes/gateway.pid` is missing while the service is active

#### Scenario: Live validation proves the managed gateway marker contract
- **WHEN** maintainers run the Hermes image validation or live post-deploy validation for the managed image
- **THEN** the validation checks that `ghostship-hermes-gateway.service` is active
- **AND** the validation checks that `/home/hermes/.hermes/gateway.pid` exists while that service is active
- **AND** the validation checks that dashboard or Hermes status surfaces report the managed gateway as present from that marker
