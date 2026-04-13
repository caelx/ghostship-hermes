## 1. Repair BookStack command dispatch

- [x] 1.1 Update the BookStack client request and request-response paths so they follow the shared `BaseHttpClient` parameter contract.
- [x] 1.2 Fix the `ghostship-bookstack request` and `ghostship-bookstack docs_display` command paths to execute successfully with the real client.
- [x] 1.3 Review other BookStack response kinds to ensure typed JSON, text, and binary operations all route through the intended client helpers.

## 2. Tighten shared HTTP response classification

- [x] 2.1 Update the shared HTTP transport to treat unexpected `3xx` responses as failures when redirect following is disabled.
- [x] 2.2 Ensure empty-body success envelopes are emitted only for successful `2xx` upstream responses.
- [x] 2.3 Confirm any clients that intentionally need redirect following still work through explicit configuration.

## 3. Add regression coverage and validation guidance

- [x] 3.1 Add BookStack CLI tests for a typed JSON command, the generic `request` command, and `docs_display`.
- [x] 3.2 Add shared contract tests for redirect classification and empty-body redirect handling.
- [x] 3.3 Update BookStack runtime documentation or smoke-validation notes to describe the supported API origin topology and post-fix validation steps.
- [ ] 3.4 Run the touched package test and build workflows, then revalidate the deployed Hermes image against the repaired BookStack call surface.

## 4. Audit The Live CLI Fleet

- [x] 4.1 Record the shipped `ghostship-*` CLI inventory from the live Hermes image and choose one safe smoke command for each service CLI.
- [x] 4.2 Run the live smoke matrix against `chill-penguin` and capture pass/fail results for every shipped CLI.
- [x] 4.3 Classify each failure as a code defect, runtime configuration gap, upstream/known service condition, or probe mismatch.

## 5. Repair Additional Audit Findings

- [ ] 5.1 Fix repo-owned CLI defects uncovered by the fleet audit, including runtime wrapper help behavior where needed.
- [ ] 5.2 Document known runtime/service failures that are not fixed in code, including the evidence and expected operator impact.
- [ ] 5.3 Re-run the full live CLI matrix against a redeployed image and confirm the remaining failure set matches the documented expectations.
