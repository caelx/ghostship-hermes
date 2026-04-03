---
name: feed
description: Use the upstream `feed` CLI in the Hermes image for persistent RSS monitoring, subscription management, unread triage, full-text search, and event tracking. Use when adding feeds, scanning what is new, searching historical entries, reading full posts, or turning RSS-Bridge-generated feed URLs into durable monitored sources.
---

# Feed Skill

Use `feed` as the persistent RSS reader and monitoring engine in the Hermes image.

## Prerequisites

- `feed` on `PATH`
- `FEED_DB_PATH`
- `RSS_BRIDGE_URL` when the source needs RSS-Bridge to produce a canonical feed URL

The runtime defaults `FEED_DB_PATH` to `$HERMES_HOME/feed/feed.db`, so feed state stays inside the active Hermes profile.

## Start Here

- Inspect database state: `feed get stats`
- Scan recent unread entries: `feed get entries --limit 25`
- Search historical coverage: `feed search "query"`
- Read one entry in full: `feed get entry <id>`
- If the source does not expose a direct feed URL, use `ghostship-rss-bridge` first

## Operating Model

- `feed` is the durable state layer: subscriptions, unread state, starred items, and full-text search live in its SQLite database.
- `ghostship-rss-bridge` is the source-discovery layer: use it to discover or build canonical feed URLs, then add those URLs to `feed`.
- Default output is table, which is usually the most efficient format for scanning.
- `feed get entries` auto-fetches when feeds are stale; use `--no-fetch` only when you explicitly want a read without refresh.

## Common Workflows

- Add a normal feed:
  - `feed add feed <url>`
  - `feed get feeds`
  - `feed fetch` if you want an immediate refresh
- Add a source that needs RSS-Bridge:
  - Use `ghostship-rss-bridge find_feed <url>` or `ghostship-rss-bridge build_url --bridge ... --param ...`
  - Take the canonical display URL from RSS-Bridge
  - `feed add feed <rss-bridge-url>`
  - `feed get feeds` to verify the subscription landed
- Monitor for events or topics:
  - `feed get entries --limit 50`
  - `feed search "topic or entity"`
  - `feed get entry <id>` for the few posts that matter
  - Use starred or read state only after the user wants triage state updated
- Recover or move subscriptions:
  - `feed export > backup.opml`
  - `feed import <file-or-url.opml>`

## Triage Patterns

- For “what is new”: start with `feed get entries --limit 25`
- For “what changed about X”: use `feed search "X"` before scanning unread blindly
- For “monitor this site over time”: add it once, then rely on `feed get entries`, `feed search`, and `feed get feeds`
- For “monitor a social or unsupported source”: generate the feed URL with RSS-Bridge first, then store it in `feed`

## Guardrails

- Do not use `feed` as a replacement for RSS-Bridge schema discovery; generate the right feed URL first when needed.
- Do not mark entries read or starred automatically unless the user asked for triage state changes.
- Keep the default table output for scanning; switch to JSON only when a downstream tool truly needs structured output.
- Confirm the active Hermes profile before assuming which feed database you are reading.
