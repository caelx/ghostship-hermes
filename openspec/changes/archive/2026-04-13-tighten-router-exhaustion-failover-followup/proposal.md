## Why

Live validation on `chill-penguin` showed three runtime gaps in the managed Hermes image contract:

- the Discord `/model` picker does not surface the named `ghostship-router` custom provider, even though the CLI picker does
- the `ghostship-router-channel-guidance` hook can suppress all future warnings after one failed Discord post
- the managed config still carries stale `ghostship-router` auth and Discord mention behavior that no longer matches the desired runtime contract

## What Changes

- patch the wrapped Hermes gateway and model-switch helper so Discord model picking can enumerate named `custom_providers`, including `ghostship-router`
- make router-channel warnings delivery-aware and repeat every 60 seconds during active non-router chats
- align the managed image scaffold and config-convergence logic with the intended runtime contract: `ghostship-router` is a no-auth custom provider, `discord.require_mention` is false, and the configured fallback remains `openai-codex / gpt-5.4-mini`

## Impact

- Affected code: `packages/hermes-agent-wrapped/package.nix`, `packages/hermes-image/nixos-module.nix`, router-channel hook code, and image/runtime tests
- Affected systems: Discord model selection, Ghostship router advisory warnings, and managed config convergence on boot/image replacement
