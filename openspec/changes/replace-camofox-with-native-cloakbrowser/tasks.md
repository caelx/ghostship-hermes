## 1. Native CloakBrowser Runtime

- [x] 1.1 Add image-native CloakBrowser installation to the Hermes image build for the supported architectures.
- [x] 1.2 Wire stock `agent-browser` to launch the native CloakBrowser executable through image-owned runtime settings instead of the retired browser service path.
- [x] 1.3 Define one supported persisted browser profile root under `/home/hermes` and ensure boot/runtime preparation preserves it across restart and container replacement.

## 2. Remove Retired Browser Surfaces

- [x] 2.1 Delete the Camofox runtime stack, including build-time cache/bootstrap logic, service definitions, nginx proxy wiring, and any runtime env or state preparation that exists only for Camofox.
- [x] 2.2 Delete the repo-owned Browser live-view dashboard patch and keep the supported dashboard patch set limited to the `Terminal` entry.
- [x] 2.3 Remove the `ghostship-cloakbrowser` package, tests, and all repo references that treat CloakBrowser Manager as a supported workstation surface.

## 3. Runtime Contract And Validation

- [x] 3.1 Update the managed runtime/home-state wiring so the supported local browser contract no longer depends on `CAMOFOX_URL`, `CLOAKBROWSER_URL`, or `CLOAKBROWSER_TOKEN`.
- [x] 3.2 Replace Camofox- and manager-specific smoke coverage with a non-destructive native browser smoke that proves stock `agent-browser` can launch CloakBrowser on the final image.
- [x] 3.3 Extend restart and full-container-replacement validation to prove the supported browser profile state persists from `/home/hermes`.

## 4. Spec And Contract Cleanup

- [x] 4.1 Align image/runtime tests, fixtures, and helper scripts with the new OpenSpec browser contract and remove references to retired Camofox helpers and endpoints.
- [x] 4.2 Remove or rewrite API/runtime docs that currently describe Camofox services, `/camofox/` dashboard paths, or `ghostship-cloakbrowser`.
- [x] 4.3 Update AGENTS durable lessons so the repo memory reflects the native CloakBrowser plus persistent-profile contract and the removal of Camofox/manager layers.

## 5. Documentation And Release Hygiene

- [x] 5.1 Update `README.md` and the relevant runtime/deployment docs to describe the supported native CloakBrowser-backed Hermes browser path and its persistence model.
- [x] 5.2 Update `CHANGELOG.md` with the browser-contract replacement and the removal of the retired browser surfaces.
- [x] 5.3 Run the relevant test/validation commands and capture that the native local browser path, terminal path, and persistence contract all pass on the final image.
- [x] 5.4 Manually validate the native browser contract on `chill-penguin`, including native browser launch and persistence of `/home/hermes/.local/state/cloakbrowser` across restart or full container recreation.
