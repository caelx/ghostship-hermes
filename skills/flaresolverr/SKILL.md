---
name: flaresolverr
description: Bypass Cloudflare protection via FlareSolverr. Output is native JSON.
---

# FlareSolverr Skill

The `ghostship-flaresolverr` utility allows agents to perform HTTP requests through a FlareSolverr instance to bypass Cloudflare and other bot protection services.

## Prerequisites

The following environment variables must be configured:
- `FLARESOLVERR_URL`: The base URL of the FlareSolverr instance (default: `http://localhost:8191`).

## Usage

All commands output native JSON.

### Commands

#### `ghostship-flaresolverr get <url>`
Perform a GET request.
- `url`: The target URL.
- `--session`: Optional session ID to use.

#### `ghostship-flaresolverr post <url> <data>`
Perform a POST request.
- `url`: The target URL.
- `data`: POST data string.
- `--session`: Optional session ID to use.

#### `ghostship-flaresolverr create-session`
Create a new browser session.

#### `ghostship-flaresolverr list-sessions`
List all active browser sessions.

#### `ghostship-flaresolverr destroy-session <id>`
Destroy a specific browser session.
- `id`: The session ID to destroy.

## Examples

```bash
# Perform a protected GET request
ghostship-flaresolverr get "https://example.com" --pretty

# Create a session for multiple requests
ghostship-flaresolverr create-session
```

## Agent Guidance

- Use FlareSolverr when direct HTTP requests return Cloudflare challenge pages (403 or 503 errors).
- Using sessions can improve performance for multiple requests to the same site.
- The output includes the `solution` which contains `cookies`, `userAgent`, and `response` HTML.
