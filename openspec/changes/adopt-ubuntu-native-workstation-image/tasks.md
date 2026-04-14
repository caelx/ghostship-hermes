## 1. Runtime Image Architecture

- [ ] 1.1 Replace the current NixOS-based runtime/image contract with a custom Ubuntu 24.04 workstation image that installs Hermes core under `/opt/hermes`, includes Nix and Node/npm, and runs under `s6`.
- [ ] 1.2 Rework container startup so `s6` supervises the mandatory gateway, dashboard, and router services, and remove the current `systemd --user` and managed bootstrap service assumptions from the container runtime path.
- [ ] 1.3 Set the fixed filesystem/process environment for the workstation image (`HOME`, `HERMES_HOME`, XDG paths, npm prefix, PATH ordering) and default Hermes terminal execution to the local backend inside the container.

## 2. Persistence And Environment Contract

- [ ] 2.1 Replace the current persisted-state contract with `/home/hermes`, `/workspace`, and `/nix`, and remove runtime assumptions that still depend on `/opt/data` or a generated home facade.
- [ ] 2.2 Implement the supported `/nix` persistence flow, including the safe first-use seeding/reuse path that downstream docs will rely on for both named volumes and bind mounts.
- [ ] 2.3 Remove the current bootstrap projection/rewrite of `/home/hermes/.hermes/.env`, and make long-running services consume downstream-owned operator env without repo-owned regeneration of that file.

## 3. Dashboard, Router, And Core Product Deltas

- [ ] 3.1 Replace the repo-owned dashboard package/runtime with the upstream Hermes dashboard on the supported browser port, and delete the retired custom dashboard code path.
- [ ] 3.2 Add the minimal repo-owned dashboard patch that exposes the `Console` tab and the same-origin `ttyd` integration without recreating the old dashboard surface.
- [ ] 3.3 Keep the router mandatory in the final image runtime and preserve the Discord free-channel router-pinning patch in the wrapped Hermes package.

## 4. Tooling Split

- [ ] 4.1 Audit the current baked utility set and move every non-core convenience tool out of the immutable image unless a core boot/runtime call site requires it directly.
- [ ] 4.2 Define and implement the default persisted userland Nix tool set, including the approved extra CLIs that must remain available by default.
- [ ] 4.3 Define and implement the default native-package-manager userland tool set for npm-managed agent CLIs such as `codex`, `gemini-cli`, and `opencode`.

## 5. CI, Validation, And Publication

- [ ] 5.1 Rewrite image smoke tests and live validation to prove the Ubuntu workstation runtime, `s6` services, upstream dashboard plus `Console` tab, router, persisted home, persisted `/nix`, and downstream env contract directly in the built image.
- [ ] 5.2 Update GitHub Actions build and publish workflows to build, validate, and publish the new multi-arch Ubuntu workstation image instead of the current NixOS image contract.
- [ ] 5.3 Update release/runbook guidance so the documented deployment examples, tags, and validation procedures match the new image and persistence model.

## 6. Docs And Contract Cleanup

- [ ] 6.1 Update `README.md`, `CHANGELOG.md`, and `AGENTS.md` to describe the Ubuntu workstation image, the new persistence model, the new env contract, and the upstream dashboard plus `Console` tab.
- [ ] 6.2 Add explicit downstream deployment instructions for persisting `/home/hermes`, persisting `/workspace`, seeding and reusing `/nix`, and supplying operator-facing environment variables through Compose or `docker run`.
- [ ] 6.3 Remove stale docs, examples, and tests that still describe the NixOS/module-managed runtime, generated managed `.env`, the retired custom dashboard, or the old baked utility bundle.
