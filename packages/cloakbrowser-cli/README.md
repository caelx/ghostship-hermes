# ghostship-cloakbrowser

`ghostship-cloakbrowser` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `CLOAKBROWSER_URL`
- `CLOAKBROWSER_TOKEN (optional)`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-cloakbrowser request`
- `ghostship-cloakbrowser get_system_status`
- `ghostship-cloakbrowser auth_status`
- `ghostship-cloakbrowser auth_login`
- `ghostship-cloakbrowser auth_logout`
- `ghostship-cloakbrowser list_profiles`
- `ghostship-cloakbrowser get_profile`
- `ghostship-cloakbrowser create_profile`
- `ghostship-cloakbrowser update_profile`
- `ghostship-cloakbrowser delete_profile`
- `ghostship-cloakbrowser launch_profile`
- `ghostship-cloakbrowser stop_profile`
- `ghostship-cloakbrowser get_profile_status`
- `ghostship-cloakbrowser get_clipboard`
- `ghostship-cloakbrowser set_clipboard`
- `ghostship-cloakbrowser get_cdp_info`

## Examples
```bash
ghostship-cloakbrowser list_profiles
```
```bash
ghostship-cloakbrowser create_profile automation --platform windows --humanize
```
```bash
ghostship-cloakbrowser get_cdp_info profile-123
```
