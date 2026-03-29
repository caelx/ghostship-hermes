# SearXNG API Spec Sheet

## Service Identity

- Product: SearXNG
- Base UI URL: `http(s)://<host>`
- Search API endpoints: `/` and `/search`
- Methods supported by the official docs: `GET` and `POST`
- Primary auth: none by default for the search API

## Canonical Source Quality

- Official docs
- No machine-readable OpenAPI mirror is currently stored in this repo

## Full Search API Surface

### Entry points
- `GET /`
- `POST /`
- `GET /search`
- `POST /search`

### Documented request parameters
- `q`: required search query
- `categories`: comma-separated categories
- `engines`: comma-separated engine selection
- `language`: result language code
- `pageno`: result page number
- `time_range`: `day`, `month`, or `year` when supported by engines
- `format`: response format such as `json`, `csv`, or `rss`
- `results_on_new_tab`
- `image_proxy`
- `autocomplete`
- `safesearch`
- `theme`
- `enabled_plugins`
- `disabled_plugins`
- `enabled_engines`
- `disabled_engines`

### Documented response formats
- `json`
- `csv`
- `rss`

### JSON response surface called out by the official docs
- query metadata
- result list
- infoboxes
- suggestions
- answers
- corrections
- engine list and timing data when configured by the instance

## Repo Utility Surface

`ghostship-searxng` currently uses `GET /search` with `format=json` plus `q`, `categories`, `language`, and `safesearch`, but the broader search parameter surface above is documented upstream.

## Source Material

- Official developer docs: <https://docs.searxng.org/dev/search_api.html>
