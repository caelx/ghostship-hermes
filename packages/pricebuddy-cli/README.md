# ghostship-pricebuddy

Typed CLI utility for the PriceBuddy REST API.

## Environment Variables

- `PRICEBUDDY_URL`: Base URL of the PriceBuddy instance.
- `PRICEBUDDY_TOKEN`: API token created from the PriceBuddy UI.

## Commands

- `ghostship-pricebuddy whoami`
- `ghostship-pricebuddy products list|get|create|update|delete`
- `ghostship-pricebuddy product-sources list|get|create|update|delete|search|search-all`
- `ghostship-pricebuddy stores list|get|create|update|delete`
- `ghostship-pricebuddy tags list|get|create|update|delete`

All commands emit JSON by default. Use `--pretty` for formatted JSON.

## Examples

```bash
ghostship-pricebuddy whoami --pretty
ghostship-pricebuddy products list --status p --include tags --pretty
ghostship-pricebuddy product-sources search-all "steam deck"
ghostship-pricebuddy tags create --name handhelds --pretty
```
