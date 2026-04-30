# Firecrawl

## Environment

- Base URL: `FIRECRAWL_API_URL`, currently expected to point at the self-hosted
  API container, for example `http://firecrawl-api:3002`.
- API key: `FIRECRAWL_API_KEY`.
- Auth header: `Authorization: Bearer $FIRECRAWL_API_KEY`.

Use the local base URL from `.env`; do not hardcode `https://api.firecrawl.dev`.

## Endpoint Inventory

The public Firecrawl API reference documents these agent-relevant endpoint groups:

| Use | Method/path | Notes |
| --- | --- | --- |
| Scrape one URL | `POST /v1/scrape` | Returns markdown/html/links/screenshots/metadata depending on `formats` and options. |
| Batch scrape | `POST /v1/batch/scrape` | Asynchronous scrape for multiple URLs. |
| Batch status | `GET /v1/batch/scrape/{id}` | Poll batch scrape state and results. |
| Batch errors | `GET /v1/batch/scrape/{id}/errors` | Inspect failed URLs. |
| Cancel batch | `DELETE /v1/batch/scrape/{id}` | Stop a running batch. |
| Crawl site | `POST /v1/crawl` | Crawl multiple pages from a starting URL. |
| Crawl status | `GET /v1/crawl/{id}` | Poll crawl state and pages. |
| Crawl errors | `GET /v1/crawl/{id}/errors` | Inspect crawl failures. |
| Active crawls | `GET /v1/crawl/active` | List active crawl jobs. |
| Cancel crawl | `DELETE /v1/crawl/{id}` | Stop a crawl. |
| Map site | `POST /v1/map` | Discover URLs on a site quickly. |
| Search | `POST /v1/search` | Search the web, optionally returning scraped content. |
| Extract | `POST /v1/extract` | Structured extraction over webpages using prompt/schema. |
| Extract status | `GET /v1/extract/{id}` | Poll async extraction state. |

Newer Firecrawl docs also describe v2 endpoints. Prefer v1 for the current
self-hosted deployment unless probing the local service proves v2 is available.

## Minimal Python Call

```python
import os
import requests

base = os.environ["FIRECRAWL_API_URL"].rstrip("/")
key = os.environ["FIRECRAWL_API_KEY"]

response = requests.post(
    f"{base}/v1/scrape",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"url": "https://example.com", "formats": ["markdown"], "onlyMainContent": True},
    timeout=120,
)
response.raise_for_status()
data = response.json()
print(data["data"].get("markdown", ""))
```

## Useful Request Options

- `formats`: common values include `markdown`, `html`, `rawHtml`, `links`, `screenshot`.
- `onlyMainContent`: remove navigation/footer/sidebar content.
- `includeTags` / `excludeTags`: constrain extraction by tag selectors.
- `waitFor`: milliseconds to wait before content capture.
- `timeout`: request timeout in milliseconds.
- `actions`: browser actions such as wait, click, type, scroll, screenshot, scrape,
  JavaScript execution, or PDF generation.
- `jsonOptions`: schema/prompt-based extraction settings.
- `blockAds`, `removeBase64Images`, `skipTlsVerification`, `mobile`, `headers`.

## When To Use Firecrawl

Use Firecrawl when the task needs page-to-markdown extraction, site crawling,
search with scrape results, or structured extraction across URLs. Use local
`agent-browser` when the task needs logged-in browsing, precise interaction,
visual confirmation, or browser session continuity.
