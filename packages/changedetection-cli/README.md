# ghostship-changedetection

`ghostship-changedetection` is a JSON-first CLI for the stable upstream `changedetection.io` API. Commands mirror the upstream operation inventory in snake_case and keep non-JSON responses wrapped in JSON objects.

## Environment
- `CHANGEDETECTION_URL`
- `CHANGEDETECTION_API_KEY` for authenticated endpoints

## Command Contract
- Primary commands use snake_case names derived from the stable upstream API.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default, including wrapped text, YAML, and binary responses.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Write and delete commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-changedetection request`
- `ghostship-changedetection list_watches`
- `ghostship-changedetection create_watch`
- `ghostship-changedetection get_watch`
- `ghostship-changedetection update_watch`
- `ghostship-changedetection delete_watch`
- `ghostship-changedetection get_watch_history`
- `ghostship-changedetection get_watch_snapshot`
- `ghostship-changedetection get_watch_history_diff`
- `ghostship-changedetection get_watch_favicon`
- `ghostship-changedetection list_tags`
- `ghostship-changedetection create_tag`
- `ghostship-changedetection get_tag`
- `ghostship-changedetection update_tag`
- `ghostship-changedetection delete_tag`
- `ghostship-changedetection get_notifications`
- `ghostship-changedetection add_notifications`
- `ghostship-changedetection replace_notifications`
- `ghostship-changedetection delete_notifications`
- `ghostship-changedetection search_watches`
- `ghostship-changedetection import_watches`
- `ghostship-changedetection get_system_info`
- `ghostship-changedetection get_full_api_spec`

## Examples
```fish
ghostship-changedetection list_watches --pretty
ghostship-changedetection get_watch 095be615-a8ad-4c33-8e9c-c7612fbf6c9f --recheck --pretty
ghostship-changedetection create_tag --body-json '{"title":"Production Sites"}' --dry-run --pretty
ghostship-changedetection import_watches https://example.com https://example.org --tag production --dry-run --pretty
ghostship-changedetection get_full_api_spec --pretty
```
