## Context

`ghostship-bookstack` was added as a full-surface CLI, but live validation against the deployed Hermes image on `chill-penguin` shows that the shipped surface is inconsistent. Typed JSON operations such as `books_list` work when the runtime points at the internal BookStack origin, while the generic `request` escape hatch and text-response operations such as `docs_display` fail because the BookStack client override does not match the shared `BaseHttpClient` parameter contract.

The same live validation also showed a transport-classification gap: when `BOOKSTACK_URL` pointed at the external Cloudflare-protected ingress, `/api/books` returned `302` and the shared HTTP layer could treat that response as a successful empty-body result instead of surfacing the redirect as a failure. Current tests cover command registration, dry-run payload shape, and shared JSON handling, but they do not cover the real passthrough/text call paths or redirect classification.

## Goals / Non-Goals

**Goals:**
- Make the BookStack generic request path and text-response commands execute through the same working parameter contract as typed JSON operations.
- Ensure the shared HTTP layer reports unexpected redirect responses as failures unless a client explicitly opts into following redirects.
- Add regression coverage that would fail on the exact issues seen in the live deployment.
- Record the supported BookStack runtime topology so live validation can distinguish a reachable API origin from an auth gateway.

**Non-Goals:**
- Rebuild the BookStack operation catalog or rename existing operation-aligned commands.
- Change the BookStack auth model or add service-specific compatibility aliases.
- Introduce a broad live-integration framework for every utility in the repo.

## Decisions

### Align derived service clients to the shared request signature
The BookStack client will either stop overriding `request` and `request_response` where no service-specific behavior is needed, or it will expose the same keyword interface as `BaseHttpClient` (`params`, `json_body`, `form_data`, `files`, `headers`, `timeout`) and map any service-local aliases internally. This keeps the shared CLI helpers free to call the base contract consistently.

Alternative considered: teaching the shared client layer to understand service-specific `query_params` aliases. Rejected because it pushes one package's inconsistency into the shared contract and makes future service clients easier to break in the same way.

### Treat non-followed redirects as transport failures, not successful responses
`BaseHttpClient.request()` will classify unexpected `3xx` responses as HTTP status failures when `follow_redirects=False`. That keeps auth-gateway redirects, bad ingress targets, and other topology errors visible to operators and prevents empty redirect bodies from being decoded as `{"status": "success"}`.

Alternative considered: enabling redirect following by default. Rejected because it can hide bad routing and auth boundaries, and it does not solve cases where a redirect lands on HTML login content that still violates the utility's contract.

### Add regression tests at the failure boundary, not only on command registration
The BookStack package will gain tests for `request` and `docs_display`, and the shared contract package will gain redirect-classification tests. The validation target is the runtime behavior seen in the deployed image: a typed JSON command, a passthrough request, a text-response command, and a redirect/error path.

Alternative considered: relying only on manual deployed-image checks. Rejected because these failures shipped once already and are cheap to reproduce with unit tests.

### Document the supported BookStack runtime topology alongside smoke validation
The change will document that a working deployment must either target the internal BookStack API origin directly or provide any required Cloudflare Access headers. Validation steps will use that documented topology so operators can distinguish a CLI bug from a misrouted service URL.

## Risks / Trade-offs

- [Stricter redirect handling may surface new failures in other utilities] → Mitigation: keep redirect classification in the shared contract explicit, add focused tests, and review any utilities that intentionally set `follow_redirects=True`.
- [Fixing only BookStack client dispatch may miss similar derived-client drift elsewhere] → Mitigation: inspect other full-surface clients for base-signature mismatches as part of implementation.
- [Live BookStack validation depends on environment-specific routing and tokens] → Mitigation: keep unit coverage authoritative and use remote smoke checks only as deployment confirmation.

## Migration Plan

1. Patch the shared HTTP and BookStack client call paths locally.
2. Add regression tests in `packages/bookstack-cli/tests` and `packages/ghostship-cli-contract/tests`.
3. Run the standard Python utility test/build workflow for the touched packages.
4. Redeploy the Hermes image and re-run the remote BookStack smoke checks on `chill-penguin`.
5. If redirect classification causes an unexpected regression elsewhere, temporarily point affected deployments at their internal origins while evaluating whether those clients should opt into redirect following.

## Open Questions

- Do any other deployed `ghostship-*` utilities currently depend on `3xx` responses passing through as success?
- Should the BookStack live smoke checks remain a documented operator workflow, or should the repo add a reusable ad hoc script for container validation?
