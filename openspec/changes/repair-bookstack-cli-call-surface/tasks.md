## 1. Repair BookStack command dispatch

- [ ] 1.1 Update the BookStack client request and request-response paths so they follow the shared `BaseHttpClient` parameter contract.
- [ ] 1.2 Fix the `ghostship-bookstack request` and `ghostship-bookstack docs_display` command paths to execute successfully with the real client.
- [ ] 1.3 Review other BookStack response kinds to ensure typed JSON, text, and binary operations all route through the intended client helpers.

## 2. Tighten shared HTTP response classification

- [ ] 2.1 Update the shared HTTP transport to treat unexpected `3xx` responses as failures when redirect following is disabled.
- [ ] 2.2 Ensure empty-body success envelopes are emitted only for successful `2xx` upstream responses.
- [ ] 2.3 Confirm any clients that intentionally need redirect following still work through explicit configuration.

## 3. Add regression coverage and validation guidance

- [ ] 3.1 Add BookStack CLI tests for a typed JSON command, the generic `request` command, and `docs_display`.
- [ ] 3.2 Add shared contract tests for redirect classification and empty-body redirect handling.
- [ ] 3.3 Update BookStack runtime documentation or smoke-validation notes to describe the supported API origin topology and post-fix validation steps.
- [ ] 3.4 Run the touched package test and build workflows, then revalidate the deployed Hermes image against the repaired BookStack call surface.
