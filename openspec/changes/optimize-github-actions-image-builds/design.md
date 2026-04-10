## Context

The repo currently has two materially different GitHub Actions cost centers:

- `ci` on pull requests and `main` pushes, which averages about 9.5 minutes and is dominated by the Python utility test step.
- `publish-image` on every `main` push, which averages about 36.9 minutes and is dominated by the native `x86_64-linux` and `aarch64-linux` image builds.

The current workflow shape is simple and correct, but it treats most `main` pushes as if they require a fresh two-architecture image publication. The repo also does not currently define a cache-backed build reuse strategy in Actions, so repeated runs rebuild large parts of the same Nix graph and recreate Python test environments on fresh runners. Because the publish path is the real bottleneck, the change should optimize the full end-to-end publication path first and treat the 10-minute target as a stretch budget that may require architectural changes rather than only YAML tuning.

## Goals / Non-Goals

**Goals:**

- Reduce unnecessary `publish-image` executions for non-image changes.
- Add instrumentation that records baseline and post-change timings per workflow and per job so optimization rounds can be evaluated with evidence.
- Add reusable caches or binary substituters for Nix and package-manager state where cache correctness is defensible.
- Permit architectural changes to image assembly and publication if they materially reduce wall-clock time while preserving the explicit `ghostship-hermes-image` contract.
- Define an optimization program that proceeds in rounds, with verification after each round and an explicit stretch target of about 10 minutes for the full image publish path.

**Non-Goals:**

- Changing the published runtime contract of `ghostship-hermes-image`.
- Dropping native multi-arch publication support.
- Optimizing every repository workflow equally; this change prioritizes the image build and publish path first.
- Guaranteeing a hard 10-minute SLA regardless of upstream runner, network, or cache state.

## Decisions

### 1. Make optimization evidence-driven instead of one-shot

The change will define a baseline-and-rounds workflow rather than a single batch of speculative tweaks. Each round will:

- record measured timings for `ci` and `publish-image`
- apply one coherent optimization set
- verify correctness and publication behavior
- compare elapsed time against the previous baseline

This avoids landing many opaque changes without knowing which one actually moved the needle.

Alternatives considered:

- Apply all likely optimizations at once: faster to implement, but it obscures which changes help and makes rollback harder.
- Optimize only the slowest job by intuition: lower effort, but too easy to miss structural waste such as unnecessary publish triggers.

### 2. Treat workflow gating as the first optimization round

The fastest image build is the one that does not run. The first round should therefore focus on gating `publish-image` by relevant path changes and release triggers. This offers the highest likely reduction in total wall-clock time spent per day and per push, even if it does not reduce the duration of every individual publish run.

Alternatives considered:

- Start with cache tuning first: useful, but it still leaves the repo rebuilding images for docs/OpenSpec-only pushes.
- Start with architectural image changes first: potentially valuable, but higher risk and slower to validate than trigger gating.

### 3. Treat cache-backed reuse as the second optimization round

Once irrelevant publish runs are eliminated, the next round should add concrete reuse:

- Nix binary cache or substituter for build outputs and closures
- package-manager cache for Python utility test setup
- any repo-local timing metadata needed to compare cache-hit versus cache-miss runs

The repo's current Nix-heavy image graph makes binary-cache reuse the most plausible way to materially reduce repeated native build time without compromising correctness.

Alternatives considered:

- Rely only on GitHub Actions cache for Nix store state: generally weaker and less reliable than a true substituter/binary cache for large Nix closures.
- Optimize Python only: good for `ci`, but it does not address the dominant `publish-image` cost.

### 4. Use a reusable base-image plus overlay assembly path for the architectural round

After the gating and cache rounds, the publish path still materially exceeds the stretch target because each architecture leg rebuilds and re-exports the full publishable image bundle. The selected architectural change is to split publication into:

- a slow-changing per-architecture `ghostship-hermes-base` image built from a reduced NixOS system that keeps the runtime contract but replaces repo-owned commands with overlay shims
- a `ghostship-hermes-overlay-bundle` derivation that carries the real repo-owned utilities and runtime packages as a small Docker build context
- a final per-architecture Docker assembly step that starts from the published base image, copies in the overlay closure, and then pushes the normal `ghostship-hermes` tags

This keeps the explicit `ghostship-hermes-image` contract for downstream consumers while making repeated publishes depend on a reusable GHCR base tag instead of rebuilding the entire image every time.

Alternatives considered:

- Commit immediately to a layered or prebuilt-image architecture before measuring gating and cache-backed reuse: potentially faster, but premature without evidence that simpler optimizations were insufficient.
- Keep the old single-shot native publish path and tune only YAML around it: lower implementation risk, but it leaves the dominant full-image rebuild cost on every publish run.

### 5. Keep correctness verification in every round

Every round must verify:

- the publishable image still derives from the explicit `ghostship-hermes-image` contract
- both architectures still publish correctly
- `main` and release-triggered publication semantics remain correct
- skipped runs are skipped only when the change is truly non-image-affecting

The repo should not chase speed by silently weakening publication coverage.

## Risks / Trade-offs

- [Aggressive path gating misses a real image-affecting change] → Start with conservative path filters, add explicit override/manual dispatch, and validate against representative change sets before tightening further.
- [Cache configuration introduces stale or confusing builds] → Prefer content-addressed or lockfile-keyed cache boundaries, document cache invalidation rules, and keep an escape hatch for no-cache validation.
- [Architectural publication changes accidentally alter image semantics] → Preserve the explicit `ghostship-hermes-image` contract as the compatibility boundary and verify runtime metadata on every optimization round.
- [The 10-minute target is not achievable on cold runners] → Treat 10 minutes as a stretch target, report warm-cache and cold-cache timings separately, and optimize for materially lower steady-state time rather than only best-case runs.
- [Optimization rounds create temporary workflow complexity] → Keep instrumentation and helpers repo-owned and remove one-off probes once a stable optimized path is established.

## Migration Plan

1. Capture and document the current workflow baseline using recent GitHub Actions timings.
2. Implement round 1 gating and verify that image publication still runs for image-affecting and release-triggering changes.
3. Implement round 2 cache-backed reuse and compare warm-cache and cold-cache timings.
4. If the publish path remains materially above target, evaluate and prototype architectural pipeline changes behind the existing image contract.
5. Keep the fastest correct configuration, update docs/changelog as needed, and record the final measured timing summary.

Rollback strategy:

- Revert the most recent optimization round independently if it causes regressions.
- Preserve manual `workflow_dispatch` access so maintainers can force publication while diagnosing gating or cache issues.

## Open Questions

- Which binary cache backend is the best fit for this repo's trust and operational model?
- Is the primary success metric the median warm-cache publish duration, the cold-cache duration, or total runner minutes consumed across all pushes?
- How much architectural change is acceptable if the 10-minute target cannot be met through gating and caching alone?
