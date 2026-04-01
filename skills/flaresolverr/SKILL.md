---
name: flaresolverr
description: Use when you need FlareSolverr request or session commands with names that match the client methods.
---

# ghostship-flaresolverr

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `FLARESOLVERR_URL`
- Prefer the dedicated snake_case command first.

## Common Commands
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
