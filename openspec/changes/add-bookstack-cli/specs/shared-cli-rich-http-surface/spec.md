## ADDED Requirements

### Requirement: Shared full-surface CLI pattern supports multipart request bodies
The shared `ghostship-*` full-surface CLI contract SHALL support multipart form requests as a first-class request type for utilities that need file uploads or mixed field/file payloads.

#### Scenario: Generic operation commands can express multipart fields and files
- **WHEN** a full-surface utility operation requires multipart form submission
- **THEN** the shared CLI layer provides a supported way to pass form fields and file inputs through operation commands and generic request commands
- **AND** utilities do not need to invent service-specific transport conventions for the same multipart behavior

#### Scenario: Dry-run output remains safe and inspectable for multipart requests
- **WHEN** an operator uses `--dry-run` on a multipart-capable write or delete command
- **THEN** the rendered request JSON shows form fields, filenames, and content types needed to inspect the request
- **AND** the dry-run output does not inline raw file bytes

### Requirement: Shared full-surface CLI pattern supports non-JSON response handling
The shared `ghostship-*` full-surface CLI contract SHALL support operations whose successful upstream response is not JSON.

#### Scenario: Binary-success endpoints avoid forced JSON decoding
- **WHEN** a utility operation is declared to return binary or other non-JSON content on success
- **THEN** the shared client path bypasses JSON decoding for that response
- **AND** the utility can surface the result through explicit binary-output handling instead of treating it as a decode error

#### Scenario: JSON-first CLI output contract remains intact
- **WHEN** a binary-capable command completes successfully
- **THEN** the command still emits JSON metadata by default about the transfer action, output path, or response characteristics
- **AND** existing JSON-returning commands continue to behave as they did before the shared transport extension

### Requirement: Shared transport extensions are additive for existing utilities
The richer multipart and binary handling SHALL be introduced without regressing current `ghostship-*` utilities that only use JSON or form-encoded request/response flows.

#### Scenario: Existing JSON-oriented utilities do not need behavior changes
- **WHEN** maintainers run existing JSON-oriented utility tests after the shared transport change
- **THEN** those utilities continue to pass without requiring service-specific migration work
- **AND** the new shared helpers remain opt-in for packages that need the richer HTTP surface
