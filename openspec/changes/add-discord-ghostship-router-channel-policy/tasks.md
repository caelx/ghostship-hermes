## 1. Managed Runtime Model Contract

- [ ] 1.1 Update `packages/hermes-image/nixos-module.nix` so the managed primary model remains `opencode-go/minimax-m2.7`.
- [ ] 1.2 Change the managed fallback model contract to `openai-codex/gpt-5.4-mini`.
- [ ] 1.3 Add one named `custom_providers` entry for `ghostship-router` pointing at `http://127.0.0.1:8788/v1`.
- [ ] 1.4 Verify the managed config still keeps auxiliary and compression tasks on the direct Gemini Flash-Lite path.

## 2. Managed Env Projection

- [ ] 2.1 Extend the managed Discord env allowlist to project `GHOSTSHIP_ROUTER_CHANNEL` into `/home/hermes/.hermes/.env`.
- [ ] 2.2 Remove this router-channel workflow's dependence on `DISCORD_FREE_RESPONSE_CHANNELS` from the managed runtime contract and generated docs.
- [ ] 2.3 Add or update tests that validate the rendered managed `.env` contains `GHOSTSHIP_ROUTER_CHANNEL` when configured and omits stale values when unset.

## 3. Advisory Discord Guidance

- [ ] 3.1 Implement a supported-interface advisory hook under the managed Hermes hook/plugin staging path for the configured router channel.
- [ ] 3.2 Detect whether the active session in `GHOSTSHIP_ROUTER_CHANNEL` is using the named `ghostship-router` custom provider with a router-exposed model id.
- [ ] 3.3 Query or cache the router `/v1/models` inventory and build one full `/model custom:ghostship-router:<model>` command per available model id.
- [ ] 3.4 Send a bold warning message in the configured router channel on normal message start when the session is not using a router-backed model.
- [ ] 3.5 Send the same warning message after `/reset` in the configured router channel.

## 4. Validation And Docs

- [ ] 4.1 Add or update validation coverage for the managed config so `ghostship-router` appears as a named custom provider and Codex appears as the configured fallback.
- [ ] 4.2 Add or update validation for the advisory router-channel warning behavior, including the `/reset` reminder path.
- [ ] 4.3 Update `README.md` and any runtime env documentation to describe `ghostship-router`, `GHOSTSHIP_ROUTER_CHANNEL`, the Codex fallback contract, and the advisory warning semantics.
- [ ] 4.4 Run the relevant OpenSpec status and targeted repo validation commands and record any remaining gaps before implementation closes.
