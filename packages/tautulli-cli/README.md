# ghostship-tautulli

`ghostship-tautulli` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `TAUTULLI_URL`
- `TAUTULLI_API_KEY`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `call` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
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
