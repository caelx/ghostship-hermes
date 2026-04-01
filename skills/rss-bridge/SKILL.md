---
name: rss-bridge
description: Discover RSS-Bridge bridges, inspect typed bridge schemas, and generate feed URLs with ghostship-rss-bridge. Output is native JSON.
---

# RSS-Bridge Skill

Use `ghostship-rss-bridge` when you need to discover a bridge, inspect its parameters, or generate a feed URL for another tool to consume.

## Prerequisites

- `RSS_BRIDGE_URL`

## Contract

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Every invocation accepts `--timeout`; default hard timeout is `30` seconds.

## Commands

- `ghostship-rss-bridge list_bridges`
- `ghostship-rss-bridge describe_bridge <bridge>`
- `ghostship-rss-bridge list_contexts <bridge>`
- `ghostship-rss-bridge list_known_formats`
- `ghostship-rss-bridge build_url --bridge ... --param key=value`
- `ghostship-rss-bridge find_feed <url>`
- `ghostship-rss-bridge detect <url>`
- `ghostship-rss-bridge display --bridge ... --param key=value`
- `ghostship-rss-bridge fetch_url <url>`

## Guidance

- RSS-Bridge does not create persistent server-side feed objects. “Creating a feed” means building a canonical `display` URL with the right bridge, context, format, and parameters.
- Start with `list_bridges` and `describe_bridge` to inspect the live instance schema instead of guessing parameter names.
- Use `find_feed` when you have a concrete URL and want RSS-Bridge to suggest candidate bridges automatically.
- Use `build_url` when you already know the bridge and want a stable feed URL to hand to an RSS reader.
- `display` and `fetch_url` wrap non-JSON feed payloads in JSON so the result stays agent-friendly.
