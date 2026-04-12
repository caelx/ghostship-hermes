## Context

The original shared-cache rollout already fixed one major ordering bug by moving cache planning before the real image build. That was necessary, but it was not sufficient. The latest `publish-image` runs on April 12, 2026 show both architecture legs planning thousands of paths and then failing during cache publication with `Argument list too long` inside the pinned upstream `cache-builder.sh`. The failure happens while the helper rebuilds the cache index in shell arguments, so the NAR uploads begin but the `cache-index` manifest never gets written.

That leaves the system stuck in the worst possible middle state: the workflow spends time exporting and uploading paths, but later runs still see no usable shared cache and rebuild from scratch. The repo also wants the cache path to stay fast. Adding more workflow verification jobs or extra publish-only checks would work against the main goal, so the design has to fix correctness while keeping the steady-state workflow lean.

## Goals / Non-Goals

**Goals:**
- Make a successful cache-refresh publish run complete `cache-index` creation or update without hitting shell argument limits.
- Keep shared-cache bootstrap fast for the intended public-cache path while preserving authenticated fallback behavior where available.
- Avoid introducing new workflow jobs or repeated verification steps that increase normal publish latency.
- Preserve the current fail-open rule that image publication still succeeds when cache publication or bootstrap fails.
- Define manual proof criteria that Codex can execute from seeded and repeat runs without baking new proof steps into the workflow.

**Non-Goals:**
- Replace `nixcache-oci` with a different cache backend.
- Add new GitHub Actions jobs, dedicated cache-proof stages, or extra post-build verification runs inside the workflow itself.
- Rework the published image contract or change the explicit `ghostship-hermes-image` artifact path.
- Expand the shared cache beyond the current Ghostship publication/consumption scope.

## Decisions

### Patch the pinned upstream helper at the integration boundary

The real blocker is in the pinned upstream `cache-builder.sh`, where index updates are assembled by repeatedly passing growing JSON blobs through shell arguments. The integration should patch or wrap that helper so index assembly happens through temp files or stdin instead of argv.

Alternative considered: reimplement cache publication locally. Rejected because the repo already relies on the upstream helper for OCI publication behavior, and a local rewrite would create more long-term maintenance surface than a narrowly-scoped integration patch.

### Keep the public-cache fast path and add authenticated fallback only where it is needed

The intended contract is that `caelx/ghostship-cache` is public, so normal cache detection and consumption should remain cheap. At the same time, the helper should not assume anonymous access forever. Bootstrap and index checks should prefer the public path and fall back to token-backed reads when a token is already available, without adding extra probes in the common case.

Alternative considered: make every cache check authenticated first. Rejected because it adds unnecessary coupling and overhead for a cache that is supposed to be publicly consumable.

### Remove redundant preflight behavior instead of adding more checks

The workflow should keep the pre-build planning step because that is required for correctness with the current dry-run planner. Beyond that, the design should avoid or remove redundant cache-publish probes that only add roundtrips without changing the publish decision materially. Cache publication can remain gated by refresh intent and required signing inputs, then fail non-fatally if the actual upload path cannot complete.

Alternative considered: add explicit cache-proof or cache-health workflow steps. Rejected because the user requirement is to avoid slowing the workflow further.

### Treat proof as a manual two-run operator flow

The right proof is still one seeded run plus one unchanged repeat run, but that proof should be manual and log-driven rather than encoded as another workflow stage. The workflow already emits enough evidence to compare plan size, bootstrap behavior, and whether the build still performs a large cold build.

Alternative considered: add a workflow assertion that fails when warm-cache evidence is missing. Rejected because the cache path is infrastructure-sensitive and should not become another steady-state source of workflow latency or flake.

## Risks / Trade-offs

- [Patching pinned upstream helper logic may drift from future upstream changes] -> Keep the patch surface as small as possible and isolate it to the JSON/index-update path rather than forking the entire cache flow.
- [Public GHCR access behavior may differ from local CLI observations] -> Keep authenticated fallback available in the helper and proxy even though the public path remains the preferred fast path.
- [Removing redundant probes may hide certain permission mistakes until publish time] -> Preserve non-fatal cache upload logging so publish runs still surface the failure reason without blocking image publication.
- [Manual proof requires human review of two runs] -> Accept that trade-off because it avoids adding persistent workflow overhead.

## Migration Plan

1. Patch the shared-cache helper integration so cache-index updates no longer pass large JSON payloads through shell arguments.
2. Simplify cache publish gating to keep only the checks required for correctness and configured refresh policy.
3. Adjust bootstrap/proxy wiring so public reads stay fast and token-backed fallback is available when needed.
4. Run one manual cache-refresh `workflow_dispatch` from the implementation branch and confirm it completes a real cache publication.
5. Run one unchanged follow-up `workflow_dispatch` and verify from the logs that bootstrap sees the cache and the repeat build shows meaningful reuse instead of another full cold build.

## Open Questions

- Should the integration patch be applied by editing the fetched upstream helper in place, or by replacing only the index-update functions with a repo-owned shim?
- Is there any remaining cache-publish probe in `publish-image` that can be dropped entirely once the real upload path is fixed?
