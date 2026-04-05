## 1. Router-Primary Hermes Runtime

- [x] 1.1 Update the Hermes image bootstrap to write root and managed profile configs with `model.base_url = http://127.0.0.1:8788/v1`
- [x] 1.2 Set the root Hermes default model to `lightweight`, the `operations` profile default to `heavyweight`, and the `coder` profile default to `coding`
- [x] 1.3 Add router dependency ordering so the managed `operations` and `coder` gateway services start after the local router service

## 2. Dashboard Environment View

- [x] 2.1 Replace OpenRouter-specific dashboard environment parsing with generic root and per-profile model endpoint parsing
- [x] 2.2 Update the dashboard home view to show root endpoint/model facts separately from per-profile endpoint/model facts
- [x] 2.3 Add local-router enrichment that reads router alias inventory and provider health when Hermes points at the local router

## 3. Router-First Validation

- [x] 3.1 Update the Hermes image dashboard smoke test to verify router service health, alias discovery, and the configured root/profile defaults
- [x] 3.2 Update the persistence validation to verify the router-primary config before and after container replacement

## 4. Documentation And Readiness

- [x] 4.1 Update README runtime documentation to describe the router as the primary OpenAI-compatible endpoint and document the root/profile alias defaults
- [x] 4.2 Update local validation guidance to remove direct-upstream `OPENROUTER_TEST_MODEL` assumptions in favor of router-first checks
