# ghostship-rss-bridge

Typed CLI utility for the RSS-Bridge action surface.

## Environment Variables

- `RSS_BRIDGE_URL`: Base URL of the RSS-Bridge instance.

## Commands

- `ghostship-rss-bridge list-bridges`
- `ghostship-rss-bridge describe-bridge <bridge>`
- `ghostship-rss-bridge list-contexts <bridge>`
- `ghostship-rss-bridge list-known-formats`
- `ghostship-rss-bridge build-url --bridge ... --param key=value`
- `ghostship-rss-bridge find-feed <url>`
- `ghostship-rss-bridge detect <url>`
- `ghostship-rss-bridge display --bridge ... --param key=value`
- `ghostship-rss-bridge fetch-url <feed-url>`

All commands emit JSON by default. Use `--pretty` for formatted JSON.

## Examples

```bash
ghostship-rss-bridge list-bridges --active-only --pretty
ghostship-rss-bridge describe-bridge RedditBridge --pretty
ghostship-rss-bridge build-url --bridge RedditBridge --format Atom --context Subreddit --param subreddit=nixos --pretty
ghostship-rss-bridge find-feed https://www.instagram.com/nasa/ --format Atom --pretty
```
