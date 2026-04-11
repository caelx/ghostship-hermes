## 1. Gateway Pidfile Lifecycle

- [ ] 1.1 Inspect the managed gateway launcher, pre-start, and post-stop scripts to identify why `gateway.pid` disappears while `ghostship-hermes-gateway.service` stays active.
- [ ] 1.2 Update the managed gateway lifecycle so `/home/hermes/.hermes/gateway.pid` is written for the active gateway process and stale pidfiles are removed on stop or replacement.

## 2. Status And Validation

- [ ] 2.1 Add or update tests so the dashboard/runtime test surface proves `has_gateway_pid` becomes true for the active managed gateway marker contract.
- [ ] 2.2 Extend image or live validation coverage to assert that `ghostship-hermes-gateway.service` being active also implies `/home/hermes/.hermes/gateway.pid` exists and status surfaces report the gateway as present.

## 3. Rollout Verification

- [ ] 3.1 Publish and deploy the rebuilt image, then verify on `chill-penguin-root2` that `gateway.pid` exists while the managed gateway service is running.
- [ ] 3.2 Re-run dashboard and Hermes health checks after deploy to confirm the false negative is gone and document the result in release notes or changelog entries if needed.
