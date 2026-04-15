## ADDED Requirements

### Requirement: Router supports curated NVIDIA Build API inventory
The router SHALL support NVIDIA Build API as an optional first-class provider activated by `NVIDIA_BUILD_API_KEY`. When enabled, the router SHALL expose only a repo-curated free-only NVIDIA inventory instead of broadly routing the hosted NVIDIA catalog.

#### Scenario: Configured NVIDIA key activates curated provider inventory
- **WHEN** `NVIDIA_BUILD_API_KEY` is configured for the router
- **THEN** the router registers provider `nvidia-build` during provider construction and refresh
- **AND** the provider inventory includes only repo-curated NVIDIA model ids
- **AND** only NVIDIA models designated free by the repo-owned inventory policy can become route candidates

#### Scenario: Missing NVIDIA key leaves provider disabled
- **WHEN** `NVIDIA_BUILD_API_KEY` is not configured
- **THEN** the router does not register provider `nvidia-build`
- **AND** routing continues using the remaining configured providers without NVIDIA inventory

## MODIFIED Requirements

### Requirement: Router performs free-first routing with transparent failover
The router SHALL prefer eligible free backends for each logical alias, cap each provider to its top scored alias-local candidates before cross-provider interleaving, track health at the concrete backend-model level, retry alternate models after retryable failures, and surface an error only after the candidate pool is exhausted.

#### Scenario: Healthy free candidate is selected before paid fallback
- **WHEN** a caller requests a logical alias with at least one eligible healthy free candidate
- **THEN** the router attempts a healthy free candidate before any paid fallback

#### Scenario: Retryable backend failure triggers transparent retry
- **WHEN** the selected backend fails with a retryable failure such as timeout, rate limit, transient provider error, or missing model
- **THEN** the router penalizes or cools down that concrete backend model
- **AND** it retries the request against the next eligible backend model without requiring caller intervention

#### Scenario: Exhaustion retry re-enters ranked candidate selection
- **WHEN** a backend fails with an exhaustion-class signal such as provider throttling, quota exhaustion, or insufficient balance
- **THEN** the router updates exhaustion state for that concrete backend model
- **AND** it recomputes the remaining eligible candidates from the ranked priority list
- **AND** it continues the same request with the highest-ranked remaining candidate regardless of provider

#### Scenario: Pool exhaustion returns a router error
- **WHEN** all eligible backend-model candidates for the requested alias are unusable
- **THEN** the router returns an error that indicates the alias pool is currently exhausted or unavailable

#### Scenario: Candidate ordering uses persisted ranking and recent health
- **WHEN** the router orders eligible candidates for a logical alias
- **THEN** it combines free-model preference, alias fit, rolling live health data, and persisted ranking outputs
- **AND** it does not rely only on static name heuristics once ranking data is available

#### Scenario: Per-provider shortlist is capped before alias interleaving
- **WHEN** the router orders eligible candidates for a logical alias bucket
- **THEN** it keeps at most the top `3` scored models from each provider for that alias
- **AND** it interleaves the provider-local shortlists into the final alias candidate order
- **AND** lower-ranked models from the same provider do not enter normal routing for that alias unless operator pins or overrides explicitly require them

#### Scenario: Provider priority affects cross-provider ordering
- **WHEN** multiple providers expose healthy eligible candidates for the same logical alias
- **THEN** the router applies provider-priority policy after eligibility, cooldown, pacing, and health filtering
- **AND** `nvidia-build` ranks ahead of `opencode-zen` and `openrouter` by default when their remaining score inputs are otherwise comparable

#### Scenario: Provider-wide suppression affects candidate selection
- **WHEN** a provider enters temporary cooldown or disablement because of broad auth, timeout, rate-limit, or exhaustion signals
- **THEN** the router deprioritizes or excludes models from that provider during candidate selection
- **AND** the provider becomes eligible again after recovery conditions or cooldown expiry
