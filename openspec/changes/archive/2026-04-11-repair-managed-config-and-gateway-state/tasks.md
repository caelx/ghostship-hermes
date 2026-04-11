## 1. Managed Config Convergence

- [x] 1.1 Update the managed bootstrap/convergence path to remove the retired router-primary `model.base_url` from the root managed config when the direct `opencode-go` contract is active.
- [x] 1.2 Add validation that image replacement with persisted `/home/hermes` no longer leaves the stale router-primary key in `/home/hermes/.hermes/config.yaml`.

## 2. Upstream Hermes User-Service Gateway

- [x] 2.1 Replace the repo-owned system gateway unit with upstream-style `systemd --user` `hermes-gateway.service` and add the boot wiring needed for the Hermes user manager in the container.
- [x] 2.2 Remove or reduce the Ghostship-specific gateway wrapper shim so `hermes gateway status/start/stop/restart` follow upstream user-service behavior.
- [x] 2.3 Update tests, docs, and runtime assertions to stop referring to `ghostship-hermes-gateway.service` and instead validate `systemctl --user` `hermes-gateway.service`.

## 3. Runtime Proof And Rollout Validation

- [x] 3.1 Extend image validation so a Hermes invocation proves direct `opencode-go/minimax-m2.7` primary execution rather than fallback-only success.
- [ ] 3.2 Publish and deploy the rebuilt image, then revalidate on the live host that the stale `model.base_url` is gone and the managed gateway user-service state surfaces report `hermes-gateway.service` correctly.
