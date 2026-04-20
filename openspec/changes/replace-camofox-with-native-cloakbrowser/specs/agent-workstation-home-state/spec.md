## ADDED Requirements

### Requirement: One supported browser profile persists inside `/home/hermes`
The workstation SHALL keep exactly one supported local-browser profile rooted at `/home/hermes/.local/state/cloakbrowser` so Hermes local browser sessions retain normal Chrome-style profile state across restart and container replacement.

#### Scenario: Runtime contract defines one persisted browser profile root
- **WHEN** maintainers inspect the runtime docs or container contract for the supported local browser path
- **THEN** the contract identifies `/home/hermes/.local/state/cloakbrowser` as the one documented browser profile root
- **AND** the supported path does not require additional persisted browser state mounts outside `/home/hermes`

#### Scenario: Reused persisted home restores browser profile state
- **WHEN** a new container starts with the same persisted `/home/hermes`
- **THEN** the supported local browser path sees the previously persisted browser profile state from `/home/hermes/.local/state/cloakbrowser`
- **AND** the operator does not need to reinitialize the supported profile solely because the container image was replaced
