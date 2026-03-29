# Sonarr API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [sonarr-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/sonarr-openapi.json)
- Companion reference: this file

## Service Identity

- Product: Sonarr
- Version mirrored in repo: `3.0.0`
- Base API URL: `http(s)://<host>/api/v3`
- Primary auth: `X-Api-Key` header

## Raw Spec Summary

- Format: OpenAPI JSON
- Path count: `162`
- Canonical source quality: official OpenAPI plus repo summary
- Server default in mirrored spec: `{protocol}://{hostpath}`

## Full Endpoint and Use-Case Inventory

The inventory below is taken directly from the mirrored upstream machine-readable specification.

### ApiInfo
- `GET /api`

### Authentication
- `POST /login`
- `GET /logout`

### AutoTagging
- `POST /api/v3/autotagging`
- `GET /api/v3/autotagging`
- `PUT /api/v3/autotagging/{id}`
- `DELETE /api/v3/autotagging/{id}`
- `GET /api/v3/autotagging/{id}`
- `GET /api/v3/autotagging/schema`

### Backup
- `GET /api/v3/system/backup`
- `DELETE /api/v3/system/backup/{id}`
- `POST /api/v3/system/backup/restore/{id}`
- `POST /api/v3/system/backup/restore/upload`

### Blocklist
- `GET /api/v3/blocklist`
- `DELETE /api/v3/blocklist/{id}`
- `DELETE /api/v3/blocklist/bulk`

### Calendar
- `GET /api/v3/calendar`
- `GET /api/v3/calendar/{id}`

### CalendarFeed
- `GET /feed/v3/calendar/sonarr.ics`

### Command
- `POST /api/v3/command`
- `GET /api/v3/command`
- `DELETE /api/v3/command/{id}`
- `GET /api/v3/command/{id}`

### CustomFilter
- `GET /api/v3/customfilter`
- `POST /api/v3/customfilter`
- `PUT /api/v3/customfilter/{id}`
- `DELETE /api/v3/customfilter/{id}`
- `GET /api/v3/customfilter/{id}`

### CustomFormat
- `GET /api/v3/customformat`
- `POST /api/v3/customformat`
- `PUT /api/v3/customformat/{id}`
- `DELETE /api/v3/customformat/{id}`
- `GET /api/v3/customformat/{id}`
- `PUT /api/v3/customformat/bulk`
- `DELETE /api/v3/customformat/bulk`
- `GET /api/v3/customformat/schema`

### Cutoff
- `GET /api/v3/wanted/cutoff`
- `GET /api/v3/wanted/cutoff/{id}`

### DelayProfile
- `POST /api/v3/delayprofile`
- `GET /api/v3/delayprofile`
- `DELETE /api/v3/delayprofile/{id}`
- `PUT /api/v3/delayprofile/{id}`
- `GET /api/v3/delayprofile/{id}`
- `PUT /api/v3/delayprofile/reorder/{id}`

### DiskSpace
- `GET /api/v3/diskspace`

### DownloadClient
- `GET /api/v3/downloadclient`
- `POST /api/v3/downloadclient`
- `PUT /api/v3/downloadclient/{id}`
- `DELETE /api/v3/downloadclient/{id}`
- `GET /api/v3/downloadclient/{id}`
- `PUT /api/v3/downloadclient/bulk`
- `DELETE /api/v3/downloadclient/bulk`
- `GET /api/v3/downloadclient/schema`
- `POST /api/v3/downloadclient/test`
- `POST /api/v3/downloadclient/testall`
- `POST /api/v3/downloadclient/action/{name}`

### DownloadClientConfig
- `GET /api/v3/config/downloadclient`
- `PUT /api/v3/config/downloadclient/{id}`
- `GET /api/v3/config/downloadclient/{id}`

### Episode
- `GET /api/v3/episode`
- `PUT /api/v3/episode/{id}`
- `GET /api/v3/episode/{id}`
- `PUT /api/v3/episode/monitor`

### EpisodeFile
- `GET /api/v3/episodefile`
- `PUT /api/v3/episodefile/{id}`
- `DELETE /api/v3/episodefile/{id}`
- `GET /api/v3/episodefile/{id}`
- `PUT /api/v3/episodefile/editor`
- `DELETE /api/v3/episodefile/bulk`
- `PUT /api/v3/episodefile/bulk`

