## 1. Policy Inputs

- [ ] 1.1 Encode the initial repo-owned top-five `agentic` usable order:
  - `nvidia-build`: `minimaxai/minimax-m2.7`, `qwen/qwen3-coder-480b-a35b-instruct`, `moonshotai/kimi-k2-thinking`, `deepseek-ai/deepseek-v3.2`, `z-ai/glm-4.7`
  - `opencode-zen`: `big-pickle`, `minimax-m2.5-free`, `trinity-large-preview-free`, `nemotron-3-super-free`, `gpt-5-nano`
  - `openrouter`: `qwen/qwen3-next-80b-a3b-instruct:free`, `google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free`, `openai/gpt-oss-120b:free`, `meta-llama/llama-3.3-70b-instruct:free`
- [ ] 1.2 Capture the initial explicit unused-model lists for discovered models that Hermes should never route.
- [ ] 1.3 Define the single persisted router policy surface for usable rankings, unused-model policy, provider order, and exhaustion thresholds.

## 2. Provider Discovery And Eligibility

- [ ] 2.1 Replace NVIDIA allowlist-only inventory loading with live NVIDIA catalog discovery behind `NVIDIA_BUILD_API_KEY`.
- [ ] 2.2 Filter discovered NVIDIA inventory to free endpoints and apply repo-owned usable or unused overlays before normal routing eligibility.
- [ ] 2.3 Collapse normal router alias exposure to `agentic` and reject retired logical aliases for normal routing.

## 3. Ranking And Failover Semantics

- [ ] 3.1 Rework candidate selection so only explicitly ranked usable models route inside each provider, with a top-five reserve and a hard cap of three active candidates chosen from the currently eligible members of that top five.
- [ ] 3.2 Exclude uncategorized discovered models from routing and surface them through an operator-facing uncategorized inventory endpoint.
- [ ] 3.3 Rework routing to stay on the highest-priority eligible provider (`nvidia-build` then `opencode-zen` then `openrouter`) until clear free-tier exhaustion or no eligible candidates remain.
- [ ] 3.4 Keep retryable model failures inside the active provider and ensure only exhaustion-class evidence triggers normal cross-provider failover.
- [ ] 3.5 Add provider-aware daily-limit inference, reset-window handling, and probe-based recovery so repeated pacing or zero-output exhaustion can suppress a provider without relying on one explicit quota error.
- [ ] 3.6 Add session stickiness inside the active provider and expose an operator-facing inventory endpoint for explicitly unused discovered models.

## 4. Runtime And Discord Wiring

- [ ] 4.1 Update managed Hermes `ghostship-router` custom-provider wiring from alias `coding` to alias `agentic`.
- [ ] 4.2 Update the managed Discord forced-response path and `/model` rejection messaging from router alias `coding` to router alias `agentic`.
- [ ] 4.3 Update router debug or metrics surfaces so they show usable-policy source, uncategorized or unused exclusions, active provider stickiness, and exhaustion-driven provider switches.

## 5. Validation And Documentation

- [ ] 5.1 Expand router unit and integration tests to cover NVIDIA catalog discovery, `agentic`-only alias exposure, top-five reserve plus top-three-active routing, uncategorized and unused inventory surfaces, session stickiness, exhaustion-gated provider failover, and inferred daily-limit suppression.
- [ ] 5.2 Update image and runtime validation so the managed config and Discord pinned route prove `ghostship-router` now means `agentic`.
- [ ] 5.3 Update `README.md`, `AGENTS.md`, and `CHANGELOG.md` to document agentic-only routing, strict provider order, NVIDIA catalog discovery, and the usable-ranking/unused-model contract.
