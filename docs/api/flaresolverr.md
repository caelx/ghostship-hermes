# FlareSolverr API Spec Sheet

## Service Identity

- Product: FlareSolverr
- Base API URL: `http(s)://<host>/v1`
- Primary auth: none by default
- Protocol style: JSON over a single `POST /v1` endpoint with a `cmd` field

## Canonical Source Quality

- Official README
- No mirrored OpenAPI artifact is currently stored in this repo

## Full Endpoint and Use-Case Inventory

FlareSolverr exposes a single HTTP endpoint and selects behavior through the `cmd` field in the JSON body.

### Transport
- `POST /v1`: command execution endpoint for all documented operations

### Session management commands
- `sessions.create`: create a browser session for reuse across requests
- `sessions.list`: list active sessions
- `sessions.destroy`: destroy a named session

### Request commands
- `request.get`: solve a page and issue a GET-like navigation
- `request.post`: solve a page and issue a POST-like navigation

### Common request fields
- `cmd`
- `url`
- `session`
- `session_ttl_minutes`
- `maxTimeout`
- `cookies`
- `proxy`
- `waitInSeconds`
- `disableMedia`
- `returnOnlyCookies`
- `returnScreenshot`
- `tabs_till_verify`

### Common response fields
- `status`
- `message`
- `startTimestamp`
- `endTimestamp`
- `solution.url`
- `solution.status`
- `solution.headers`
- `solution.response`
- `solution.cookies`
- `solution.userAgent`
- `solution.screenshot`
- `solution.turnstile_value`

## Repo Utility Surface

`ghostship-flaresolverr` currently uses the documented session and request command surface above.

## Source Material

- Official README: <https://github.com/FlareSolverr/FlareSolverr>
- Official raw README: <https://raw.githubusercontent.com/FlareSolverr/FlareSolverr/master/README.md>
