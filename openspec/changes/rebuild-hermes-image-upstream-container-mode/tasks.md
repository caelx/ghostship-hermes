## 1. Minimal Upstream-Aligned Spike

- [x] 1.1 Create a throwaway minimal Hermes container build path that does not reuse the current Ghostship runtime bootstrap, workstation seed, skill seed, update timers, or profile reconciler code.
- [x] 1.2 Add the smallest declarative Hermes config needed to boot the container successfully with the upstream-aligned `/data` contract and a dedicated `hermes` user at `3000:3000`.
- [x] 1.3 Boot the minimal container and verify that Hermes gateway starts successfully and the container reaches a usable runtime state.
- [x] 1.4 Inspect and document the runtime environment from the minimal container, including `HERMES_HOME`, `HOME`, UID/GID, actual write paths under `/data` and `/home/hermes`, and any upstream assumptions that affect the final rebuild.

## 2. Persistence Contract Validation

- [x] 2.1 Implement the rebuilt persistence layout around `/data`, `/data/home`, `/workspace`, and `/nix`, with `/home/hermes` acting as a thin facade over the persisted home state.
- [x] 2.2 Persist the needed top-level HOME-backed directories, at minimum `~/.config`, `~/.local`, and `~/.cache`, then add only the additional top-level agent/tool roots justified by the runtime spike and operator home audit.
- [x] 2.3 Validate that reused `/data` and `/workspace` mounts restore Hermes state, HOME-backed state, and work products across container replacement.
- [x] 2.4 Validate that persisted `/nix` preserves user-level `nix profile install` results across container replacement and that the installed binaries remain usable to the runtime user.
- [x] 2.5 Install `opencode` in the validation environment, run it long enough to create its active XDG-backed config/state/cache under `~/.config/opencode`, `~/.local/share/opencode`, `~/.local/state/opencode`, and `~/.cache/opencode`, replace the container, and verify that both the install and the resulting persisted config/state survive.
- [x] 2.6 Use the current operator home as a reference set and verify that agent-specific persisted directories such as `~/.agents` are preserved by the rebuilt home-facade contract.
- [x] 2.7 Verify comprehensive browser-and-agent persistence using the operator home as a reference set, with subpath checks used only to prove that the required top-level directories are sufficient.
- [x] 2.8 Verify that persisted later-installed tool roots remain updateable by upgrading a test-installed tool and confirming the runtime does not overwrite the newer persisted code on the next boot.

## 3. Runtime Rebuild

- [x] 3.1 Rework the flake and image wiring so the image is centered on upstream Hermes Nix/container-mode semantics and canonical `/data` paths.
- [x] 3.2 Remove the old Ghostship workstation runtime layer, including the custom shell runtime, honcho compatibility logic, workstation seed tree, profile reconciler, and app/asset refresh services.
- [x] 3.3 Reduce the default image package set to the lean retained inventory: upstream Hermes requirements, runtime Nix support, the minimal dashboard/terminal stack, and all `ghostship-*` utilities.
- [x] 3.4 Ensure the rebuilt runtime consistently uses the dedicated `hermes` identity at UID/GID `3000:3000` and that persisted mounts remain writable without a custom identity rewrite layer.

## 4. Minimal Dashboard And Terminal Surface

- [x] 4.1 Replace the current profile-aware dashboard with a minimal static browser entrypoint that only exposes the supported terminal access path.
- [x] 4.2 Implement on-demand ephemeral `ttyd` session launch and teardown from the dashboard and remove the persistent per-profile `ttyd` service model.
- [x] 4.3 Verify that the rebuilt dashboard comes up without the legacy profile reconciler architecture and still provides a working browser terminal flow.

## 5. Remove Custom Skills And Legacy Extras

- [x] 5.1 Remove all custom default skill payloads from the image runtime, including Ghostship-managed local skills and vendored Google Workspace skills, while leaving Hermes built-in skills untouched.
- [x] 5.2 Remove Ghostship-managed app/tool extras from the default image, including Codex, Gemini CLI, Opencode, OpenSpec, `skills`, `gws`, `bws`, and `feed`.
- [x] 5.3 Delete or simplify the code, assets, and wiring that only existed to support the removed custom skills, vendored skills, or workstation app/update flows.

## 6. Verification, Docs, And Cleanup

- [x] 6.1 Update README, CHANGELOG, AGENTS guidance, and any other affected docs to describe the new upstream-aligned `/data` runtime, lean package set, broad HOME persistence, and minimal dashboard behavior.
- [x] 6.2 Replace or rewrite image-level tests so they verify the new runtime contract: `/data` paths, `3000:3000` identity, no custom default skills, minimal dashboard behavior, and persisted `nix profile install`.
- [x] 6.3 Run the relevant build and runtime validation commands for the rebuilt image, leave a final validated container running and ready for manual dashboard inspection, and clean up any temporary images, containers, or test artifacts created during verification.
