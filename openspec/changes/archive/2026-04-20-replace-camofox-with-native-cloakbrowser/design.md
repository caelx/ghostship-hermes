## Context

The current workstation image has two separate browser-specific layers that sit outside the actual Hermes local-browser contract:

- a Camofox service stack with a local HTTP shim, dedicated cache/bootstrap handling, and VNC/noVNC sidecars that drive a repo-owned Browser page inside the dashboard
- a separate `ghostship-cloakbrowser` CLI package that wraps CloakBrowser Manager as another supported browser surface

Neither layer matches the actual product target. The desired supported workflow is the upstream Hermes local browser path: Hermes invokes `agent-browser`, `agent-browser` launches a Chromium-compatible browser, and browser state persists in Hermes home across restart and image replacement. The repo already treats the upstream Hermes dashboard plus a small `Terminal` patch as the supported browser UI surface, so keeping a second repo-owned Browser live-view path adds complexity without satisfying a required contract.

This is a cross-cutting change. It affects image build inputs, runtime environment ownership, dashboard patching, smoke tests, live validation, docs, and the supported browser contract exposed to downstream operators.

## Goals / Non-Goals

**Goals:**
- Replace the Camofox runtime path with image-native CloakBrowser used through stock `agent-browser`.
- Keep one persistent Chrome-style profile rooted in persisted Hermes home state so local browser sessions retain state across restart and container replacement.
- Remove the repo-owned `ghostship-cloakbrowser` CLI and the CloakBrowser Manager API from the supported workstation contract.
- Remove the custom Browser live-view iframe and `/camofox/` proxy path so the only required Ghostship dashboard patch remains the `Terminal` entry.
- Prove the new browser contract in image validation and deployment docs.

**Non-Goals:**
- Adding a new browser dashboard surface, remote browser control plane, or a replacement for the removed live-view iframe.
- Supporting multiple managed browser profiles, profile switching, or browser-manager APIs.
- Reworking Hermes upstream browser behavior beyond the minimum image/runtime wiring needed to launch CloakBrowser through `agent-browser`.
- Preserving compatibility with Camofox-specific helpers, health endpoints, cache layouts, or manager-oriented browser workflows.

## Decisions

### Use direct `agent-browser` launch with the CloakBrowser binary

The supported local browser path will be:

```text
Hermes browser tools
  -> agent-browser
    -> image-installed CloakBrowser binary
      -> persistent profile under /home/hermes
```

The image will install CloakBrowser natively and wire `agent-browser` to it through image-owned execution settings such as the browser executable path and the CloakBrowser stealth/default args. Hermes continues using its stock local Chromium browser mode instead of talking to a repo-owned browser HTTP service.

Rationale:
- matches Hermes' documented local-browser path most closely
- avoids carrying a second daemon, port, or manager process for the supported path
- lets CloakBrowser appear as the effective local Chrome/Chromium executable for Hermes
- keeps the integration surface small and testable

Alternatives considered:
- Keep a long-lived CloakBrowser daemon and connect through CDP. Rejected because it recreates a custom sidecar service contract and adds a browser-port lifecycle the product does not need.
- Keep Camofox for dashboard live view and add CloakBrowser separately for automation. Rejected because it preserves the complexity this change is meant to remove.
- Keep CloakBrowser Manager as the supported interface. Rejected because the user goal is a persistent local Chrome profile, not a manager API.

### Persist exactly one browser profile in Hermes home

The image will keep a single persisted browser profile path under `/home/hermes` and treat that path as part of the workstation persistence contract. The browser state will survive restart and full container replacement alongside the rest of Hermes home state.

Rationale:
- directly satisfies the product goal
- avoids profile-management UX and migration complexity
- fits the existing workstation contract that persisted user state lives under `/home/hermes`

Alternatives considered:
- Multiple named profiles. Rejected as out of scope and unnecessary.
- Stateless ephemeral browser sessions. Rejected because it breaks the desired login/session persistence.
- Persist profile data outside `/home/hermes`. Rejected because it fragments the user-owned state contract.

### Remove repo-owned Browser live view and treat Browser automation as a non-dashboard concern

The repo-owned Browser page patch and `/camofox/` nginx proxy route will be removed. The supported Ghostship dashboard delta returns to the minimal `Terminal` entry only. Browser automation remains available through Hermes native browser tools rather than through a repo-owned iframe live view.

Rationale:
- aligns the dashboard with the documented upstream-Hermes-plus-Terminal contract
- removes VNC/noVNC services that are no longer needed
- avoids inventing a second UI contract for a feature the user does not need

Alternatives considered:
- Build a new CloakBrowser live-view page. Rejected because it would replace one repo-owned browser UI customization with another.
- Leave a broken or placeholder Browser entry. Rejected because it weakens the published contract and validation story.

### Remove operator-facing browser-manager env and CLI surface

The workstation will stop advertising `ghostship-cloakbrowser`, `CLOAKBROWSER_URL`, `CLOAKBROWSER_TOKEN`, and Camofox-specific browser env as supported runtime surfaces. The local browser path becomes image-owned rather than downstream-configured.

Rationale:
- narrows the operator-facing contract to the actual supported path
- removes env and docs that imply unsupported manager/service integrations
- reduces drift between runtime behavior and documented surface area

Alternatives considered:
- Keep the manager CLI as an optional extra. Rejected because it would continue to expand the supported contract beyond the stated goal.

## Risks / Trade-offs

- [Risk] Upstream Hermes local browser behavior may still have edge cases around headed persistence or browser cleanup.  
  Mitigation: keep the design on the stock `agent-browser` execution path, validate persistent profile behavior directly in the image smoke suite, and avoid adding a repo-owned daemon layer that would mask upstream behavior.

- [Risk] CloakBrowser installation and runtime wiring may differ across `amd64` and `arm64`.  
  Mitigation: make architecture support an explicit build concern in the implementation tasks and require publication validation on the final multi-arch image path.

- [Risk] Removing the Browser iframe may surprise operators who used it informally.  
  Mitigation: document the supported browser contract clearly and keep the dashboard patch set intentionally minimal.

- [Risk] Old docs and tests may leave behind references to Camofox paths or the removed CLI.  
  Mitigation: include explicit cleanup tasks for docs, tests, changelog, and AGENTS memory.

- [Risk] Persisted homes may contain stale Camofox or manager artifacts after upgrade.  
  Mitigation: treat them as retired state, avoid depending on them at boot, and keep the new persistent profile path explicit and self-contained.

## Migration Plan

1. Add native CloakBrowser installation and runtime wiring in the image build.
2. Define the single persisted browser profile path under `/home/hermes` and make `agent-browser` use CloakBrowser through image-owned execution settings.
3. Remove the Camofox services, nginx proxy path, cache/bootstrap code, dashboard Browser page patch, and Camofox-specific smoke checks.
4. Remove the `ghostship-cloakbrowser` package, tests, docs, and runtime references.
5. Update OpenSpec deltas, image validation, and operator docs to describe only the native CloakBrowser-backed Hermes path.
6. Validate restart and full container replacement with the persistent browser profile preserved.

Rollback:
- Restore the previous image generation with the Camofox services and dashboard patch if native CloakBrowser launch cannot satisfy the supported Hermes browser contract on both target architectures.
- Because this change narrows the supported contract, rollback is image-based rather than data-migration-heavy.

## Open Questions

- What is the exact native installation path for CloakBrowser in the image on both supported architectures, and does it require build-time prefetching or first-run download?
- Which `agent-browser` execution settings must be image-owned for reliable CloakBrowser launch in Hermes without introducing a downstream browser env contract?
