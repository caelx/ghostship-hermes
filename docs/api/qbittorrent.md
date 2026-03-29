# qBittorrent WebUI API Spec Sheet

## Service Identity

- Product: qBittorrent WebUI API
- Base API URL: `http(s)://<host>/api/v2`
- Authentication model: cookie-based login via `POST /api/v2/auth/login`

## Canonical Source Quality

- Official qBittorrent wiki
- No mirrored OpenAPI artifact is currently stored in this repo

## Full Endpoint and Use-Case Inventory

The official WebUI API wiki documents these endpoint families and use cases:

### Authentication
- `POST /api/v2/auth/login`: create a session cookie
- `POST /api/v2/auth/logout`: end the authenticated session

### Application
- `GET /api/v2/app/version`: server version
- `GET /api/v2/app/webapiVersion`: WebUI API version
- `GET /api/v2/app/buildInfo`: build details
- `POST /api/v2/app/shutdown`: stop qBittorrent
- `GET /api/v2/app/preferences`: read preferences
- `POST /api/v2/app/setPreferences`: update preferences
- `GET /api/v2/app/defaultSavePath`: resolve the default save path

### Log
- `GET /api/v2/log/main`: main application log
- `GET /api/v2/log/peers`: peer log

### Sync
- `GET /api/v2/sync/maindata`: incremental global state sync
- `GET /api/v2/sync/torrentPeers`: incremental peer-state sync for a torrent

### Transfer
- `GET /api/v2/transfer/info`: global transfer statistics
- `GET /api/v2/transfer/speedLimitsMode`: alternate-speed toggle state
- `POST /api/v2/transfer/toggleSpeedLimitsMode`: flip alternate-speed mode
- `GET /api/v2/transfer/downloadLimit`: global download limit
- `POST /api/v2/transfer/setDownloadLimit`: set global download limit
- `GET /api/v2/transfer/uploadLimit`: global upload limit
- `POST /api/v2/transfer/setUploadLimit`: set global upload limit
- `POST /api/v2/transfer/banPeers`: ban peers by IP

### Torrents
- `GET /api/v2/torrents/info`: list torrents with filters
- `GET /api/v2/torrents/properties`: generic torrent properties
- `GET /api/v2/torrents/trackers`: tracker list
- `GET /api/v2/torrents/webseeds`: web seed list
- `GET /api/v2/torrents/files`: file list
- `GET /api/v2/torrents/pieceStates`: piece-state map
- `GET /api/v2/torrents/pieceHashes`: piece hashes
- `POST /api/v2/torrents/pause`: pause torrents
- `POST /api/v2/torrents/resume`: resume torrents
- `POST /api/v2/torrents/delete`: delete torrents
- `POST /api/v2/torrents/recheck`: force recheck
- `POST /api/v2/torrents/reannounce`: reannounce
- `POST /api/v2/torrents/editTracker`: edit tracker URL
- `POST /api/v2/torrents/removeTrackers`: remove trackers
- `POST /api/v2/torrents/addPeers`: add peers manually
- `POST /api/v2/torrents/add`: add torrent or magnet
- `POST /api/v2/torrents/addTrackers`: add trackers
- `POST /api/v2/torrents/increasePrio`: raise queue priority
- `POST /api/v2/torrents/decreasePrio`: lower queue priority
- `POST /api/v2/torrents/topPrio`: move to top priority
- `POST /api/v2/torrents/bottomPrio`: move to bottom priority
- `POST /api/v2/torrents/filePrio`: change file priority
- `POST /api/v2/torrents/downloadLimit`: get per-torrent download limit
- `POST /api/v2/torrents/setDownloadLimit`: set per-torrent download limit
- `POST /api/v2/torrents/setShareLimits`: set ratio and seeding limits
- `POST /api/v2/torrents/uploadLimit`: get per-torrent upload limit
- `POST /api/v2/torrents/setUploadLimit`: set per-torrent upload limit
- `POST /api/v2/torrents/setLocation`: move save location
- `POST /api/v2/torrents/rename`: rename torrent
- `POST /api/v2/torrents/setCategory`: assign category
- `GET /api/v2/torrents/categories`: list categories
- `POST /api/v2/torrents/createCategory`: create category
- `POST /api/v2/torrents/editCategory`: edit category
- `POST /api/v2/torrents/removeCategories`: remove categories
- `POST /api/v2/torrents/addTags`: add tags
- `POST /api/v2/torrents/removeTags`: remove tags
- `GET /api/v2/torrents/tags`: list tags
- `POST /api/v2/torrents/createTags`: create tags
- `POST /api/v2/torrents/deleteTags`: delete tags
- `POST /api/v2/torrents/setAutoManagement`: set automatic management
- `POST /api/v2/torrents/toggleSequentialDownload`: toggle sequential download
- `POST /api/v2/torrents/toggleFirstLastPiecePrio`: toggle first-last piece priority
- `POST /api/v2/torrents/setForceStart`: force start
- `POST /api/v2/torrents/setSuperSeeding`: super seeding toggle
- `POST /api/v2/torrents/renameFile`: rename file inside torrent
- `POST /api/v2/torrents/renameFolder`: rename folder inside torrent

### RSS
- `POST /api/v2/rss/addFolder`: create RSS folder
- `POST /api/v2/rss/addFeed`: create RSS feed
- `POST /api/v2/rss/removeItem`: remove feed or folder
- `POST /api/v2/rss/moveItem`: move feed or folder
- `GET /api/v2/rss/items`: list feeds and folders
- `POST /api/v2/rss/markAsRead`: mark article as read
- `POST /api/v2/rss/refreshItem`: refresh feed or folder
- `POST /api/v2/rss/setRule`: create or update auto-download rule
- `POST /api/v2/rss/renameRule`: rename rule
- `POST /api/v2/rss/removeRule`: delete rule
- `GET /api/v2/rss/rules`: list auto-download rules
- `GET /api/v2/rss/matchingArticles`: articles matching a rule

### Search
- `POST /api/v2/search/start`: start a search job
- `POST /api/v2/search/stop`: stop a search job
- `GET /api/v2/search/status`: list search-job status
- `GET /api/v2/search/results`: fetch search results
- `POST /api/v2/search/delete`: delete a search job
- `GET /api/v2/search/plugins`: list search plugins
- `POST /api/v2/search/installPlugin`: install a search plugin
- `POST /api/v2/search/uninstallPlugin`: uninstall a search plugin
- `POST /api/v2/search/enablePlugin`: enable or disable a plugin
- `POST /api/v2/search/updatePlugins`: update installed plugins

## Repo Utility Surface

`ghostship-qbittorrent` currently uses auth, app, log, sync, transfer, selected torrent operations, search, and RSS endpoints, but the official API surface above is broader.

## Source Material

- Official wiki: <https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)>
- Official raw wiki markdown: <https://raw.githubusercontent.com/wiki/qbittorrent/qBittorrent/WebUI-API-%28qBittorrent-4.1%29.md>
