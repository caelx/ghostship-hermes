---
name: tautulli
description: Use when you need Tautulli history, activity, user, or control endpoints through exact method-name commands.
---

# ghostship-tautulli

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `TAUTULLI_URL`
- `TAUTULLI_API_KEY`
- Prefer the dedicated snake_case command first. Use `call` only as fallback.

## Common Commands
- `ghostship-tautulli call`
- `ghostship-tautulli get_server_status`
- `ghostship-tautulli get_tautulli_info`
- `ghostship-tautulli get_status`
- `ghostship-tautulli get_activity`
- `ghostship-tautulli terminate_session`
- `ghostship-tautulli get_history`
- `ghostship-tautulli get_libraries`
- `ghostship-tautulli get_library_user_stats`
- `ghostship-tautulli get_users`
- `ghostship-tautulli get_user_player_stats`
- `ghostship-tautulli get_user_watch_time_stats`
- `ghostship-tautulli get_metadata`
- `ghostship-tautulli search`
- `ghostship-tautulli restart`

## Examples
```bash
ghostship-tautulli get_tautulli_info --pretty
```
```bash
ghostship-tautulli get_activity --pretty
```
```bash
ghostship-tautulli get_users --pretty
```
