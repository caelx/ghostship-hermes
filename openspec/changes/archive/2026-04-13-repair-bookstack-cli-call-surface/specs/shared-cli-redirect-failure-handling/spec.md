## ADDED Requirements

### Requirement: Shared HTTP clients SHALL treat unexpected redirects as failures by default
The shared `ghostship-*` HTTP transport SHALL classify non-followed redirect responses as HTTP failures unless a client explicitly enables redirect following.

#### Scenario: Redirect response raises an HTTP status error
- **WHEN** a shared client receives a `3xx` response while `follow_redirects` is disabled
- **THEN** the request path SHALL raise an HTTP status error that preserves the redirect status code and response details
- **AND** decode helpers SHALL not treat that response as a successful payload

#### Scenario: Clients can still opt into redirect following explicitly
- **WHEN** a service client is configured with `follow_redirects=True`
- **THEN** the shared transport SHALL continue the redirect chain before classifying the final response
- **AND** only the final non-redirect response SHALL be decoded or returned to the caller

### Requirement: Empty-body success envelopes SHALL only represent successful upstream statuses
The shared decode helpers SHALL emit `{"status": "success"}` for empty responses only when the upstream status is in the successful `2xx` range.

#### Scenario: Empty redirect responses are not collapsed into success
- **WHEN** an upstream service returns an empty-body redirect such as an auth-gateway `302`
- **THEN** the shared client SHALL report that redirect as a failure
- **AND** the CLI SHALL not emit an empty-body success envelope that masks the routing or auth problem
