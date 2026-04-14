## 1. Runtime And Packaging

- [ ] 1.1 Verify the pinned Hermes release’s actual dashboard CLI contract (`hermes dashboard` vs `hermes web`), required flags, and whether the wrapped Nix package already ships the native web assets and Python web dependencies.
- [ ] 1.2 Rewire the managed browser service to launch the upstream Hermes dashboard process on port `9119` with non-interactive startup behavior (`--no-open` or equivalent), and remove the repo-owned dashboard controller from the service path.
- [ ] 1.3 Remove `packages/hermes-dashboard` from the flake/image/runtime graph and delete the retired custom dashboard, frontend, API, and ttyd browser-proxy code paths once the upstream dashboard path is wired.
- [ ] 1.4 Update image networking and runtime publication to the upstream dashboard port contract, including `EXPOSE`, firewall rules, health checks, runtime env defaults, and any startup wiring that still assumes `7681` or browser-terminal coupling.

## 2. Validation And Tests

- [ ] 2.1 Rewrite the dashboard smoke test to validate the upstream Hermes dashboard root and native operator APIs/pages on port `9119` instead of custom `/api/health`, `/api/profiles`, `/api/projects`, `/api/console`, and `ttyd` behavior.
- [ ] 2.2 Rewrite workstation persistence and live runtime validation to prove the managed runtime through upstream dashboard surfaces plus supporting CLI/service checks, and remove browser-terminal assertions entirely.
- [ ] 2.3 Add or update package/runtime checks so maintainers can prove the wrapped Hermes output includes the native dashboard assets/dependencies and that the managed service launches successfully in-image.
- [ ] 2.4 Run a live validation on `chill-penguin` that exercises broad upstream dashboard functions and proves the deployed dashboard can load and be used inside a cross-origin iframe.

## 3. Docs And Contract Cleanup

- [ ] 3.1 Update `README.md`, `CHANGELOG.md`, and `AGENTS.md` to replace the old `7681` HUDUI/MMX/Console contract with the upstream Hermes dashboard on `9119`, including explicit breaking-change notes for removed browser-terminal behavior.
- [ ] 3.2 Update image/runtime descriptions, base-image split docs, and any package references so the dashboard is described as upstream Hermes runtime content rather than a repo-owned `hermes-dashboard` artifact.
- [ ] 3.3 Remove stale test names, validation notes, and operational guidance that still describe same-origin `ttyd`, `/workspace` Projects, Ghostship dashboard APIs, or the old browser service identity.
