# RomM API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [romm-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/romm-openapi.json)
- Companion reference: this file

## Service Identity

- Product: RomM
- Version mirrored in repo: `4.7.0`
- Base API URL: `http(s)://<host>/api`
- Primary auth: Bearer token from `POST /api/token` using the OAuth password grant

## Raw Spec Summary

- Format: OpenAPI JSON
- Path count: `98`
- Canonical source quality: official OpenAPI plus repo summary

## Full Endpoint and Use-Case Inventory

The inventory below is taken directly from the mirrored upstream machine-readable specification.

### auth
- `POST /api/login`: Login
- `POST /api/logout`: Logout
- `POST /api/token`: Token
- `GET /api/login/openid`: Login Via Openid
- `GET /api/oauth/openid`: Auth Openid
- `POST /api/forgot-password`: Request Password Reset
- `POST /api/reset-password`: Reset Password

### collections
- `POST /api/collections`: Add Collection
- `GET /api/collections`: Get Collections
- `POST /api/collections/smart`: Add Smart Collection
- `GET /api/collections/smart`: Get Smart Collections
- `GET /api/collections/identifiers`: Get Collection Identifiers
- `GET /api/collections/virtual`: Get Virtual Collections
- `GET /api/collections/virtual/identifiers`: Get Virtual Collection Identifiers
- `GET /api/collections/smart/identifiers`: Get Smart Collection Identifiers
- `GET /api/collections/{id}`: Get Collection
- `PUT /api/collections/{id}`: Update Collection
- `DELETE /api/collections/{id}`: Delete Collection
- `GET /api/collections/virtual/{id}`: Get Virtual Collection
- `GET /api/collections/smart/{id}`: Get Smart Collection
- `PUT /api/collections/smart/{id}`: Update Smart Collection
- `DELETE /api/collections/smart/{id}`: Delete Smart Collection

### config
- `GET /api/config`: Get Config
- `POST /api/config/system/platforms`: Add Platform Binding
- `DELETE /api/config/system/platforms/{fs_slug}`: Delete Platform Binding
- `POST /api/config/system/versions`: Add Platform Version
- `DELETE /api/config/system/versions/{fs_slug}`: Delete Platform Version
- `POST /api/config/exclude`: Add Exclusion
- `DELETE /api/config/exclude/{exclusion_type}/{exclusion_value}`: Delete Exclusion

### devices
- `GET /api/devices`: Get Devices
- `POST /api/devices`: Register Device
- `GET /api/devices/{device_id}`: Get Device
- `PUT /api/devices/{device_id}`: Update Device
- `DELETE /api/devices/{device_id}`: Delete Device

### feeds
- `GET /api/feeds/webrcade`: Platforms Webrcade Feed
- `GET /api/feeds/tinfoil`: Tinfoil Index Feed
- `GET /api/feeds/pkgi/ps3/{content_type}`: Pkgi Ps3 Feed
- `GET /api/feeds/pkgi/psvita/{content_type}`: Pkgi Psvita Feed
- `GET /api/feeds/pkgi/psp/{content_type}`: Pkgi Psp Feed
- `GET /api/feeds/fpkgi/{platform_slug}`: Fpkgi Feed
- `GET /api/feeds/kekatsu/{platform_slug}`: Kekatsu Ds Feed
- `GET /api/feeds/pkgj/psp/games`: Pkgj Psp Games Feed
- `GET /api/feeds/pkgj/psp/dlc`: Pkgj Psp Dlcs Feed
- `GET /api/feeds/pkgj/psvita/games`: Pkgj Psv Games Feed
- `GET /api/feeds/pkgj/psvita/dlc`: Pkgj Psv Dlcs Feed
- `GET /api/feeds/pkgj/psx/games`: Pkgj Psx Games Feed

### firmware
- `POST /api/firmware`: Add Firmware
- `GET /api/firmware`: Get Platform Firmware
- `GET /api/firmware/identifiers`: Get Firmware Identifiers
- `GET /api/firmware/{id}`: Get Firmware
- `HEAD /api/firmware/{id}/content/{file_name}`: Head Firmware Content
- `GET /api/firmware/{id}/content/{file_name}`: Get Firmware Content
- `POST /api/firmware/delete`: Delete Firmware

### gamelist
- `POST /api/gamelist/export`: Export Gamelist

### netplay
- `GET /api/netplay/list`: Get Rooms

