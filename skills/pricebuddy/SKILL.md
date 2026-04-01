---
name: pricebuddy
description: Manage PriceBuddy products, product sources, stores, and tags with the typed ghostship-pricebuddy CLI. Output is native JSON.
---

# PriceBuddy Skill

Use `ghostship-pricebuddy` when you need to inspect or change PriceBuddy state.

## Prerequisites

- `PRICEBUDDY_URL`
- `PRICEBUDDY_TOKEN`

## Commands

- `ghostship-pricebuddy whoami`
- `ghostship-pricebuddy products list|get|create|update|delete`
- `ghostship-pricebuddy product-sources list|get|create|update|delete|search|search-all`
- `ghostship-pricebuddy stores list|get|create|update|delete`
- `ghostship-pricebuddy tags list|get|create|update|delete`

## Guidance

- Prefer `tags` for disposable write-path tests because they are small and easy to create, update, and delete safely.
- Use `product-sources search-all` when you want to see how saved source definitions search the web without creating a product.
- Store and product-source creation require nested scraping strategy data. Read `ghostship-pricebuddy <resource> create --help` carefully; the CLI exposes those nested fields as explicit flags instead of opaque untyped blobs.
- All commands emit JSON. Use `--pretty` only for inspection.
