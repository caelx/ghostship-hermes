# ghostship-plex

`ghostship-plex` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `PLEX_URL`
- `PLEX_TOKEN`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.

## Commands
- `ghostship-plex request`
- `ghostship-plex get_identity`
- `ghostship-plex get_server_info`
- `ghostship-plex get_status_sessions`
- `ghostship-plex get_activities`
- `ghostship-plex get_library_sections`
- `ghostship-plex get_library_section`
- `ghostship-plex get_library_filters`
- `ghostship-plex get_library_sorts`
- `ghostship-plex refresh_library`
- `ghostship-plex get_metadata`
- `ghostship-plex get_metadata_children`
- `ghostship-plex get_playlists`
- `ghostship-plex get_playlist_items`
- `ghostship-plex get_collections`
- `ghostship-plex get_preferences`
- `ghostship-plex get_butler_tasks`
- `ghostship-plex get_statistics`
- `ghostship-plex terminate_session`
- `ghostship-plex get_session`

## Examples
```bash
ghostship-plex get_server_info --pretty
```
```bash
ghostship-plex get_library_sections --pretty
```
```bash
ghostship-plex get_metadata 12345
```
