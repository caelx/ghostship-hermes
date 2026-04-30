# API Catalog

Restored API reference files are copied into:

`/home/hermes/ghostship-wiki/api/reference`

The source files come from repo `docs/api`. Use those Markdown sheets and raw
OpenAPI/Swagger mirrors when writing direct API clients.

## Restored Coverage

- Bazarr: `bazarr.md`, `bazarr-swagger.json`
- BookStack: `bookstack.md`, `bookstack-docs.json`
- changedetection.io: `changedetection.md`, `changedetection-openapi.json`
- Chaptarr: `chaptarr.md`, `chaptarr-openapi.json`
- FlareSolverr: `flaresolverr.md`
- Grimmory: `grimmory.md`
- n8n: `n8n.md`, `n8n-openapi.json`
- NZBGet: `nzbget.md`
- Plex: `plex.md`
- PriceBuddy: `pricebuddy.md`
- Prowlarr: `prowlarr.md`, `prowlarr-openapi.json`
- pyLoad-ng: `pyload-ng.md`, `pyload-openapi.json`
- qBittorrent: `qbittorrent.md`
- Radarr: `radarr.md`, `radarr-openapi.json`
- RomM: `romm.md`, `romm-openapi.json`
- RSS Bridge: `rss-bridge.md`
- SearXNG: `searxng.md`
- Sonarr: `sonarr.md`, `sonarr-openapi.json`
- Synology: `synology.md`
- Tautulli: `tautulli.md`

## Agent-Relevant Generated Skill Feedback

Generated skills currently rely most on:

- Prowlarr, NZBGet, qBittorrent, and pyLoad for media acquisition flows.
- `gws`, `gcloud`, and Bitwarden for Google Workspace/Cloud auth workflows.
- Firecrawl as Hermes' managed web backend.

Other deployed utility services exist on `chill-penguin`, but they are not
first-class wiki targets unless a generated skill or task starts using them.