### platforms
- `POST /api/platforms`: Add Platform
- `GET /api/platforms`: Get Platforms
- `GET /api/platforms/identifiers`: Get Platform Identifiers
- `GET /api/platforms/supported`: Get Supported Platforms Endpoint
- `GET /api/platforms/{id}`: Get Platform
- `PUT /api/platforms/{id}`: Update Platform
- `DELETE /api/platforms/{id}`: Delete Platform

### raw
- `HEAD /api/raw/assets/{path}`: Head Raw Asset
- `GET /api/raw/assets/{path}`: Get Raw Asset

### roms
- `POST /api/roms`: Add Rom
- `GET /api/roms`: Get Roms
- `GET /api/roms/identifiers`: Get Rom Identifiers
- `GET /api/roms/download`: Download Roms
- `GET /api/roms/by-metadata-provider`: Get Rom By Metadata Provider
- `GET /api/roms/by-hash`: Get Rom By Hash
- `GET /api/roms/filters`: Get Rom Filters
- `GET /api/roms/{id}`: Get Rom
- `PUT /api/roms/{id}`: Update Rom
- `HEAD /api/roms/{id}/content/{file_name}`: Head Rom Content
- `GET /api/roms/{id}/content/{file_name}`: Get Rom Content
- `POST /api/roms/{id}/manuals`: Add Rom Manuals
- `DELETE /api/roms/{id}/manuals`: Delete Rom Manuals
- `POST /api/roms/delete`: Delete Roms
- `PUT /api/roms/{id}/props`: Update Rom User
- `GET /api/roms/files/{id}`: Get Romfile
- `GET /api/romsfiles/{id}/content/{file_name}`: Get Romfile Content
- `GET /api/roms/{id}/notes`: Get Rom Notes
- `POST /api/roms/{id}/notes`: Create Rom Note
- `GET /api/roms/{id}/notes/identifiers`: Get Rom Note Identifiers
- `PUT /api/roms/{id}/notes/{note_id}`: Update Rom Note
- `DELETE /api/roms/{id}/notes/{note_id}`: Delete Rom Note

### saves
- `POST /api/saves`: Add Save
- `GET /api/saves`: Get Saves
- `GET /api/saves/identifiers`: Get Save Identifiers
- `GET /api/saves/summary`: Get Saves Summary
- `GET /api/saves/{id}`: Get Save
- `PUT /api/saves/{id}`: Update Save
- `GET /api/saves/{id}/content`: Download Save
- `POST /api/saves/{id}/downloaded`: Confirm Download
- `POST /api/saves/delete`: Delete Saves
- `POST /api/saves/{id}/track`: Track Save
- `POST /api/saves/{id}/untrack`: Untrack Save

### screenshots
- `POST /api/screenshots`: Add Screenshot

### search
- `GET /api/search/roms`: Search Rom
- `GET /api/search/cover`: Search Cover

### states
- `POST /api/states`: Add State
- `GET /api/states`: Get States
- `GET /api/states/identifiers`: Get State Identifiers
- `GET /api/states/{id}`: Get State
- `PUT /api/states/{id}`: Update State
- `POST /api/states/delete`: Delete States

### stats
- `GET /api/stats`: Stats

### system
- `GET /api/heartbeat`: Heartbeat
- `GET /api/heartbeat/metadata/{source}`: Metadata Heartbeat
- `GET /api/setup/library`: Get Setup Library Info
- `POST /api/setup/platforms`: Create Setup Platforms

### tasks
- `GET /api/tasks`: List Tasks
- `GET /api/tasks/status`: Get Tasks Status
- `GET /api/tasks/{task_id}`: Get Task By Id
- `POST /api/tasks/run`: Run All Tasks
- `POST /api/tasks/run/{task_name}`: Run Single Task

### users
- `GET /api/users`: Get Users
- `POST /api/users`: Add User
- `POST /api/users/invite-link`: Create Invite Link
- `POST /api/users/register`: Create User From Invite
- `GET /api/users/identifiers`: Get User Identifiers
- `GET /api/users/me`: Get Current User
- `GET /api/users/{id}`: Get User
- `PUT /api/users/{id}`: Update User
- `DELETE /api/users/{id}`: Delete User
- `POST /api/users/{id}/ra/refresh`: Refresh RetroAchievements

## Repo Utility Surface

`ghostship-romm` currently uses:
- heartbeat
- rom inventory and detail lookup
- platforms
- collections
- config
- saves and save summaries
- users and current-user lookup

## Notes

- `ghostship-romm scan` still predates the current `/api/tasks*` task surface and should be treated as a compatibility gap rather than the canonical upstream contract.

## Source Material

- Local mirrored raw spec: [romm-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/romm-openapi.json)
- Upstream repository: <https://github.com/rommapp/romm>
