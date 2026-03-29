# CloakBrowser Manager API Spec Sheet

## Service Identity

- Product: CloakBrowser Manager
- Base UI URL: `http(s)://<host>`
- Base API URL: `http(s)://<host>/api`

## Authentication

- Auth mode: optional static shared secret
- Server configuration: `AUTH_TOKEN=<secret>`
- API client header when auth is enabled:
  - `Authorization: Bearer <same AUTH_TOKEN value>`
- Browser session auth endpoints:
  - `GET /api/auth/status`
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
- Public health endpoint:
  - `GET /api/status`

## Full Endpoint and Use-Case Inventory

### Authentication and health
- `GET /api/auth/status`: report whether auth is enabled and whether the caller is authenticated
- `POST /api/auth/login`: exchange the static token for a browser cookie session
- `POST /api/auth/logout`: clear the browser cookie session
- `GET /api/status`: health, binary version, profile counts

### Profile CRUD
- `GET /api/profiles`: list profiles
- `POST /api/profiles`: create a profile
- `GET /api/profiles/{profile_id}`: fetch profile details
- `PUT /api/profiles/{profile_id}`: update a profile
- `DELETE /api/profiles/{profile_id}`: delete a profile

### Runtime lifecycle
- `POST /api/profiles/{profile_id}/launch`: start a browser profile
- `POST /api/profiles/{profile_id}/stop`: stop a running profile
- `GET /api/profiles/{profile_id}/status`: retrieve running or stopped state and CDP info

### Clipboard
- `POST /api/profiles/{profile_id}/clipboard`: write clipboard text into a running profile
- `GET /api/profiles/{profile_id}/clipboard`: read clipboard text from a running profile

### CDP discovery and transport
- `GET /api/profiles/{profile_id}/cdp`: summarize CDP connection details
- `GET /api/profiles/{profile_id}/cdp/json/version`
- `GET /api/profiles/{profile_id}/cdp/json/version/`
- `GET /api/profiles/{profile_id}/cdp/json/list`
- `GET /api/profiles/{profile_id}/cdp/json/list/`
- `GET /api/profiles/{profile_id}/cdp/json`
- `GET /api/profiles/{profile_id}/cdp/json/`
- `WS /api/profiles/{profile_id}/cdp`: WebSocket CDP bridge
- `WS /api/profiles/{profile_id}/cdp/devtools/{path:path}`: CDP devtools-path bridge

### VNC transport
- `WS /api/profiles/{profile_id}/vnc`: browser display stream

## CLI Env Mapping

- `CLOAKBROWSER_URL`
- Optional `CLOAKBROWSER_TOKEN`
  - Set it only when the manager was started with `AUTH_TOKEN=...`
  - Use the same exact static secret as the server

## Source Material

- Official manager README: <https://github.com/CloakHQ/CloakBrowser-Manager>
- Official backend implementation: <https://raw.githubusercontent.com/CloakHQ/CloakBrowser-Manager/main/backend/main.py>
- Official auth tests: <https://raw.githubusercontent.com/CloakHQ/CloakBrowser-Manager/main/backend/tests/test_auth.py>
- Official API tests: <https://raw.githubusercontent.com/CloakHQ/CloakBrowser-Manager/main/backend/tests/test_api.py>
