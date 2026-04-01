---
name: rss-bridge
description: Discover RSS-Bridge bridges, inspect typed bridge schemas, and generate feed URLs with ghostship-rss-bridge. Output is native JSON.
---

# RSS-Bridge Skill

Use `ghostship-rss-bridge` when you need to discover a bridge, inspect its parameters, or generate a feed URL for another tool to consume.

## Prerequisites

- `RSS_BRIDGE_URL`

## Commands

- `ghostship-rss-bridge list-bridges`
- `ghostship-rss-bridge describe-bridge <bridge>`
- `ghostship-rss-bridge list-contexts <bridge>`
- `ghostship-rss-bridge list-known-formats`
- `ghostship-rss-bridge build-url --bridge ... --param key=value`
- `ghostship-rss-bridge find-feed <url>`
- `ghostship-rss-bridge detect <url>`
- `ghostship-rss-bridge display --bridge ... --param key=value`
- `ghostship-rss-bridge fetch-url <url>`

## Guidance

- RSS-Bridge does not create persistent server-side feed objects for you. “Creating a feed” means building a canonical `display` URL with the right bridge, context, format, and parameters.
- Start with `list-bridges` and `describe-bridge` to inspect the live instance schema instead of guessing parameter names.
- Use `find-feed` when you have a concrete URL and want RSS-Bridge to suggest candidate bridges automatically.
- Use `build-url` when you already know the bridge and want a stable feed URL to hand to an RSS reader.
- `display` and `fetch-url` wrap non-JSON feed payloads in JSON so the result stays agent-friendly.
