## 1. Workflow Execution Model

- [x] 1.1 Update `.github/workflows/publish-image.yml` so `x86_64-linux` and `aarch64-linux` image artifacts build on execution environments that can run each target system's Nix derivations.
- [x] 1.2 Remove workflow assumptions that Docker QEMU or Nix `extra-platforms` alone make x86-hosted arm64 image builds valid for this release path.
- [x] 1.3 Keep artifact names and publish-stage inputs stable so GHCR publication still assembles the same amd64, arm64, and manifest tags after both builds succeed.

## 2. Validation Boundaries

- [x] 2.1 Review `.github/workflows/ci.yml` and related validation helpers to keep x86-host arm64 checks at evaluation-only scope unless an arm64-capable builder is present.
- [x] 2.2 Add or update workflow comments and maintainer-facing guidance so the repo clearly distinguishes arm64 derivation evaluation from full arm64 image artifact production.

## 3. Documentation And Release Guidance

- [x] 3.1 Update `README.md` to document the arm64 publication requirement and the x86-host `nix eval` validation fallback.
- [x] 3.2 Update `CHANGELOG.md` and any affected maintainer guidance to record the corrected multi-arch image publication contract.

## 4. Verification

- [x] 4.1 Validate the updated workflow structure and confirm the publish job still consumes the expected per-architecture artifacts.
- [x] 4.2 Run the relevant local x86 validation path to confirm arm64 checks remain evaluation-only where full arm64 execution is unavailable.
- [ ] 4.3 Confirm the next image publication run can complete both amd64 and arm64 build jobs before manifest publication.
