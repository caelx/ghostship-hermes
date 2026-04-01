---
name: searxng
description: Use when you need SearXNG search results or raw JSON endpoint access.
---

# ghostship-searxng

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `SEARXNG_URL`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
- `ghostship-searxng request`
- `ghostship-searxng search web`

## Examples
```bash
ghostship-searxng search web "ghostship hermes" --limit 3 --pretty
```
```bash
ghostship-searxng request search --param q=test --param format=json
```
