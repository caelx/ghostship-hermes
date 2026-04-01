# ghostship-rss-bridge

`ghostship-rss-bridge` is a JSON-first CLI for the RSS-Bridge action surface. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `RSS_BRIDGE_URL`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.

## Commands
- `ghostship-rss-bridge list_bridges`
- `ghostship-rss-bridge describe_bridge <bridge>`
- `ghostship-rss-bridge list_contexts <bridge>`
- `ghostship-rss-bridge list_known_formats`
- `ghostship-rss-bridge build_url --bridge ... --param key=value`
- `ghostship-rss-bridge find_feed <url>`
- `ghostship-rss-bridge detect <url>`
- `ghostship-rss-bridge display --bridge ... --param key=value`
- `ghostship-rss-bridge fetch_url <feed-url>`

## Examples
```bash
ghostship-rss-bridge list_bridges --active-only --pretty
ghostship-rss-bridge describe_bridge RedditBridge --pretty
ghostship-rss-bridge build_url --bridge RedditBridge --format Atom --context Subreddit --param subreddit=nixos --pretty
ghostship-rss-bridge find_feed https://www.instagram.com/nasa/ --format Atom --pretty
```
