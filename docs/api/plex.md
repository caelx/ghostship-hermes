# Plex Media Server API Spec Sheet

## Service Identity

- Product: Plex Media Server
- Base server URL: `http(s)://<host>:32400`
- Primary auth used by this repo: `X-Plex-Token`
- Response formats in official docs: XML is the canonical documented format, though some endpoints can negotiate JSON

## Canonical Source Quality

- Official URL command documentation plus repo summary
- Plex does not currently publish a repo-consumed OpenAPI artifact in this repository

## Full Endpoint and Use-Case Inventory

### Officially documented stable URL commands
- `GET /`: root discovery
- `GET /library/sections`: list library sections
- `GET /library/sections/{id}/all`: list items in a section
- `GET /library/metadata/{ratingKey}`: fetch metadata for an item
- `GET /library/sections/{id}/refresh`: refresh or rescan a section

### Broader practical Plex surface used by this repo
- `GET /identity`: server identity
- `GET /status/sessions`: active playback sessions
- `GET /activities`: current background activities
- `GET /library/sections/{id}/filters`: section filter options
- `GET /library/sections/{id}/sorts`: section sort options
- `GET /library/sections/all/refresh`: global refresh trigger
- `GET /library/metadata/{ratingKey}/children`: child metadata
- `GET /playlists`: playlists inventory
- `GET /playlists/{id}/items`: playlist items
- `GET /library/sections/{id}/collections`: collections in a section
- `GET /:/prefs`: effective server preferences
- `GET /butler`: maintenance and scheduled-task surface
- `GET /statistics/resources`: system resource statistics
- `GET /library/terminate/{sessionId}`: terminate playback session
- `GET /sessions/{sessionId}`: session detail

## Notes

- Plex’s officially published support article is narrower than the practical server surface the CLI uses.
- This sheet therefore separates the stable documented commands from the broader practical endpoints already exercised by `ghostship-plex`.
- If a future official machine-readable Plex spec becomes available, it should replace this repo-owned reference.

## Source Material

- Official support article: <https://support.plex.tv/articles/201638786-plex-media-server-url-commands/>