### FileSystem
- `GET /api/v3/filesystem`
- `GET /api/v3/filesystem/type`
- `GET /api/v3/filesystem/mediafiles`

### Health
- `GET /api/v3/health`

### History
- `GET /api/v3/history`
- `GET /api/v3/history/since`
- `GET /api/v3/history/series`
- `POST /api/v3/history/failed/{id}`

### HostConfig
- `GET /api/v3/config/host`
- `PUT /api/v3/config/host/{id}`
- `GET /api/v3/config/host/{id}`

### ImportList
- `GET /api/v3/importlist`
- `POST /api/v3/importlist`
- `PUT /api/v3/importlist/{id}`
- `DELETE /api/v3/importlist/{id}`
- `GET /api/v3/importlist/{id}`
- `PUT /api/v3/importlist/bulk`
- `DELETE /api/v3/importlist/bulk`
- `GET /api/v3/importlist/schema`
- `POST /api/v3/importlist/test`
- `POST /api/v3/importlist/testall`
- `POST /api/v3/importlist/action/{name}`

### ImportListConfig
- `GET /api/v3/config/importlist`
- `PUT /api/v3/config/importlist/{id}`
- `GET /api/v3/config/importlist/{id}`

### ImportListExclusion
- `GET /api/v3/importlistexclusion`
- `POST /api/v3/importlistexclusion`
- `GET /api/v3/importlistexclusion/paged`
- `PUT /api/v3/importlistexclusion/{id}`
- `DELETE /api/v3/importlistexclusion/{id}`
- `GET /api/v3/importlistexclusion/{id}`
- `DELETE /api/v3/importlistexclusion/bulk`

### Indexer
- `GET /api/v3/indexer`
- `POST /api/v3/indexer`
- `PUT /api/v3/indexer/{id}`
- `DELETE /api/v3/indexer/{id}`
- `GET /api/v3/indexer/{id}`
- `PUT /api/v3/indexer/bulk`
- `DELETE /api/v3/indexer/bulk`
- `GET /api/v3/indexer/schema`
- `POST /api/v3/indexer/test`
- `POST /api/v3/indexer/testall`
- `POST /api/v3/indexer/action/{name}`

### IndexerConfig
- `GET /api/v3/config/indexer`
- `PUT /api/v3/config/indexer/{id}`
- `GET /api/v3/config/indexer/{id}`

### IndexerFlag
- `GET /api/v3/indexerflag`

### Language
- `GET /api/v3/language`
- `GET /api/v3/language/{id}`

### LanguageProfile
- `POST /api/v3/languageprofile`
- `GET /api/v3/languageprofile`
- `DELETE /api/v3/languageprofile/{id}`
- `PUT /api/v3/languageprofile/{id}`
- `GET /api/v3/languageprofile/{id}`

### LanguageProfileSchema
- `GET /api/v3/languageprofile/schema`

### Localization
- `GET /api/v3/localization`
- `GET /api/v3/localization/language`
- `GET /api/v3/localization/{id}`

### Log
- `GET /api/v3/log`

### LogFile
- `GET /api/v3/log/file`
- `GET /api/v3/log/file/{filename}`

### ManualImport
- `GET /api/v3/manualimport`
- `POST /api/v3/manualimport`

### MediaCover
- `GET /api/v3/mediacover/{seriesId}/{filename}`

### MediaManagementConfig
- `GET /api/v3/config/mediamanagement`
- `PUT /api/v3/config/mediamanagement/{id}`
- `GET /api/v3/config/mediamanagement/{id}`

### Metadata
- `GET /api/v3/metadata`
- `POST /api/v3/metadata`
- `PUT /api/v3/metadata/{id}`
- `DELETE /api/v3/metadata/{id}`
- `GET /api/v3/metadata/{id}`
- `GET /api/v3/metadata/schema`
- `POST /api/v3/metadata/test`
- `POST /api/v3/metadata/testall`
- `POST /api/v3/metadata/action/{name}`

### Missing
- `GET /api/v3/wanted/missing`
- `GET /api/v3/wanted/missing/{id}`

### NamingConfig
- `GET /api/v3/config/naming`
- `PUT /api/v3/config/naming/{id}`
- `GET /api/v3/config/naming/{id}`
- `GET /api/v3/config/naming/examples`

