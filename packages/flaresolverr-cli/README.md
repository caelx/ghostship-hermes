# ghostship-flaresolverr

`ghostship-flaresolverr` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `FLARESOLVERR_URL`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use the generic passthrough command only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.

## Commands
- `ghostship-flaresolverr command`
- `ghostship-flaresolverr request_get`
- `ghostship-flaresolverr request_post`
- `ghostship-flaresolverr sessions_create`
- `ghostship-flaresolverr sessions_list`
- `ghostship-flaresolverr sessions_destroy`

## Examples
```bash
ghostship-flaresolverr sessions_list
```
```bash
ghostship-flaresolverr request_get https://example.com --pretty
```
```bash
ghostship-flaresolverr command sessions.list
```
