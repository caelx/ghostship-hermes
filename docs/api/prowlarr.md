# Prowlarr API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [prowlarr-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/prowlarr-openapi.json)
- Companion reference: this file

## Service Identity

- Product: Prowlarr
- Version mirrored in repo: `1.0.0`
- Base API URL: `http(s)://<host>/api/v1`
- Primary auth: `X-Api-Key` header

## Raw Spec Summary

- Format: OpenAPI JSON
- Path count: `93`
- Canonical source quality: official OpenAPI plus repo summary
- Server default in mirrored spec: `{protocol}://{hostpath}`

## Full Endpoint and Use-Case Inventory

The inventory below is taken directly from the mirrored upstream machine-readable specification.

### ApiInfo
- `GET /api`

### AppProfile
- `POST /api/v1/appprofile`
- `GET /api/v1/appprofile`
- `DELETE /api/v1/appprofile/{id}`
- `PUT /api/v1/appprofile/{id}`
- `GET /api/v1/appprofile/{id}`
- `GET /api/v1/appprofile/schema`

### Application
- `GET /api/v1/applications/{id}`
- `PUT /api/v1/applications/{id}`
- `DELETE /api/v1/applications/{id}`
- `GET /api/v1/applications`
- `POST /api/v1/applications`
- `PUT /api/v1/applications/bulk`
- `DELETE /api/v1/applications/bulk`
- `GET /api/v1/applications/schema`
- `POST /api/v1/applications/test`
- `POST /api/v1/applications/testall`
- `POST /api/v1/applications/action/{name}`

### Authentication
- `POST /login`
- `GET /logout`

### Backup
- `GET /api/v1/system/backup`
- `DELETE /api/v1/system/backup/{id}`
- `POST /api/v1/system/backup/restore/{id}`
- `POST /api/v1/system/backup/restore/upload`

### Command
- `GET /api/v1/command/{id}`
- `DELETE /api/v1/command/{id}`
- `POST /api/v1/command`
- `GET /api/v1/command`

### CustomFilter
- `GET /api/v1/customfilter/{id}`
- `PUT /api/v1/customfilter/{id}`
- `DELETE /api/v1/customfilter/{id}`
- `GET /api/v1/customfilter`
- `POST /api/v1/customfilter`

### DevelopmentConfig
- `PUT /api/v1/config/development/{id}`
- `GET /api/v1/config/development/{id}`
- `GET /api/v1/config/development`

### DownloadClient
- `GET /api/v1/downloadclient/{id}`
- `PUT /api/v1/downloadclient/{id}`
- `DELETE /api/v1/downloadclient/{id}`
- `GET /api/v1/downloadclient`
- `POST /api/v1/downloadclient`
- `PUT /api/v1/downloadclient/bulk`
- `DELETE /api/v1/downloadclient/bulk`
- `GET /api/v1/downloadclient/schema`
- `POST /api/v1/downloadclient/test`
- `POST /api/v1/downloadclient/testall`
- `POST /api/v1/downloadclient/action/{name}`

### DownloadClientConfig
- `GET /api/v1/config/downloadclient/{id}`
- `PUT /api/v1/config/downloadclient/{id}`
- `GET /api/v1/config/downloadclient`

### FileSystem
- `GET /api/v1/filesystem`
- `GET /api/v1/filesystem/type`

### Health
- `GET /api/v1/health`

### History
- `GET /api/v1/history`
- `GET /api/v1/history/since`
- `GET /api/v1/history/indexer`

### HostConfig
- `GET /api/v1/config/host/{id}`
- `PUT /api/v1/config/host/{id}`
- `GET /api/v1/config/host`

### Indexer
- `GET /api/v1/indexer/{id}`
- `PUT /api/v1/indexer/{id}`
- `DELETE /api/v1/indexer/{id}`
- `GET /api/v1/indexer`
- `POST /api/v1/indexer`
- `PUT /api/v1/indexer/bulk`
- `DELETE /api/v1/indexer/bulk`
- `GET /api/v1/indexer/schema`
- `POST /api/v1/indexer/test`
- `POST /api/v1/indexer/testall`
- `POST /api/v1/indexer/action/{name}`

### IndexerDefaultCategories
- `GET /api/v1/indexer/categories`

### IndexerProxy
- `GET /api/v1/indexerproxy/{id}`
- `PUT /api/v1/indexerproxy/{id}`
- `DELETE /api/v1/indexerproxy/{id}`
- `GET /api/v1/indexerproxy`
- `POST /api/v1/indexerproxy`
- `GET /api/v1/indexerproxy/schema`
- `POST /api/v1/indexerproxy/test`
- `POST /api/v1/indexerproxy/testall`
- `POST /api/v1/indexerproxy/action/{name}`

### IndexerStats
- `GET /api/v1/indexerstats`

### IndexerStatus
- `GET /api/v1/indexerstatus`

### Localization
- `GET /api/v1/localization`
- `GET /api/v1/localization/options`

### Log
- `GET /api/v1/log`

### LogFile
- `GET /api/v1/log/file`
- `GET /api/v1/log/file/{filename}`

### Newznab
- `GET /api/v1/indexer/{id}/newznab`
- `GET /{id}/api`
- `GET /api/v1/indexer/{id}/download`
- `GET /{id}/download`

### Notification
- `GET /api/v1/notification/{id}`
- `PUT /api/v1/notification/{id}`
- `DELETE /api/v1/notification/{id}`
- `GET /api/v1/notification`
- `POST /api/v1/notification`
- `GET /api/v1/notification/schema`
- `POST /api/v1/notification/test`
- `POST /api/v1/notification/testall`
- `POST /api/v1/notification/action/{name}`

### Ping
- `GET /ping`
- `HEAD /ping`

### Search
- `POST /api/v1/search`
- `GET /api/v1/search`
- `POST /api/v1/search/bulk`

### StaticResource
- `GET /login`
- `GET /content/{path}`
- `GET /`
- `GET /{path}`

### System
- `GET /api/v1/system/status`
- `GET /api/v1/system/routes`
- `GET /api/v1/system/routes/duplicate`
- `POST /api/v1/system/shutdown`
- `POST /api/v1/system/restart`

### Tag
- `GET /api/v1/tag/{id}`
- `PUT /api/v1/tag/{id}`
- `DELETE /api/v1/tag/{id}`
- `GET /api/v1/tag`
- `POST /api/v1/tag`

### TagDetails
- `GET /api/v1/tag/detail/{id}`
- `GET /api/v1/tag/detail`

### Task
- `GET /api/v1/system/task`
- `GET /api/v1/system/task/{id}`

### UiConfig
- `PUT /api/v1/config/ui/{id}`
- `GET /api/v1/config/ui/{id}`
- `GET /api/v1/config/ui`

### Update
- `GET /api/v1/update`

### UpdateLogFile
- `GET /api/v1/log/file/update`
- `GET /api/v1/log/file/update/{filename}`

## Repo Utility Surface

`ghostship-prowlarr` currently uses:
- indexers
- search
- applications
- history
- system status
- commands
- indexer stats and status

## Source Material

- Local mirrored raw spec: [prowlarr-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/prowlarr-openapi.json)
