# Shared CLI Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize every `ghostship-*` CLI around a shared transport and CLI contract with dry-run support for writes/deletes, fixed timeouts, and consistent JSON errors.

**Architecture:** Add a shared Python package for request specs, transport, and CLI helpers, then migrate every service client and CLI to use it. Write/delete operations gain request-builder methods so `--dry-run` can render the exact outbound request object without making a network call.

**Tech Stack:** Python, Typer, httpx, pytest, Nix flakes

---

### Task 1: Add the shared CLI contract package

**Files:**
- Create: `packages/ghostship-cli-contract/pyproject.toml`
- Create: `packages/ghostship-cli-contract/.python-version`
- Create: `packages/ghostship-cli-contract/uv.lock`
- Create: `packages/ghostship-cli-contract/src/ghostship_cli_contract/__init__.py`
- Create: `packages/ghostship-cli-contract/src/ghostship_cli_contract/cli.py`
- Create: `packages/ghostship-cli-contract/src/ghostship_cli_contract/http.py`
- Create: `packages/ghostship-cli-contract/src/ghostship_cli_contract/models.py`
- Create: `packages/ghostship-cli-contract/src/ghostship_cli_contract/errors.py`
- Create: `packages/ghostship-cli-contract/src/ghostship_cli_contract/py.typed`
- Create: `packages/ghostship-cli-contract/tests/test_cli_contract.py`
- Modify: `flake.nix`
- Modify: `docs/python-utilities.md`

- [ ] Define `RequestSpec`, error types, exit-code mapping, and shared JSON helpers.
- [ ] Implement shared timeout-aware `httpx` transport helpers with test-only Cloudflare header injection.
- [ ] Add unit tests covering dry-run serialization, timeout defaults, and error translation.
- [ ] Wire the package into the flake and Python utility workflow docs.

### Task 2: Migrate the direct-HTTP JSON utilities

**Files:**
- Modify: `packages/bazarr-cli/src/ghostship_bazarr/client.py`
- Modify: `packages/bazarr-cli/src/ghostship_bazarr/cli.py`
- Modify: `packages/bazarr-cli/tests/test_cli.py`
- Modify: `packages/bazarr-cli/tests/test_client.py`
- Modify: `packages/cloakbrowser-cli/src/ghostship_cloakbrowser/client.py`
- Modify: `packages/cloakbrowser-cli/src/ghostship_cloakbrowser/cli.py`
- Modify: `packages/cloakbrowser-cli/tests/test_cli.py`
- Modify: `packages/cloakbrowser-cli/tests/test_client.py`
- Modify: `packages/grimmory-cli/src/ghostship_grimmory/client.py`
- Modify: `packages/grimmory-cli/src/ghostship_grimmory/cli.py`
- Modify: `packages/grimmory-cli/tests/test_cli.py`
- Modify: `packages/grimmory-cli/tests/test_client.py`
- Modify: `packages/plex-cli/src/ghostship_plex/client.py`
- Modify: `packages/plex-cli/src/ghostship_plex/cli.py`
- Modify: `packages/plex-cli/tests/test_cli.py`
- Modify: `packages/plex-cli/tests/test_client.py`
- Modify: `packages/romm-cli/src/ghostship_romm/client.py`
- Modify: `packages/romm-cli/src/ghostship_romm/cli.py`
- Modify: `packages/romm-cli/tests/test_cli.py`
- Modify: `packages/romm-cli/tests/test_client.py`
- Modify: `packages/searxng-cli/src/ghostship_searxng/client.py`
- Modify: `packages/searxng-cli/src/ghostship_searxng/cli.py`
- Modify: `packages/searxng-cli/tests/test_cli.py`
- Modify: `packages/pricebuddy-cli/src/ghostship_pricebuddy/client.py`
- Modify: `packages/pricebuddy-cli/src/ghostship_pricebuddy/cli.py`
- Modify: `packages/pricebuddy-cli/tests/test_cli.py`
- Modify: `packages/pricebuddy-cli/tests/test_client.py`
- Modify: `packages/rss-bridge-cli/src/ghostship_rss_bridge/client.py`
- Modify: `packages/rss-bridge-cli/src/ghostship_rss_bridge/cli.py`
- Modify: `packages/rss-bridge-cli/tests/test_cli.py`
- Modify: `packages/rss-bridge-cli/tests/test_client.py`

- [ ] Move these clients onto the shared transport layer with default `30.0` second timeouts.
- [ ] Add `build_<operation>_request` methods for write/delete operations.
- [ ] Add `--timeout` to all commands and `--dry-run` to all write/delete commands.
- [ ] Update tests to assert stable dry-run JSON and consistent exit codes.

