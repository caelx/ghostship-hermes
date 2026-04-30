# Models And Reasoning

## Managed Model Contract

- Primary: `provider=opencode-go`, model `deepseek-v4-flash`.
- Fallback: `provider=opencode-go`, model `kimi-k2.6`.
- Agent reasoning: `reasoning_effort: high`.

The direct `opencode-go` provider hides the final upstream host behind an
aggregator, so Kimi/Moonshot-specific host detection is insufficient.

## Reasoning Replay Patch

When Hermes replays assistant tool-call history to OpenCode Go with reasoning
enabled, it must preserve tool-call replay while satisfying providers that require
`reasoning_content` on assistant tool-call messages.

The image patch:

- preserves existing `tool_calls`;
- preserves real `reasoning_content`;
- copies stored `reasoning` into `reasoning_content` when present;
- adds `reasoning_content: ""` for replayed `opencode-go` assistant messages
  with tool calls and no reasoning text, when reasoning is enabled.

Fallback logging records the primary model, fallback model, status, exception
type, and summarized provider error before switching models.
