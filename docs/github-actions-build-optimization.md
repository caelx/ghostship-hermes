# GitHub Actions Build Optimization

Historical note: the 2026-04-11 overlay-based final publication path described in older drafts was superseded after it dropped managed runtime changes from the deployed image. Final GHCR publication now exports the explicit `ghostship-hermes-image` bundle instead.

This note captures the measured optimization baseline for the `optimize-github-actions-image-builds` change, the acceptance metrics used for each implementation round, and the final measured outcome from the landed workflow.

## Baseline

Captured on 2026-04-10 UTC from recent successful GitHub Actions runs:

- `ci`: approximately `9.5` minutes average over the last 10 successful runs
- `publish-image`: approximately `36.9` minutes average over the last 10 successful runs
- Latest successful `publish-image` job breakdown:
  - `build (x86_64-linux, ubuntu-24.04)`: approximately `33.5` minutes
  - `build (aarch64-linux, ubuntu-24.04-arm)`: approximately `26.4` minutes
  - `publish`: approximately `4.9` minutes

The current long pole is the native multi-arch publish path, not the lightweight `ci` verification path.

## Acceptance Metrics

Use these metrics for each optimization round:

- `publish-image` runner frequency: how often the workflow runs after path gating lands
- `publish-image` warm-cache elapsed time: the main steady-state success metric
- `publish-image` cold-cache elapsed time: to confirm worst-case behavior remains reasonable
- `ci` elapsed time: to verify Python utility setup changes reduce overhead without weakening checks
- Whole-workflow elapsed time and major job timings: to distinguish build bottlenecks from workflow overhead

The stretch target for this change remains approximately `10` minutes end-to-end for `publish-image`, but the evaluation should distinguish between cold-cache and warm-cache results.

## Final Measured Outcome

Measured on 2026-04-11 UTC from the landed `main` workflow:

- `ci`: approximately `9.44` minutes average over the latest 6 successful `main` runs, down slightly from the `9.5` minute baseline but still dominated by the Python utility test step.
- `publish-image` latest successful `main` average: approximately `32.01` minutes over the latest 4 successful `main` runs, with that aggregate still mixing cold-content and reuse-path runs.
- Cold-content publish (`24272531324`, `fix(ci): cancel superseded main workflow runs`): `34.97` minutes end-to-end.
- Base-reuse publish (`24270102401`, `docs(openspec): propose repeat image publish reuse`): `20.48` minutes end-to-end.
- Warm-repeat publish (`24273264295`, manual `workflow_dispatch` on `main`): `1.17` minutes end-to-end.

Observed long poles by path:

- Cold-content: native base-image publication is still the long pole. In run `24272531324`, `Ensure base image tag exists` took approximately `31.5` minutes on `amd64` and `24.07` minutes on `arm64`.
- Base-reuse: once the base is already published, the remaining bottleneck is the final overlay/content image build. In run `24270102401`, `Ensure base image tag exists` completed in approximately `0.02` minutes on both architectures while `Build and publish content-addressed final image` still took approximately `18.15` minutes on `amd64` and `15.78` minutes on `arm64`.
- Warm-repeat: both architecture jobs found the immutable final image and skipped both `Ensure base image tag exists` and `Build and publish content-addressed final image`; only the lightweight retag/manifest work remained.

Stretch-goal result:

- The approximately `10` minute publish stretch goal is still missed for cold-content publishes.
- The stretch goal is also still missed for overlay-only/base-reuse publishes at approximately `20.5` minutes.
- The exact-repeat steady-state path easily beats the stretch goal at approximately `1.2` minutes.

## Publish Gating Result

From the latest successful `main` workflow window after path gating landed:

- `ci` recorded 6 successful `main` push runs.
- `publish-image` recorded 4 successful `main` push runs over the same window.
- That means at least 2 successful `main` pushes completed without triggering automatic publication because they were non-image changes.

Using the current successful `publish-image` average of approximately `32.01` minutes, those skipped automatic publishes avoided roughly `64` runner-minutes in that sample window alone.

## Workflow Strategy

Optimization rounds are implemented in this order:

1. Conservative publish gating so docs-only and OpenSpec-only `main` pushes do not publish images.
2. Cache-backed reuse:
   - native `uv` caching for the Python utility steps in `ci`
3. Architectural publish optimization by keeping a true reusable per-architecture `ghostship-hermes-base` image for the shared Hermes/core-runtime layer, while keying content-addressed final-image reuse to the explicit `ghostship-hermes-image` bundle so repeated runs can still avoid exact-repeat publishes without dropping managed runtime changes from the final image.

## Measuring Again

Use the repo helper script after each round:

```fish
python3 scripts/github_actions_timings.py --include-latest-jobs
```

If you want to target one workflow only:

```fish
python3 scripts/github_actions_timings.py --workflow publish-image.yml --include-latest-jobs
```

The helper emits JSON so runs, job timings, and the latest-job breakdown can be copied directly into this note without hand-timing the Actions UI.

## Cache Notes

The current free reuse strategy is split by workflow.
- `uv` cache keys are derived from the tracked Python utility inputs and lockfiles, so dependency changes create a new cache key automatically.
- The publish workflow first checks for a GHCR-published content-addressed final image derived from the explicit `ghostship-hermes-image` bundle derivation; if it exists, the run skips rebuilding/exporting that final image and retags the immutable image directly.
- The reusable `ghostship-hermes-base` image is built from the shared module with final-only wiring disabled. It now carries upstream Hermes/core container behavior, the stable shared system/runtime toolchain (`bashInteractive`, `cacert`, `coreutils`, `curl`, `findutils`, `git`, `gh`, `gnugrep`, `gnused`, `jq`, `nix`, `nodejs_22`, `openssh`, `procps`, `ripgrep`, `tirith`, `ttyd`, and `util-linux`), the shared Python dependency closure (`httpx`, `typer`, `fastapi`, `uvicorn`, and `websockets` from the repo's overridden Python package set), and the stable external utility closures (`agent-browser`, `bws`, `gcloud`, and `gws`).
- When the final image is not already available, the workflow still ensures the separate GHCR-published `ghostship-hermes-base` image exists, tagged from an explicit tracked base-input set instead of the raw base derivation path, so the reusable base artifact stays current without forcing another native base build on overlay-only changes.
- The repo-owned command surfaces still stay out of the base closure (`ghostship-hermes-router`, `ghostship-hermes-runtime`, `hermes-dashboard`, `ghostship-cli-contract`, and the `ghostship-*` utilities). The overlay bundle remains an internal closure-audit artifact, but final GHCR publication no longer reconstructs `ghostship-hermes` from that lightweight overlay path.
- Structural validation for the split boundary is still `nix why-depends --derivation` plus realized overlay inspection: the base image derivation should stay free of final-only Ghostship closures, and the overlay bundle store paths should remain limited to Ghostship-owned packages plus the tiny overlay env.
- Magic Nix Cache was removed from `publish-image` after the native multi-arch jobs repeatedly hit GitHub Actions cache throttling and `ResourceExhausted` responses from the cache proxy.
