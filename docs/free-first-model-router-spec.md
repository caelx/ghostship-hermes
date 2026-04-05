# Free-First Model Router for Hermes

## Purpose

Build a lightweight Python service that acts as a local model router for Hermes.

The router should maximize use of free models first, intelligently choose among them based on health and responsiveness, and transparently fall back to paid models only when necessary.

This is intended to become the main routing layer for small tasks at first, and later possibly for more advanced coding and general agent workloads.

## Core goals

The router must:

- present a stable API to Hermes
- manage a pool of free models from multiple providers
- discover available models automatically
- rank and bucket models by capability
- route requests to the best currently healthy model
- transparently fail over when a model or provider fails
- avoid wasting time on slow or unhealthy models
- fall back to paid Gemini only when free options are not usable

## High-level behavior

Hermes should not need to know the real underlying model names most of the time.

Instead, the router should expose a small set of stable logical model aliases such as:

- lightweight
- coding
- heavyweight

Each alias maps to a dynamic pool of backend models.

The router is responsible for deciding which real backend model should serve a given request.

## Free-first routing policy

The router should prefer free models before anything paid.

General flow:

1. receive a request for a logical model alias
2. identify the pool of candidate free models for that alias
3. remove models/providers that are currently unhealthy, rate-limited, exhausted, or disabled
4. rank the remaining candidates based on recent observed performance
5. send the request to the best candidate
6. if it fails, automatically retry with the next best candidate
7. if no free candidate works, fall back to Gemini

## Model pools

The router should support multiple buckets of models.

Suggested buckets:

### Lightweight

For summaries, extraction, classification, routing, and cheap general work.

### Coding

For code generation, debugging, editing, and technical reasoning.

### Heavyweight

For harder reasoning or tasks where weaker free models perform poorly.

These are logical pools, not fixed providers.

## Model discovery

The router should automatically maintain its view of available models.

It should support:

- periodic model refresh on a timer
- refresh on startup
- forced refresh when a request fails because a model no longer exists
- updating internal metadata without requiring manual edits

The point is to avoid hardcoding fragile model lists wherever possible.

## Model classification

Discovered models should be sorted into capability buckets.

Classification can be based on:

- static rules you define
- naming heuristics
- metadata if available
- optional background ranking/classification by a stronger model

This classification should not happen inline on the request path unless absolutely necessary.

It should be a background maintenance task.

## Routing intelligence

The router should track live performance over time and use that to make better decisions.

It should maintain rolling state for each provider and model, including things like:

- average latency
- recent failures
- recent success rate
- rate-limit behavior
- likely quota exhaustion
- current cooldown state
- capability tags
- operator preference weights

The ranking system should prefer models that are:

- healthy
- responsive
- appropriate for the task class
- still likely to have free usage available

## Transparent failover

If a model fails, the caller should not need to care.

The router should transparently handle:

- model not found
- unauthorized
- rate limit
- timeout
- server failure
- transient provider errors

Expected behavior:

- immediately penalize or cool down the failing backend
- try the next best candidate
- continue until success or exhaustion of candidates
- only surface an error to Hermes when the entire pool is unusable

## Provider and model disablement

The router should be able to temporarily disable individual models or whole providers when they appear unusable.

Examples:

- repeated rate limits
- repeated auth failures
- repeated timeouts
- obvious quota exhaustion
- operator-defined disablement

Disablement should usually be temporary, not permanent.

The router should automatically retry disabled models/providers later after cooldown or refresh.

## Gemini fallback

Gemini is the paid backup layer.

It should only be used when:

- no suitable free model exists for the request
- all free models for that request are unhealthy
- the free pool appears exhausted
- a required capability is unavailable among free models

Gemini should be stable and predictable, not part of the volatile free-model competition.

## Router API expectations

The router should expose a simple model API that Hermes can target.

It should provide:

- a way to list the logical models it exposes
- a chat/completion-style endpoint Hermes can call
- health and readiness endpoints
- metrics for debugging and tuning

The external contract should stay stable even when the backend pool changes.

## Persistence

The router should persist its state across restarts.

That includes:

- discovered model inventory
- rolling latency and health data
- disablement and cooldown state
- manual overrides
- bucket assignments
- provider metadata

This should live in a small local persistent store.

## Observability

The router should make it easy to understand what it is doing.

It should expose:

- structured logs
- per-request backend choice
- retry count
- failure reasons
- current health state
- model rankings
- metrics over time

This is important because tuning free-model routing will require visibility.

## Configuration

The router should be configurable without code changes.

It should support configuring:

- providers
- API keys
- refresh intervals
- bucket definitions
- static model weights
- cooldown behavior
- disablement thresholds
- paid fallback choice
- operator allowlists and blocklists

## Suggested implementation shape

Build this as a small local Python service under systemd.

Keep it simple and modular.

Likely components:

- API layer
- provider adapters
- model registry
- routing engine
- health tracker
- background refresh/classification jobs
- persistence layer
- metrics/logging

## Recommended development order

### Phase 1

Get the basic router working:

- stable aliases
- model discovery
- ranking
- free-first selection
- automatic retry/failover
- Gemini fallback
- persistent state

### Phase 2

Add smarter dynamic behavior:

- better model bucketing
- stronger health scoring
- provider-wide disablement
- automatic recovery
- operator overrides
- richer metrics

### Phase 3

Make it strong enough for broader use:

- more capable coding pool selection
- better long-running performance tuning
- optional stronger classification logic
- advanced routing policies

## Guidance for implementation

Important design principles:

- keep Hermes-facing behavior simple and stable
- keep free-model logic inside the router
- do not hardcode too much brittle provider detail
- optimize for recovery and unattended operation
- make routing decisions observable
- prefer graceful degradation over hard failure

## What success looks like

The router is successful if:

- Hermes can point at stable logical model aliases
- free models are used as much as possible automatically
- slow or broken models get deprioritized without manual intervention
- model inventory updates itself
- failures are handled transparently
- paid Gemini is only used when truly needed
- the whole system can run unattended inside the container
