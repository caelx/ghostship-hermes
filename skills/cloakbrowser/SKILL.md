---
name: cloakbrowser
description: Manage CloakBrowser profiles, launch browsers, and get CDP URLs for automation.
---

# CloakBrowser Skill

The `ghostship-cloakbrowser` utility allows agents to create, manage, and launch browser profiles with unique fingerprints for automation tasks.

## Structure

- **Skill Document:** `skills/cloakbrowser/SKILL.md` (this file)
- **Package Directory:** `packages/cloakbrowser-cli/`
- **README:** `packages/cloakbrowser-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `CLOAKBROWSER_URL`: The base URL of the CloakBrowser Manager (default: `http://localhost:8080`).
- `CLOAKBROWSER_TOKEN`: Optional static auth token. If the manager was started with `AUTH_TOKEN=...`, set this to that same exact value. Omit it when manager auth is disabled.

## Usage

All commands output native JSON. Use `--pretty` for human-readable output.

### Commands

#### `ghostship-cloakbrowser status`
Get system status (running count, binary version, total profiles).

#### `ghostship-cloakbrowser auth-status`
Report whether manager auth is enabled and whether the current client is authenticated.

#### `ghostship-cloakbrowser list`
List all profiles with their status and CDP URLs. Running profiles show `cdp_url` for Playwright/Puppeteer connection.

#### `ghostship-cloakbrowser get <profile-id>`
Get detailed information for a specific profile.

#### `ghostship-cloakbrowser create <name>`
Create a new browser profile with fingerprint settings.

Options:
- `--fingerprint-seed`: Fingerprint seed number (random if not set)
- `--proxy`: Proxy URL (e.g., `http://user:pass@host:port`)
- `--timezone`: Timezone (e.g., `America/New_York`)
- `--locale`: Locale (e.g., `en-US`)
- `--platform`: Platform (`windows`, `macos`, `linux`)
- `--user-agent`: Custom user agent string
- `--screen-width`: Screen width (default: 1920)
- `--screen-height`: Screen height (default: 1080)
- `--humanize`: Enable humanization
- `--human-preset`: Human preset (`default`, `careful`)
- `--headless`: Run in headless mode
- `--geoip`: Use geoip-based settings

#### `ghostship-cloakbrowser update <profile-id>`
Update an existing profile. Same options as `create`.

#### `ghostship-cloakbrowser delete <profile-id>`
Delete a browser profile.

#### `ghostship-cloakbrowser launch <profile-id>`
Launch a browser profile. Returns `cdp_url` for Playwright/Puppeteer automation.

#### `ghostship-cloakbrowser stop <profile-id>`
Stop a running browser profile.

#### `ghostship-cloakbrowser profile-status <profile-id>`
Get status of a specific profile.

#### `ghostship-cloakbrowser clipboard-get <profile-id>`
Get clipboard text from a running profile.

#### `ghostship-cloakbrowser clipboard-set <profile-id> <text>`
Set clipboard text in a running profile.

#### `ghostship-cloakbrowser cdp-info <profile-id>`
Get CDP connection info for Playwright/Puppeteer automation.

## CDP Automation

To connect with Playwright:
```python
from playwright.async_api import async_playwright

async with async_playwright() as pw:
    browser = await pw.chromium.connect_over_cdp(
        "http://localhost:8080/api/profiles/<profile-id>/cdp"
    )
    page = browser.contexts[0].pages[0]
    await page.goto("https://example.com")
```

The `cdp_url` from `launch` or `list` commands can be prefixed with the host to create the full WebSocket URL.

## Examples

```bash
# List all profiles
ghostship-cloakbrowser list --pretty

# Create a profile with custom settings
ghostship-cloakbrowser create "automation-profile" --platform windows --humanize

# Launch a profile and get CDP URL
ghostship-cloakbrowser launch profile-123 --pretty

# Stop a profile
ghostship-cloakbrowser stop profile-123
```

## Agent Guidance

- CloakBrowser Manager auth is a static shared secret, not a username/password login flow. Use `CLOAKBROWSER_TOKEN` only when the server was started with `AUTH_TOKEN=...`.
- Use `list` to find running profiles and their CDP URLs for automation.
- The `cdp_url` returned is relative; prefix with your `CLOAKBROWSER_URL` host for full WebSocket URL.
- Profile fingerprints are persistent - created profiles maintain their identity across launches.
- Use `status` to monitor how many profiles are running (resource management).
- For browser automation, always launch the profile first, then connect via CDP.
