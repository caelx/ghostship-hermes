# Synology File Station API Spec Sheet

## Service Identity

- Product area: Synology DSM WebAPI, primarily File Station
- Base API URL: `http(s)://<host>/webapi`
- Discovery endpoint: `SYNO.API.Info`
- Auth endpoint: `SYNO.API.Auth`

## Canonical Source Quality

- Official Synology PDF guides plus official-repo-adjacent controller and wrapper verification
- No mirrored OpenAPI artifact is currently stored in this repo

## API Discovery and Auth Flow

The official DSM login guide documents this sequence:

1. Query `SYNO.API.Info` with `method=query`
2. Read `path`, `minVersion`, and `maxVersion` for the named APIs
3. Authenticate against `SYNO.API.Auth`
4. Reuse the returned session cookie or `_sid`
5. When supported, also send `SynoToken`

Documented auth details:
- `api=SYNO.API.Auth`
- `method=login`
- `account=<username>`
- `passwd=<password>`
- `session=FileStation`
- `format=sid`
- optional `enable_syno_token=yes`
- response fields can include `sid` and `synotoken`
- logout uses `method=logout` and may also accept `_sid`

Common documented errors include `105`, `106`, `119`, and `150`.

## Full Namespace and Method Inventory

The official File Station guide documents these namespaces. The concrete method and use-case list below combines the official guide with the maintained Synology File Station wrapper you provided.

### Core discovery and auth
- `SYNO.API.Info`: query available API namespaces and version ranges
- `SYNO.API.Auth`: login and logout for File Station sessions

### Information and listing
- `SYNO.FileStation.Info`: `get`
- `SYNO.FileStation.List`: `list_share`, `list`, `getinfo`
- `SYNO.FileStation.VirtualFolder`: mount-point and virtual-folder listing
- `SYNO.FileStation.Thumb`: thumbnail retrieval
- `SYNO.FileStation.BackgroundTask`: background-task listing

### Search and favorites
- `SYNO.FileStation.Search`: `start`, `list`, `stop`, `stop_all`
- `SYNO.FileStation.Favorite`: `list`, `add`, `delete`, `clear_broken`, `edit`, `replace_all`

### Space, hashing, and permissions
- `SYNO.FileStation.DirSize`: `start`, `status`, `stop`
- `SYNO.FileStation.MD5`: `start`, `status`, `stop`
- `SYNO.FileStation.CheckPermission`: permission checks against paths

### Transfer and sharing
- `SYNO.FileStation.Upload`: `upload`
- `SYNO.FileStation.Download`: `download`
- `SYNO.FileStation.Sharing`: `getinfo`, `list`, `create`, `delete`, `clear_invalid`, `edit`

### File and folder mutation
- `SYNO.FileStation.CreateFolder`: `create`
- `SYNO.FileStation.Rename`: `rename`
- `SYNO.FileStation.CopyMove`: `start`, `status`, `stop`
- `SYNO.FileStation.Delete`: `start`, `status`, `stop`
- blocking delete is commonly wrapped client-side on top of the task API

### Archive and compression workflows
- `SYNO.FileStation.Extract`: `start`, `status`, `stop`, archive-file listing
- `SYNO.FileStation.Compress`: `start`, `status`, `stop`

## Repo Utility Surface

`ghostship-synology` currently works against a subset of the broader File Station contract:

- `SYNO.API.Info`
- `SYNO.API.Auth`
- `SYNO.FileStation.List`
- `SYNO.FileStation.Search`
- `SYNO.FileStation.CreateFolder`
- `SYNO.FileStation.Rename`
- `SYNO.FileStation.Delete`
- `SYNO.FileStation.Download`
- `SYNO.FileStation.Upload`
- `SYNO.FileStation.CopyMove`

## Notes

- Synology DSM exposes many more WebAPI namespaces than this repo currently targets.
- The authoritative contract here is the discovery flow plus the File Station namespace and method inventory above.
- The repo client currently uses `_sid`; the official DSM login guide shows that newer flows may also require or benefit from `SynoToken`.

## Source Material

- Official Synology File Station API Guide PDF: <https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf>
- Official Synology DSM Login Web API Guide PDF: <https://global.download.synology.com/download/Document/Software/DeveloperGuide/Os/DSM/All/enu/DSM_Login_Web_API_Guide_enu.pdf>
- Official Synology DSM Login guide landing page: <https://kb.synology.com/en-us/DG/DSM_Login_Web_API_Guide/2>
- Supplemental File Station endpoint wrapper: <https://github.com/N4S4/synology-api/blob/master/synology_api/filestation.py>
