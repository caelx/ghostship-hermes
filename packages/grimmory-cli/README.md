# ghostship-grimmory

CLI utility for Grimmory API.

## Environment Variables

- `GRIMMORY_URL`: The base URL of your Grimmory or BookLore instance (e.g., `http://localhost:6060`).
- Preferred: `GRIMMORY_USERNAME` and `GRIMMORY_PASSWORD`. The CLI exchanges these at `POST /api/v1/auth/login` and uses the returned bearer token.
- Optional override: `GRIMMORY_TOKEN` if you already have a valid bearer token.

## Authentication Notes

- Grimmory/BookLore does not appear to use a repo-managed static API token as its primary auth mechanism.
- The CLI is stateless: it authenticates at startup, uses the returned bearer token for the requested call, and exits.
- `GRIMMORY_TOKEN` is treated as an override for automation flows that already manage bearer tokens.
