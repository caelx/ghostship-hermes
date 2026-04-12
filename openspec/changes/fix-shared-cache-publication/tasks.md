## 1. Repair Cache Publication

- [x] 1.1 Patch the shared-cache helper integration so `cache-index` updates no longer pass large JSON payloads through shell arguments and large cache-refresh runs can complete successfully.
- [x] 1.2 Keep shared-cache publication fail-open for image publication while surfacing clear log output when cache upload or index update fails.

## 2. Keep Cache Consumption Fast

- [x] 2.1 Update shared-cache bootstrap and proxy wiring so the public cache path remains the normal fast path and authenticated registry access is available as fallback when needed.
- [x] 2.2 Remove or simplify redundant cache-side publish probes that add workflow roundtrips without materially improving correctness.

## 3. Prove Reuse Manually

- [ ] 3.1 Run a manual cache-refresh `workflow_dispatch` from the implementation branch and confirm that cache publication finishes with a consumable `cache-index`.
- [ ] 3.2 Run an unchanged follow-up `workflow_dispatch` from the same branch and confirm shared-cache bootstrap succeeds before `nix build`.
- [ ] 3.3 Compare the seeded and repeat run logs to verify meaningful warm-cache reuse without adding new workflow proof steps.
