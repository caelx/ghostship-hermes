---
name: cloakbrowser
description: Use when you need exact CloakBrowser Manager operations and profile lifecycle control from the CLI.
---

# ghostship-cloakbrowser

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `CLOAKBROWSER_URL`
- `CLOAKBROWSER_TOKEN (optional)`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
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
