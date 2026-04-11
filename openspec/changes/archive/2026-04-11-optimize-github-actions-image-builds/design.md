## Context

The repo's GitHub Actions image optimization effort now has three implemented pieces that belong together:

- broad workflow optimization and publish gating
- repeat-publish reuse through stable base tags and immutable final-image tags
- a true Hermes base-image split that removes Ghostship-owned runtime wiring from the base closure

Treating these as separate active OpenSpec changes now adds bookkeeping overhead without adding clarity. The actual optimization architecture is one stack: skip unnecessary publishes, reuse the slow-changing base layer, reuse exact final-image content when possible, and keep measuring what still dominates cold runs.

## Goals / Non-Goals

**Goals:**
- Keep one authoritative OpenSpec track for GitHub Actions image-build optimization.
- Preserve the free-only GHCR-backed optimization strategy.
- Keep the base image low-churn by excluding Ghostship-owned runtime packages and managed service wiring.
- Keep only approved shared dependencies in base when they materially reduce overlay churn.
- Distinguish cold-content publishes, base-reuse publishes, and warm-repeat publishes in verification and timing evidence.

**Non-Goals:**
- Reopening paid-cache options.
- Changing the consumer-facing `ghostship-hermes` image contract.
- Claiming the 10-minute stretch goal was met without measured evidence.

## Decisions

### 1. Keep one surviving change for the whole optimization stack
The surviving change is `optimize-github-actions-image-builds`. The repeat-publish reuse and true-base work are now subparts of that optimization plan rather than independent active changes.

### 2. Reuse order stays layered and free-only
The selected publish stack is:
1. skip irrelevant publishes through workflow gating
2. reuse immutable final architecture images when the full content matches
3. otherwise reuse stable per-architecture base images when the base payload matches
4. rebuild natively only when neither reusable image exists

### 3. The base image is a true Hermes/core-runtime layer
The base image carries upstream Hermes/core container behavior plus approved shared dependency closures, but it excludes Ghostship-owned runtime packages and managed service wiring.

Approved base-side shared dependency set:
- shared Python service deps from the repo's overridden Python package set: `httpx`, `typer`, `fastapi`, `uvicorn`, `websockets`
- stable external utility closures that materially shrink the overlay: `agent-browser`, `bws`, `gcloud`, `gws`
- shared system/runtime toolchain already approved for the image runtime

### 4. Overlay inspection is part of the acceptance criteria
The optimization effort is not done when the module split looks right in source. The realized overlay must be inspected so remaining shared non-Ghostship closures are moved into base when that lowers churn without reintroducing repo-coupled semantics.

### 5. Timing evidence must separate cold, base-reuse, and warm-repeat paths
The remaining open measurement work should report these cases separately so the repo can tell whether the architecture changes helped in the intended steady-state scenarios even if cold publishes remain slow.

## Risks / Trade-offs

- [One consolidated change becomes broader] -> Keep the tasks grouped by optimization round and architecture boundary so the surviving change remains navigable.
- [Base-side dependency creep reintroduces churn] -> Keep the dependency-audit rule explicit and inspect the realized overlay before expanding the base set.
- [Cold publishes remain slow] -> Record that explicitly rather than masking it with warm-repeat wins.

## Migration Plan

1. Consolidate the three overlapping optimization changes into `optimize-github-actions-image-builds`.
2. Keep the merged spec deltas for image publication, repeat-publish reuse, and the true base-image architecture under that one change.
3. Preserve the implemented workflow and image-boundary changes already on `main`.
4. Finish the remaining runtime-contract and timing verification work under the single surviving change.
