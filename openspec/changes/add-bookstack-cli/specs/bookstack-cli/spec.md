## ADDED Requirements

### Requirement: BookStack utility exposes the full upstream REST API surface
The repo SHALL provide a `ghostship-bookstack` utility that covers the full verified upstream BookStack REST API contract through operation-aligned client methods and CLI commands.

#### Scenario: Every verified BookStack operation has a corresponding command
- **WHEN** maintainers compare the committed BookStack API reference against the `ghostship-bookstack` operation catalog
- **THEN** every verified upstream BookStack REST API operation is represented by one snake_case CLI command and one matching client method
- **AND** the utility also exposes a generic `request` escape hatch for temporary upstream drift or debugging

#### Scenario: Command names stay aligned with upstream operations
- **WHEN** the BookStack utility exposes commands for pages, books, shelves, attachments, comments, image gallery, imports, roles, users, search, system, recycle bin, and related endpoint groups
- **THEN** command names remain operation-aligned instead of introducing repo-specific compatibility aliases
- **AND** the command surface stays consistent with the repo-wide `ghostship-*` utility contract

### Requirement: BookStack utility uses the official token auth contract
The `ghostship-bookstack` utility SHALL authenticate with BookStack's official API token format and SHALL document the required runtime environment variables.

#### Scenario: Token auth header is built from runtime configuration
- **WHEN** an operator invokes `ghostship-bookstack` against a BookStack instance
- **THEN** the client sends `Authorization: Token <token_id>:<token_secret>` using repo-documented environment variables
- **AND** the utility fails with a config error when the required BookStack URL or token material is missing

### Requirement: BookStack API docs are committed as repo-owned reference material
The repo SHALL capture the verified BookStack API contract under `docs/api/` so the utility surface is reviewed against a committed upstream snapshot instead of a live-only docs page.

#### Scenario: Repo contains canonical BookStack API reference artifacts
- **WHEN** maintainers inspect the BookStack utility documentation
- **THEN** `docs/api/bookstack.md` exists as the canonical repo-owned reference sheet
- **AND** the repo also contains the captured upstream docs artifact or normalized machine-readable snapshot used to derive the operation inventory
- **AND** the reference records the source quality and capture origin

### Requirement: BookStack utility supports upload operations required by the upstream API
The `ghostship-bookstack` utility SHALL support BookStack operations that require multipart form uploads, including attachment, image, and import workflows.

#### Scenario: Attachment or image upload operations can be expressed through the CLI
- **WHEN** an operator invokes a BookStack create or update command that includes an uploaded file
- **THEN** the CLI can represent multipart fields and file payloads without requiring ad hoc local patches
- **AND** dry-run output shows the intended multipart request structure without embedding raw file bytes

#### Scenario: Import creation supports ZIP upload semantics
- **WHEN** an operator invokes the BookStack import-create workflow for a compatible ZIP archive
- **THEN** the client sends a multipart upload request that matches the verified upstream import contract
- **AND** the resulting command remains part of the standard `ghostship-bookstack` surface rather than a one-off helper script

### Requirement: BookStack utility supports binary-content endpoints
The `ghostship-bookstack` utility SHALL cover BookStack endpoints that return binary content, including exports and image-data fetches.

#### Scenario: Export endpoints remain part of the supported utility surface
- **WHEN** an operator invokes a page, chapter, or book export command for HTML, PDF, plain text, Markdown, or ZIP output
- **THEN** the utility handles the non-JSON response successfully
- **AND** the command reports JSON metadata about the transfer result in a way consistent with the repo's JSON-first CLI contract

#### Scenario: Image-data endpoints can fetch raw image content
- **WHEN** an operator invokes a BookStack image data command
- **THEN** the utility can retrieve the binary payload from the verified upstream endpoint
- **AND** the client does not route that response through JSON decoding paths that would corrupt or reject valid content