### Notification
- `GET /api/v3/notification`
- `POST /api/v3/notification`
- `PUT /api/v3/notification/{id}`
- `DELETE /api/v3/notification/{id}`
- `GET /api/v3/notification/{id}`
- `GET /api/v3/notification/schema`
- `POST /api/v3/notification/test`
- `POST /api/v3/notification/testall`
- `POST /api/v3/notification/action/{name}`

### Parse
- `GET /api/v3/parse`

### Ping
- `GET /ping`
- `HEAD /ping`

### QualityDefinition
- `PUT /api/v3/qualitydefinition/{id}`
- `GET /api/v3/qualitydefinition/{id}`
- `GET /api/v3/qualitydefinition`
- `PUT /api/v3/qualitydefinition/update`
- `GET /api/v3/qualitydefinition/limits`

### QualityProfile
- `POST /api/v3/qualityprofile`
- `GET /api/v3/qualityprofile`
- `DELETE /api/v3/qualityprofile/{id}`
- `PUT /api/v3/qualityprofile/{id}`
- `GET /api/v3/qualityprofile/{id}`

### QualityProfileSchema
- `GET /api/v3/qualityprofile/schema`

### Queue
- `DELETE /api/v3/queue/{id}`
- `DELETE /api/v3/queue/bulk`
- `GET /api/v3/queue`

### QueueAction
- `POST /api/v3/queue/grab/{id}`
- `POST /api/v3/queue/grab/bulk`

### QueueDetails
- `GET /api/v3/queue/details`

### QueueStatus
- `GET /api/v3/queue/status`

### Release
- `POST /api/v3/release`
- `GET /api/v3/release`

### ReleaseProfile
- `POST /api/v3/releaseprofile`
- `GET /api/v3/releaseprofile`
- `DELETE /api/v3/releaseprofile/{id}`
- `PUT /api/v3/releaseprofile/{id}`
- `GET /api/v3/releaseprofile/{id}`

### ReleasePush
- `POST /api/v3/release/push`

### RemotePathMapping
- `POST /api/v3/remotepathmapping`
- `GET /api/v3/remotepathmapping`
- `DELETE /api/v3/remotepathmapping/{id}`
- `PUT /api/v3/remotepathmapping/{id}`
- `GET /api/v3/remotepathmapping/{id}`

### RenameEpisode
- `GET /api/v3/rename`

### RootFolder
- `POST /api/v3/rootfolder`
- `GET /api/v3/rootfolder`
- `DELETE /api/v3/rootfolder/{id}`
- `GET /api/v3/rootfolder/{id}`

### SeasonPass
- `POST /api/v3/seasonpass`

### Series
- `GET /api/v3/series`
- `POST /api/v3/series`
- `GET /api/v3/series/{id}`
- `PUT /api/v3/series/{id}`
- `DELETE /api/v3/series/{id}`

### SeriesEditor
- `PUT /api/v3/series/editor`
- `DELETE /api/v3/series/editor`

### SeriesFolder
- `GET /api/v3/series/{id}/folder`

### SeriesImport
- `POST /api/v3/series/import`

### SeriesLookup
- `GET /api/v3/series/lookup`

### StaticResource
- `GET /login`
- `GET /content/{path}`
- `GET /`
- `GET /{path}`

### System
- `GET /api/v3/system/status`
- `GET /api/v3/system/routes`
- `GET /api/v3/system/routes/duplicate`
- `POST /api/v3/system/shutdown`
- `POST /api/v3/system/restart`

### Tag
- `GET /api/v3/tag`
- `POST /api/v3/tag`
- `PUT /api/v3/tag/{id}`
- `DELETE /api/v3/tag/{id}`
- `GET /api/v3/tag/{id}`

### TagDetails
- `GET /api/v3/tag/detail`
- `GET /api/v3/tag/detail/{id}`

### Task
- `GET /api/v3/system/task`
- `GET /api/v3/system/task/{id}`

### UiConfig
- `PUT /api/v3/config/ui/{id}`
- `GET /api/v3/config/ui/{id}`
- `GET /api/v3/config/ui`

### Update
- `GET /api/v3/update`

### UpdateLogFile
- `GET /api/v3/log/file/update`
- `GET /api/v3/log/file/update/{filename}`

## Repo Utility Surface

`ghostship-sonarr` currently uses:
- series CRUD and lookup
- episode listing and update
- commands
- queue and history
- system status
- wanted missing and cutoff
- blocklist
- tags
- root folders
- quality profiles

## Source Material

- Local mirrored raw spec: [sonarr-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/sonarr-openapi.json)
