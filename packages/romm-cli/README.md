# ghostship-romm

CLI utility for Romm API.

## Environment Variables

- `ROMM_URL`: The base URL of your RomM instance (e.g., `http://localhost:8080`).
- Preferred: `ROMM_USERNAME` and `ROMM_PASSWORD`. The CLI exchanges these at `POST /api/token` and uses the returned bearer token.
- Optional override: `ROMM_TOKEN` if you already have a valid RomM bearer token.

## Authentication Notes

- RomM v4.7.0 uses an OAuth password-grant style token endpoint at `/api/token`.
- The CLI is stateless: it authenticates at startup, uses the bearer token for the requested call, and exits.
- `ROMM_TOKEN` is treated as an override for automation flows that already manage bearer tokens themselves.
