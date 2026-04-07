## 1. API Contract Snapshot And Docs

- [ ] 1.1 Download and bundle the official n8n public API spec into a committed repo mirror at `docs/api/n8n-openapi.json`, recording the upstream version and source path
- [ ] 1.2 Write `docs/api/n8n.md` with auth, pagination, endpoint-group coverage, configurable public API path/version behavior, and command inventory notes
- [ ] 1.3 Update `docs/api/README.md`, the top-level README, and the changelog to include `ghostship-n8n` and its documentation source of truth

## 2. Package Scaffold And Core Client

- [ ] 2.1 Create `packages/n8n-cli` on the shared `ghostship-cli-contract` pattern with repo-standard build, test, and packaging files
- [ ] 2.2 Implement environment-driven config and auth for `N8N_URL`, `N8N_API_KEY`, and optional public API path/version overrides
- [ ] 2.3 Implement shared request/response plumbing for JSON-first output, pagination cursors, empty responses, and mutation dry-run rendering

## 3. Full Public API Command Coverage

- [ ] 3.1 Inventory the mirrored n8n public API operations and map each one to a dedicated typed client method and snake_case CLI command
- [ ] 3.2 Implement command coverage for discover, audit, credentials, workflows, executions, and tags endpoints
- [ ] 3.3 Implement command coverage for users, variables, data tables, projects, source control, and community packages endpoints
- [ ] 3.4 Add a generic `request` escape hatch without reducing the dedicated command coverage of the mirrored public API contract

## 4. Wiring And Verification

- [ ] 4.1 Expose `ghostship-n8n` in flake packages and include it in the Hermes image runtime path
- [ ] 4.2 Add tests that verify client and CLI coverage against the mirrored OpenAPI snapshot, plus auth and pagination behavior
- [ ] 4.3 Run package build/test flows and repo evaluation to confirm `ghostship-n8n` is packaged, documented, and available in the Hermes runtime
