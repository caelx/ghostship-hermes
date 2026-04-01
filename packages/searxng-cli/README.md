# ghostship-searxng

`ghostship-searxng` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `SEARXNG_URL`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.

## Commands
- `ghostship-searxng request`
- `ghostship-searxng search web`

## Examples
```bash
ghostship-searxng search web "ghostship hermes" --limit 3 --pretty
```
```bash
ghostship-searxng request search --param q=test --param format=json
```
