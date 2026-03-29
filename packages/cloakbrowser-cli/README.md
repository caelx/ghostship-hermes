# ghostship-cloakbrowser

CLI utility for CloakBrowser Manager API.

## Environment Variables

- `CLOAKBROWSER_URL`: The base URL of your CloakBrowser Manager instance (default: `http://localhost:8080`).
- `CLOAKBROWSER_TOKEN`: Auth token. Optional if authentication is disabled on the server.

## Contract

- executable name: `ghostship-cloakbrowser`
- Python package name: `ghostship-cloakbrowser`
- import package: `ghostship_cloakbrowser`
- output: JSON by default

## Commands

### status
Get system status information (running count, binary version, total profiles).
```bash
ghostship-cloakbrowser status
```

### list
List all profiles with their status and CDP URLs.
```bash
ghostship-cloakbrowser list
```

### get
Get detailed information for a specific profile.
```bash
ghostship-cloakbrowser get <profile-id>
```

### create
Create a new browser profile.
```bash
ghostship-cloakbrowser create <name> [options]
```

Options:
- `--fingerprint-seed`: Fingerprint seed number
- `--proxy`: Proxy URL (e.g., `http://user:pass@host:port`)
- `--timezone`: Timezone (e.g., `America/New_York`)
- `--locale`: Locale (e.g., `en-US`)
- `--platform`: Platform (`windows`, `macos`, `linux`)
- `--user-agent`: Custom user agent string
- `--screen-width`: Screen width (default: 1920)
- `--screen-height`: Screen height (default: 1080)
- `--gpu-vendor`: GPU vendor
- `--gpu-renderer`: GPU renderer
- `--hardware-concurrency`: Hardware concurrency (CPU cores)
- `--humanize`: Enable humanization
- `--human-preset`: Human preset (`default`, `careful`)
- `--headless`: Run in headless mode
- `--geoip`: Use geoip-based settings
- `--clipboard-sync/--no-clipboard-sync`: Enable clipboard sync
- `--color-scheme`: Color scheme (`light`, `dark`, `no-preference`)
- `--notes`: Profile notes

### update
Update an existing browser profile.
```bash
ghostship-cloakbrowser update <profile-id> [options]
```

### delete
Delete a browser profile.
```bash
ghostship-cloakbrowser delete <profile-id>
```

### launch
Launch a browser profile.
```bash
ghostship-cloakbrowser launch <profile-id>
```

Returns CDP URL for Playwright/Puppeteer connection:
```json
{
  "profile_id": "abc123",
  "status": "running",
  "vnc_ws_port": 6080,
  "display": ":1",
  "cdp_url": "/api/profiles/abc123/cdp"
}
```

### stop
Stop a running browser profile.
```bash
ghostship-cloakbrowser stop <profile-id>
```

### profile-status
Get status of a specific profile.
```bash
ghostship-cloakbrowser profile-status <profile-id>
```

### clipboard-get
Get clipboard text from a running profile.
```bash
ghostship-cloakbrowser clipboard-get <profile-id>
```

### clipboard-set
Set clipboard text in a running profile.
```bash
ghostship-cloakbrowser clipboard-set <profile-id> --text <text>
```

### cdp-info
Get CDP connection info for a profile.
```bash
ghostship-cloakbrowser cdp-info <profile-id>
```

Returns:
```json
{
  "cdp_url": "/api/profiles/abc123/cdp",
  "usage": "playwright.chromium.connect_over_cdp('http://<host>/api/profiles/abc123/cdp')"
}
```

## Development

Lock dependencies:
```fish
python3 ../../scripts/python_utility.py lock .
```

Run tests:
```fish
python3 ../../scripts/python_utility.py test .
```

Build wheel and sdist:
```fish
python3 ../../scripts/python_utility.py build .
```
