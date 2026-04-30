# API Specifications

This directory is the canonical API reference area for every `ghostship-*` utility in this repository.

The repo uses a hybrid model:

- Official raw OpenAPI or Swagger mirrors are stored here when upstream publishes them.
- Repo-owned Markdown spec sheets are stored here for every utility.
- When no machine-readable upstream spec exists, the Markdown sheet becomes the canonical reference and records the source quality explicitly.

## Coverage Matrix

| Utility | Canonical docs | Raw spec mirror | Source quality |
| --- | --- | --- | --- |
| `ghostship-bazarr` | `docs/api/bazarr.md` | `docs/api/bazarr-swagger.json` | Official Swagger + repo summary |
| `ghostship-bookstack` | `docs/api/bookstack.md` | `docs/api/bookstack-docs.json` | Official docs plus repo-owned normalized snapshot |
| `ghostship-changedetection` | `docs/api/changedetection.md` | `docs/api/changedetection-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-flaresolverr` | `docs/api/flaresolverr.md` | None | Official README |
| `ghostship-grimmory` | `docs/api/grimmory.md` | None | Official Grimmory repository source code |
| `ghostship-n8n` | `docs/api/n8n.md` | `docs/api/n8n-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-nzbget` | `docs/api/nzbget.md` | None | Official RPC reference |
| `ghostship-plex` | `docs/api/plex.md` | None | Official URL command docs plus repo summary |
| `ghostship-pricebuddy` | `docs/api/pricebuddy.md` | None | Official docs plus upstream tests/source code |
| `ghostship-prowlarr` | `docs/api/prowlarr.md` | `docs/api/prowlarr-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-pyload-ng` | `docs/api/pyload-ng.md` | `docs/api/pyload-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-chaptarr` | `docs/api/chaptarr.md` | `docs/api/chaptarr-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-rss-bridge` | `docs/api/rss-bridge.md` | None | Official docs and source code |
| `ghostship-qbittorrent` | `docs/api/qbittorrent.md` | None | Official WebUI wiki |
| `ghostship-radarr` | `docs/api/radarr.md` | `docs/api/radarr-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-romm` | `docs/api/romm.md` | `docs/api/romm-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-searxng` | `docs/api/searxng.md` | None | Official docs |
| `ghostship-sonarr` | `docs/api/sonarr.md` | `docs/api/sonarr-openapi.json` | Official OpenAPI + repo summary |
| `ghostship-synology` | `docs/api/synology.md` | None | Official Synology PDF guides + repo summary |
| `ghostship-tautulli` | `docs/api/tautulli.md` | None | Official API docs |

## Naming Rules

- Raw upstream mirrors use:
  - `*-openapi.json`
  - `*-swagger.json`
- Repo-owned summary or full reference sheets use:
  - `*.md`

## Source Quality Labels

- `Official OpenAPI + repo summary`: upstream publishes a machine-readable spec and the repo adds a companion sheet for auth and endpoint-group context.
- `Official Swagger + repo summary`: same pattern, but from Swagger.
- `Official docs`: upstream publishes narrative documentation but not a machine-readable schema.
- `Official API docs`: upstream publishes a stable API reference, but not a repo-consumed OpenAPI or Swagger artifact.
- `Official README`: upstream README is the practical API contract.
- `Official README and source code`: README plus upstream implementation or tests were needed to clarify behavior.
- `Official RPC reference`: upstream publishes an RPC method reference rather than a REST-style schema.
- `Official URL command docs plus repo summary`: upstream publishes a limited stable command set, and the repo sheet documents the broader practical surface separately.
- `Official WebUI wiki`: upstream publishes the API contract in a maintained wiki rather than a machine-readable spec.
- `Official Synology PDF guides + repo summary`: upstream publishes PDF developer guides, and the repo sheet organizes them into a current endpoint and namespace reference.
- `Official Grimmory repository source code`: the canonical contract was derived directly from the official upstream backend controllers because no repo-published machine-readable schema was available.
- `Official docs and source code`: upstream publishes narrative documentation, and the repo confirmed the callable surface directly from the implementation.
- `Official docs plus upstream tests/source code`: upstream publishes narrative docs, but the practical endpoint contract and field shapes had to be confirmed from upstream tests and implementation.
- `Official docs plus upstream/community verification`: no raw spec exists and the repo had to confirm the live auth or response shape from additional material.
- `Official docs plus repo-owned normalized snapshot`: upstream publishes an official docs surface, but the repo commits a normalized machine-readable snapshot derived from that docs output when a directly consumable raw schema is not available for capture.
