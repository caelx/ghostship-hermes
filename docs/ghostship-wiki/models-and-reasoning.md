# Models And Reasoning

## Managed Model Contract

- Primary: `provider=custom:ollama-pro`, model `deepseek-v4-pro:cloud`.
- Fallback: `provider=opencode-go`, model `deepseek-v4-pro`.
- Agent reasoning: `reasoning_effort: high`.

The OpenCode Go fallback hides the final upstream host behind an aggregator, so
host-specific reasoning detection is insufficient.

## Reasoning Replay Patch

When Hermes replays assistant history to OpenCode Go with reasoning enabled, it
must preserve tool-call replay while satisfying providers that require
`reasoning_content` on prior assistant messages.

The image patch:

- preserves existing `tool_calls`;
- preserves real `reasoning_content`;
- copies stored `reasoning` into `reasoning_content` when present;
- adds `reasoning_content: ""` for replayed `opencode-go` assistant messages
  with no stored reasoning text, when reasoning is enabled.

Fallback logging records the primary model, fallback model, status, exception
type, and summarized provider error before switching models.
