# Bazarr API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [bazarr-swagger.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/bazarr-swagger.json)
- Companion reference: this file

## Service Identity

- Product: Bazarr
- Version mirrored in repo: `1.5.6`
- Base API URL: `http(s)://<host>/api`
- Primary auth: `X-Api-Key` header or `apikey` query parameter

## Raw Spec Summary

- Format: Swagger JSON
- Path count: `51`
- Canonical source quality: official Swagger plus repo summary

## Full Endpoint and Use-Case Inventory

The inventory below is taken directly from the mirrored upstream machine-readable specification.

### Badges
- `GET /badges`: Get badges count to update the UI

### Episodes
- `GET /episodes`: List episodes metadata for specific series or episodes

### Episodes Blacklist
- `DELETE /episodes/blacklist`: Delete an episodes subtitles from blacklist
- `POST /episodes/blacklist`: Add an episodes subtitles to blacklist
- `GET /episodes/blacklist`: List blacklisted episodes subtitles

### Episodes History
- `GET /episodes/history`: List episodes history events

### Episodes Subtitles
- `PATCH /episodes/subtitles`: Download an episode subtitles
- `POST /episodes/subtitles`: Upload an episode subtitles
- `DELETE /episodes/subtitles`: Delete an episode subtitles

### Episodes Wanted
- `GET /episodes/wanted`: List episodes wanted subtitles

### Files Browser for Bazarr
- `GET /files`: List Bazarr file system content

### Files Browser for Radarr
- `GET /files/radarr`: List Radarr file system content

### Files Browser for Sonarr
- `GET /files/sonarr`: List Sonarr file system content

### History Statistics
- `GET /history/stats`: Get history statistics

### Movies
- `PATCH /movies`: Run actions on specific movies
- `POST /movies`: Update specific movies languages profile
- `GET /movies`: List movies metadata for specific movies

### Movies Blacklist
- `DELETE /movies/blacklist`: Delete a movies subtitles from blacklist
- `POST /movies/blacklist`: Add a movies subtitles to blacklist
- `GET /movies/blacklist`: List blacklisted movies subtitles

### Movies History
- `GET /movies/history`: List movies history events

### Movies Subtitles
- `PATCH /movies/subtitles`: Download a movie subtitles
- `POST /movies/subtitles`: Upload a movie subtitles
- `DELETE /movies/subtitles`: Delete a movie subtitles

### Movies Wanted
- `GET /movies/wanted`: List movies wanted subtitles

### Plex Authentication
- `POST /plex/apikey`: post_plex_api_key
- `GET /plex/autopulse/config`: get_plex_autopulse_config
- `POST /plex/encrypt-apikey`: post_plex_encrypt_api_key
- `GET /plex/oauth/libraries`: get_plex_libraries
- `POST /plex/oauth/logout`: post_plex_logout
- `POST /plex/oauth/pin`: post_plex_pin
- `GET /plex/oauth/pin`: get_plex_pin
- `GET /plex/oauth/pin/{pin_id}/check`: get_plex_pin_check
- `GET /plex/oauth/servers`: get_plex_servers
- `GET /plex/oauth/validate`: get_plex_validate
- `POST /plex/select-server`: post_plex_select_server
- `GET /plex/select-server`: get_plex_select_server
- `POST /plex/test-connection`: post_plex_test_connection
- `GET /plex/test-connection`: get_plex_test_connection
- `POST /plex/webhook/create`: post_plex_webhook_create
- `POST /plex/webhook/delete`: post_plex_webhook_delete
- `GET /plex/webhook/list`: get_plex_webhook_list

### Providers
- `POST /providers`: Reset providers status
- `GET /providers`: Get providers status

### Providers Episodes
- `POST /providers/episodes`: Manually download an episode subtitles
- `GET /providers/episodes`: Search manually for an episode subtitles

### Providers Movies
- `POST /providers/movies`: Manually download a movie subtitles
- `GET /providers/movies`: Search manually for a movie subtitles

### Series
- `PATCH /series`: Run actions on specific series
- `POST /series`: Update specific series languages profile
- `GET /series`: List series metadata for specific series

### Subtitles
- `PATCH /subtitles`: Apply mods/tools on external subtitles
- `GET /subtitles`: Return available audio and embedded subtitles tracks with external subtitles

### Subtitles Info
- `GET /subtitles/info`: Guessit over subtitles filename

### System Announcements
- `POST /system/announcements`: Mark announcement as dismissed
- `GET /system/announcements`: List announcements relative to Bazarr

### System Backups
- `PATCH /system/backups`: Restore a backup file
- `DELETE /system/backups`: Delete a backup file
- `POST /system/backups`: Create a new backup
- `GET /system/backups`: List backup files

### System Health
- `GET /system/health`: List health issues

### System Jobs
- `PATCH /system/jobs`: Empty a specific jobs queue
- `DELETE /system/jobs`: Delete a job from the queue
- `POST /system/jobs`: Force start, move to top or move to bottom of the queue a specific job
- `GET /system/jobs`: List jobs from the queue

### System Languages
- `GET /system/languages`: List languages for history filter or for language filter menu

### System Languages Profiles
- `GET /system/languages/profiles`: List languages profiles

### System Logs
- `DELETE /system/logs`: Force log rotation and create a new log file
- `GET /system/logs`: List log entries

### System Ping
- `GET /system/ping`: Return status and http 200

### System Releases
- `GET /system/releases`: Get Bazarr releases

### System Searches
- `GET /system/searches`: List results from query

### System Status
- `GET /system/status`: Return environment information and versions

### System Tasks
- `POST /system/tasks`: Run task
- `GET /system/tasks`: List tasks

### Webhooks Plex
- `POST /webhooks/plex`: Trigger subtitles search on play media event in Plex

### Webhooks Radarr
- `POST /webhooks/radarr`: Search for missing subtitles based on Radarr webhooks

### Webhooks Sonarr
- `POST /webhooks/sonarr`: Search for missing subtitles based on Sonarr webhooks

### systemSettings
- `POST /system/webhooks/test`: Test external webhook connection

## Repo Utility Surface

`ghostship-bazarr` currently uses:
- badges
- episodes and wanted episodes
- movies and wanted movies
- series
- providers
- subtitles and subtitle search
- system health, jobs, tasks, and status
- episode and movie history
- episode and movie blacklist

## Source Material

- Local mirrored raw spec: [bazarr-swagger.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/bazarr-swagger.json)
