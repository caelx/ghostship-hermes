## 1. Wrapper Routing Guard

- [x] 1.1 Inspect the existing Hermes wrapper patch and identify the gateway turn-resolution paths that create agents for Discord sessions.
- [x] 1.2 Add a repo-owned helper in the wrapped Hermes gateway code that detects managed Discord free-response sessions from the existing Discord channel contract.
- [x] 1.3 Force matched Discord free-response turns onto the local router `agentic` path before agent creation instead of relying on upstream session-switch behavior.
- [x] 1.4 Reject `/model` in Discord free-response sessions and clear any stale session override state for that context.

## 2. Discord Runtime Cleanup

- [x] 2.1 Locate the old repo-owned Discord plugin steering path that never worked and confirm its remaining write set.
- [x] 2.2 Remove that unsupported Discord plugin path so the wrapper-enforced router pin is the only supported behavior.

## 3. Validation

- [x] 3.1 Add or extend managed runtime validation to prove Discord free-response sessions stay pinned to `http://127.0.0.1:8788/v1` with the `agentic` alias.
- [x] 3.2 Add or extend validation to prove `/model` does not persist or apply a conflicting session override in Discord free-response channels.
- [x] 3.3 Run the relevant repo validation for the changed wrapper/runtime paths and record any residual gaps.
