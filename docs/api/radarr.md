# Radarr API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [radarr-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/radarr-openapi.json)
- Companion reference: this file

## Service Identity

- Product: Radarr
- Version mirrored in repo: `3.0.0`
- Base API URL: `http(s)://<host>/api/v3`
- Primary auth: `X-Api-Key` header

## Raw Spec Summary

- Format: OpenAPI JSON
- Path count: `164`
- Canonical source quality: official OpenAPI plus repo summary
- Server default in mirrored spec: `{protocol}://{hostpath}`

## Full Endpoint and Use-Case Inventory

The inventory below is taken directly from the mirrored upstream machine-readable specification.

### AlternativeTitle
- `GET /api/v3/alttitle`
- `GET /api/v3/alttitle/{id}`

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
- `GET /api/v3/blocklist/movie`
- `DELETE /api/v3/blocklist/{id}`
- `DELETE /api/v3/blocklist/bulk`

### Calendar
- `GET /api/v3/calendar`

### CalendarFeed
- `GET /feed/v3/calendar/radarr.ics`

### Collection
- `GET /api/v3/collection`
- `PUT /api/v3/collection`
- `PUT /api/v3/collection/{id}`
- `GET /api/v3/collection/{id}`

### Command
- `POST /api/v3/command`
- `GET /api/v3/command`
- `DELETE /api/v3/command/{id}`
- `GET /api/v3/command/{id}`

### Credit
- `GET /api/v3/credit`
- `GET /api/v3/credit/{id}`

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

### ExtraFile
- `GET /api/v3/extrafile`

### FileSystem
- `GET /api/v3/filesystem`
- `GET /api/v3/filesystem/type`
- `GET /api/v3/filesystem/mediafiles`

### Health
- `GET /api/v3/health`

### History
- `GET /api/v3/history`
- `GET /api/v3/history/since`
- `GET /api/v3/history/movie`
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
- `GET /api/v3/exclusions`
- `POST /api/v3/exclusions`
- `GET /api/v3/exclusions/paged`
- `PUT /api/v3/exclusions/{id}`
- `DELETE /api/v3/exclusions/{id}`
- `GET /api/v3/exclusions/{id}`
- `POST /api/v3/exclusions/bulk`
- `DELETE /api/v3/exclusions/bulk`

### ImportListMovies
- `GET /api/v3/importlist/movie`
- `POST /api/v3/importlist/movie`

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

### Localization
- `GET /api/v3/localization`
- `GET /api/v3/localization/language`

### Log
- `GET /api/v3/log`

### LogFile
- `GET /api/v3/log/file`
- `GET /api/v3/log/file/{filename}`

### ManualImport
- `GET /api/v3/manualimport`
- `POST /api/v3/manualimport`

### MediaCover
- `GET /api/v3/mediacover/{movieId}/{filename}`

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

### MetadataConfig
- `GET /api/v3/config/metadata`
- `PUT /api/v3/config/metadata/{id}`
- `GET /api/v3/config/metadata/{id}`

### Missing
- `GET /api/v3/wanted/missing`

### Movie
- `GET /api/v3/movie`
- `POST /api/v3/movie`
- `PUT /api/v3/movie/{id}`
- `DELETE /api/v3/movie/{id}`
- `GET /api/v3/movie/{id}`

### MovieEditor
- `PUT /api/v3/movie/editor`
- `DELETE /api/v3/movie/editor`

### MovieFile
- `GET /api/v3/moviefile`
- `PUT /api/v3/moviefile/{id}`
- `DELETE /api/v3/moviefile/{id}`
- `GET /api/v3/moviefile/{id}`
- `PUT /api/v3/moviefile/editor`
- `DELETE /api/v3/moviefile/bulk`
- `PUT /api/v3/moviefile/bulk`

### MovieFolder
- `GET /api/v3/movie/{id}/folder`

### MovieImport
- `POST /api/v3/movie/import`

### MovieLookup
- `GET /api/v3/movie/lookup/tmdb`
- `GET /api/v3/movie/lookup/imdb`
- `GET /api/v3/movie/lookup`

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

### RenameMovie
- `GET /api/v3/rename`

### RootFolder
- `POST /api/v3/rootfolder`
- `GET /api/v3/rootfolder`
- `DELETE /api/v3/rootfolder/{id}`
- `GET /api/v3/rootfolder/{id}`

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

`ghostship-radarr` currently uses:
- movie CRUD and lookup
- commands
- queue and history
- system status
- wanted missing and cutoff
- blocklist
- tags
- root folders
- quality profiles

## Source Material

- Local mirrored raw spec: [radarr-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/radarr-openapi.json)
