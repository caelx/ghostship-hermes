## ADDED Requirements

### Requirement: Managed gateway restart surface is limited to live runtime inputs
The Hermes image SHALL restart the managed single-agent gateway only for changes to managed files that are part of the gateway's live runtime input surface.

#### Scenario: Managed env changes trigger gateway restart behavior
- **WHEN** `/home/hermes/.hermes/.env` changes with different effective runtime content
- **THEN** the managed restart unit observes that file change
- **AND** the managed gateway restart flow is triggered for the running `hermes-gateway.service`

#### Scenario: Managed config changes trigger gateway restart behavior
- **WHEN** `/home/hermes/.hermes/config.yaml` changes
- **THEN** the managed restart unit observes that file change
- **AND** the managed gateway restart flow is triggered for the running `hermes-gateway.service`

### Requirement: Managed gateway ignores non-runtime mutable state
The Hermes image SHALL NOT treat managed OAuth state or managed prompt content as automatic restart triggers for the single-agent gateway.

#### Scenario: Auth state changes do not trigger managed gateway restart
- **WHEN** `/home/hermes/.hermes/auth.json` changes during a managed runtime session
- **THEN** the managed restart unit does not trigger a gateway restart solely because of that file change
- **AND** the running managed gateway process remains in place unless a separate restart-triggering change occurs

#### Scenario: Prompt changes do not trigger managed gateway restart
- **WHEN** `/home/hermes/.hermes/SOUL.md` changes during a managed runtime session
- **THEN** the managed restart unit does not trigger a gateway restart solely because of that file change
- **AND** the running managed gateway process remains in place unless a separate restart-triggering change occurs
