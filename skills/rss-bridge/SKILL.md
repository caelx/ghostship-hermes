---
name: rss-bridge
description: Operate RSS-Bridge from the Hermes image with `ghostship-rss-bridge`. Use when discovering bridges, inspecting live parameter schemas, finding a bridge for a source URL, generating stable feed URLs, or fetching feed output through the typed CLI.
---

# RSS-Bridge Skill

Use `ghostship-rss-bridge` when you need to turn a site or content source into a canonical RSS-Bridge feed URL.

## Prerequisites

- `RSS_BRIDGE_URL`

## Start Here

- Discover the live bridge inventory: `ghostship-rss-bridge list_bridges`
- Inspect one bridge schema before building parameters: `ghostship-rss-bridge describe_bridge <bridge>`
- Ask RSS-Bridge to suggest a bridge for a URL: `ghostship-rss-bridge find_feed <url>`
- See supported output formats: `ghostship-rss-bridge list_known_formats`

## Operating Model

- Commands mirror the API/client method names exactly.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- RSS-Bridge is action-driven, not CRUD-driven: “create a feed” means generating the right `action=display` URL.
- Start from live bridge metadata instead of guessing parameter names or contexts.

## Common Workflows

- Generate a feed URL when you already know the bridge:
  - `describe_bridge <bridge>`
  - `list_contexts <bridge>` if the bridge exposes multiple contexts
  - `build_url --bridge <bridge> --param key=value ...`
  - `fetch_url <url>` or `display --bridge ... --param ...` to verify the output
- Discover a bridge from a source URL:
  - `find_feed <url>`
  - `describe_bridge <bridge>` on the suggested candidate
  - `build_url ...` once the needed parameters are clear
- Inspect output before handing it to another system:
  - `display --bridge ... --param ...`
  - `fetch_url <url>`
  - Keep the JSON-wrapped response in view long enough to confirm the format and payload shape

## Guardrails

- Do not describe RSS-Bridge as storing server-side feed objects; it generates feed responses from URLs.
- Always inspect the live schema with `describe_bridge` or `list_contexts` before composing parameters.
- Prefer `build_url` for stable reusable feeds and `display` for quick validation.
- Keep formats explicit when another tool depends on a specific output type.