### Task 3: Migrate Arr-style clients

**Files:**
- Modify: `packages/sonarr-cli/src/ghostship_sonarr/client.py`
- Modify: `packages/sonarr-cli/src/ghostship_sonarr/cli.py`
- Modify: `packages/sonarr-cli/tests/test_cli.py`
- Modify: `packages/sonarr-cli/tests/test_client.py`
- Modify: `packages/radarr-cli/src/ghostship_radarr/client.py`
- Modify: `packages/radarr-cli/src/ghostship_radarr/cli.py`
- Modify: `packages/radarr-cli/tests/test_cli.py`
- Modify: `packages/radarr-cli/tests/test_client.py`
- Modify: `packages/prowlarr-cli/src/ghostship_prowlarr/client.py`
- Modify: `packages/prowlarr-cli/src/ghostship_prowlarr/cli.py`
- Modify: `packages/prowlarr-cli/tests/test_cli.py`
- Modify: `packages/prowlarr-cli/tests/test_client.py`

- [ ] Standardize Arr clients on the shared transport layer.
- [ ] Add request builders for write/delete operations and command-style POST payloads.
- [ ] Add timeout and dry-run support to the CLIs without changing command names.
- [ ] Extend unit tests to cover request builders, timeouts, and JSON errors.

### Task 4: Migrate download/automation and RPC-style clients

**Files:**
- Modify: `packages/qbittorrent-cli/src/ghostship_qbittorrent/client.py`
- Modify: `packages/qbittorrent-cli/src/ghostship_qbittorrent/cli.py`
- Modify: `packages/qbittorrent-cli/tests/test_cli.py`
- Modify: `packages/qbittorrent-cli/tests/test_client.py`
- Modify: `packages/nzbget-cli/src/ghostship_nzbget/client.py`
- Modify: `packages/nzbget-cli/src/ghostship_nzbget/cli.py`
- Modify: `packages/nzbget-cli/tests/test_cli.py`
- Modify: `packages/nzbget-cli/tests/test_client.py`
- Modify: `packages/pyload-ng-cli/src/ghostship_pyload_ng/client.py`
- Modify: `packages/pyload-ng-cli/src/ghostship_pyload_ng/cli.py`
- Modify: `packages/pyload-ng-cli/tests/test_cli.py`
- Modify: `packages/pyload-ng-cli/tests/test_client.py`
- Modify: `packages/flaresolverr-cli/src/ghostship_flaresolverr/client.py`
- Modify: `packages/flaresolverr-cli/src/ghostship_flaresolverr/cli.py`
- Modify: `packages/flaresolverr-cli/tests/test_cli.py`
- Modify: `packages/flaresolverr-cli/tests/test_client.py`
- Modify: `packages/synology-cli/src/ghostship_synology/client.py`
- Modify: `packages/synology-cli/src/ghostship_synology/cli.py`
- Modify: `packages/synology-cli/tests/test_cli.py`
- Modify: `packages/synology-cli/tests/test_client.py`
- Modify: `packages/tautulli-cli/src/ghostship_tautulli/client.py`
- Modify: `packages/tautulli-cli/src/ghostship_tautulli/cli.py`
- Modify: `packages/tautulli-cli/tests/test_cli.py`
- Modify: `packages/tautulli-cli/tests/test_client.py`

- [ ] Adapt the shared request model to handle form posts, JSON-RPC payloads, and action-style APIs.
- [ ] Add request builders and dry-run support for all write/delete commands.
- [ ] Normalize error handling and timeout configuration across these clients.
- [ ] Add unit coverage for request-spec generation and CLI error behavior.

### Task 5: Update repo docs, skills, and live tests

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `AGENTS.md`
- Modify: `tests/live/test_live_services.py`
- Modify: `tests/live/conftest.py`
- Modify: `packages/*/README.md` for every migrated package
- Modify: `skills/*/SKILL.md` for every migrated service skill

- [ ] Document the shared CLI contract, default timeout, dry-run behavior, and stable error model.
- [ ] Update all service skills so Hermes knows every write/delete command supports `--dry-run` and every command supports `--timeout`.
- [ ] Extend read-only live integration tests to cover representative `--timeout` usage.
- [ ] Record the new repo rule in `AGENTS.md` so future utilities inherit the shared contract.

### Task 6: Verify and commit

**Files:**
- Modify: repository working tree as needed for final fixes

- [ ] Run `python3 scripts/python_utility.py test` for every migrated package.
- [ ] Run `nix develop -c python -m pytest tests/live/test_live_services.py -q`.
- [ ] Run `git diff --check`.
- [ ] Commit with a focused conventional commit message.
