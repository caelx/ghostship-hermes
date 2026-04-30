# Service Environment Variables

Load `/home/hermes/.hermes/.env` in process memory. Do not echo secret values.

## URL And Auth Mapping

| Service | URL variable | Auth variables | Typical auth shape |
| --- | --- | --- | --- |
| Bazarr | `BAZARR_URL` | `BAZARR_API_KEY` | `X-API-Key: $BAZARR_API_KEY` |
| BookStack | `BOOKSTACK_URL` | `BOOKSTACK_TOKEN_ID`, `BOOKSTACK_TOKEN_SECRET` | `Authorization: Token <id>:<secret>` |
| changedetection.io | `CHANGEDETECTION_URL` | `CHANGEDETECTION_API_KEY` | API key header/query; see `api/reference/changedetection.md` |
| Chaptarr | `CHAPTARR_URL` | `CHAPTARR_API_KEY` | `X-Api-Key: $CHAPTARR_API_KEY` |
| Firecrawl | `FIRECRAWL_API_URL` | `FIRECRAWL_API_KEY` | `Authorization: Bearer $FIRECRAWL_API_KEY` |
| FlareSolverr | `FLARESOLVERR_URL` | none | JSON commands to `/v1` |
| Grimmory | `GRIMMORY_URL` | `GRIMMORY_USERNAME`, `GRIMMORY_PASSWORD` | login/session auth |
| n8n | `N8N_URL` | `N8N_API_KEY` | `X-N8N-API-KEY: $N8N_API_KEY` |
| NZBGet | `NZBGET_URL` | none in Hermes env | JSON-RPC endpoints under `/jsonrpc` |
| Plex | `PLEX_URL` | `PLEX_TOKEN` | `X-Plex-Token` query/header |
| PriceBuddy | `PRICEBUDDY_URL` | `PRICEBUDDY_TOKEN` | bearer/token auth; see `api/reference/pricebuddy.md` |
| Prowlarr | `PROWLARR_URL` | `PROWLARR_API_KEY` | `X-Api-Key: $PROWLARR_API_KEY` |
| pyLoad-ng | `PYLOAD_URL` | `PYLOAD_API_KEY` | `X-API-Key: $PYLOAD_API_KEY` for `/api/*` |
| qBittorrent | `QBITTORRENT_URL` | none in Hermes env | Web API; internal deployment may allow unauthenticated access |
| Radarr | `RADARR_URL` | `RADARR_API_KEY` | `X-Api-Key: $RADARR_API_KEY` |
| RomM | `ROMM_URL` | `ROMM_USERNAME`, `ROMM_PASSWORD` | login/token flow; see `api/reference/romm.md` |
| RSS Bridge | `RSS_BRIDGE_URL` | none | public feed/API routes |
| SearXNG | `SEARXNG_URL` | none | search endpoint parameters |
| Sonarr | `SONARR_URL` | `SONARR_API_KEY` | `X-Api-Key: $SONARR_API_KEY` |
| Synology | `SYNOLOGY_URL` | `SYNOLOGY_USER`, `SYNOLOGY_PASS`, `SYNOLOGY_VERIFY_SSL` | Synology auth/session APIs |
| Tautulli | `TAUTULLI_URL` | `TAUTULLI_API_KEY` | `apikey` parameter |

## Media Flow Notes

Generated media skills use:

- `PROWLARR_URL` + `PROWLARR_API_KEY` for search and download-client APIs.
- `NZBGET_URL` for JSON-RPC status and append calls.
- `QBITTORRENT_URL` for Web API torrent control.
- `PYLOAD_URL` + `PYLOAD_API_KEY` for pyLoad REST calls.

Prowlarr/Radarr/Sonarr/Chaptarr share the common `X-Api-Key` style. pyLoad uses
`X-API-Key` capitalization in its OpenAPI spec.
