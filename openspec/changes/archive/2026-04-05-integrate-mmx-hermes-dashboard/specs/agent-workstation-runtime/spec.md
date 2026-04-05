## MODIFIED Requirements

### Requirement: Systemd runtime preserves the custom dashboard services
The workstation SHALL run the packaged MMX Ghostship Hermes dashboard under the image-managed `systemd` runtime.

#### Scenario: Dashboard services still come up under systemd
- **WHEN** the workstation boots under the current image runtime contract
- **THEN** the system-level dashboard service starts under `systemd`
- **AND** that service reaches the packaged `hermes-dashboard` entrypoint through the image runtime path
- **AND** the browser-facing MMX dashboard remains available through the supported runtime path
- **AND** the runtime does not depend on a deleted repo-local dashboard asset tree or on pre-generated per-profile terminal services to make the dashboard available
