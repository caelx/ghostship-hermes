# ghostship-bazarr

`ghostship-bazarr` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `BAZARR_URL`
- `BAZARR_API_KEY`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.

## Commands
- `ghostship-bazarr request`
- `ghostship-bazarr get_badges`
- `ghostship-bazarr get_episodes`
- `ghostship-bazarr get_wanted_episodes`
- `ghostship-bazarr get_movies`
- `ghostship-bazarr get_wanted_movies`
- `ghostship-bazarr get_series`
- `ghostship-bazarr get_providers`
- `ghostship-bazarr get_subtitles`
- `ghostship-bazarr get_system_health`
- `ghostship-bazarr get_system_jobs`
- `ghostship-bazarr get_system_tasks`
- `ghostship-bazarr get_system_status`
- `ghostship-bazarr search_subtitles_missing`
- `ghostship-bazarr get_episodes_history`
- `ghostship-bazarr get_movies_history`
- `ghostship-bazarr get_episodes_blacklist`
- `ghostship-bazarr get_movies_blacklist`

## Examples
```bash
ghostship-bazarr get_system_status --pretty
```
```bash
ghostship-bazarr get_episodes --series-id 123 --pretty
```
```bash
ghostship-bazarr request GET system/status
```
