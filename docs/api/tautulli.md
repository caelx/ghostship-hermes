# Tautulli API Spec Sheet

## Service Identity

- Product: Tautulli
- Base API URL: `http(s)://<host>/api/v2`
- Invocation pattern: `GET /api/v2?apikey=<key>&cmd=<command>`
- Primary auth: API key query parameter

## Canonical Source Quality

- Official API documentation
- No mirrored OpenAPI artifact is currently stored in this repo

## Full Endpoint and Use-Case Inventory

Tautulli uses a single HTTP endpoint and selects behavior with the `cmd` query parameter. The official API reference documents these commands:

### Configuration, backup, and maintenance
- `add_newsletter_config`
- `add_notifier_config`
- `backup_config`
- `backup_db`
- `docs`
- `docs_md`
- `download_config`
- `download_database`
- `import_config`
- `import_database`
- `restart`
- `status`
- `server_status`
- `update`
- `update_check`

### Cleanup and delete operations
- `delete_all_library_history`
- `delete_all_user_history`
- `delete_cache`
- `delete_export`
- `delete_history`
- `delete_hosted_images`
- `delete_image_cache`
- `delete_library`
- `delete_login_log`
- `delete_lookup_info`
- `delete_media_info_cache`
- `delete_mobile_device`
- `delete_newsletter`
- `delete_newsletter_log`
- `delete_notification_log`
- `delete_notifier`
- `delete_recently_added`
- `delete_synced_item`
- `delete_temp_sessions`
- `delete_user`
- `undelete_library`
- `undelete_user`

### Logs, diagnostics, and low-level tooling
- `arnold`
- `download_export`
- `download_log`
- `download_plex_log`
- `get_apikey`
- `get_date_formats`
- `get_geoip_lookup`
- `get_logs`
- `get_plex_log`
- `get_server_friendly_name`
- `get_server_id`
- `get_server_identity`
- `get_server_info`
- `get_server_list`
- `get_server_pref`
- `get_servers_info`
- `get_settings`
- `get_whois_lookup`
- `sql`

### Activity, history, and statistics
- `get_activity`
- `get_history`
- `get_home_stats`
- `get_plays_by_date`
- `get_plays_by_dayofweek`
- `get_plays_by_hourofday`
- `get_plays_by_source_resolution`
- `get_plays_by_stream_resolution`
- `get_plays_by_stream_type`
- `get_plays_by_top_10_platforms`
- `get_plays_by_top_10_users`
- `get_plays_per_month`
- `get_pms_update`
- `get_stream_data`
- `get_stream_type_by_top_10_platforms`
- `get_stream_type_by_top_10_users`

### Libraries, metadata, exports, and search
- `edit_library`
- `export_metadata`
- `get_children_metadata`
- `get_collections_table`
- `get_export_fields`
- `get_exports_table`
- `get_libraries`
- `get_libraries_table`
- `get_library`
- `get_library_media_info`
- `get_library_names`
- `get_library_user_stats`
- `get_library_watch_time_stats`
- `get_metadata`
- `get_new_rating_keys`
- `get_old_rating_keys`
- `get_playlists_table`
- `get_recently_added`
- `search`
- `update_metadata_details`

### Users, sessions, sync, and devices
- `edit_user`
- `get_synced_items`
- `get_user`
- `get_user_ips`
- `get_user_logins`
- `get_user_names`
- `get_user_player_stats`
- `get_user_watch_time_stats`
- `get_users`
- `get_users_table`
- `logout_user_session`
- `register_device`
- `set_mobile_device_config`
- `terminate_session`

### Notifications and newsletters
- `get_newsletter_config`
- `get_newsletter_log`
- `get_newsletters`
- `get_notification_log`
- `get_notifier_config`
- `get_notifier_parameters`
- `get_notifiers`
- `notify`
- `notify_newsletter`
- `notify_recently_added`
- `set_newsletter_config`
- `set_notifier_config`

### Reader, image, and presentation helpers
- `get_playlists_table`
- `pms_image_proxy`
- `refresh_libraries_list`
- `refresh_users_list`

## Repo Utility Surface

`ghostship-tautulli` currently uses a small subset of the commands above for status, activity, history, libraries, users, metadata, search, and restart operations.

## Notes

- Tautulli’s upstream contract is command-centric rather than path-centric.
- The full documented surface is the command inventory above, all executed via the same `/api/v2` endpoint.

## Source Material

- Official API docs: <https://docs.tautulli.com/extending-tautulli/api-reference>
- Official Markdown export: <https://docs.tautulli.com/extending-tautulli/api-reference.md>
