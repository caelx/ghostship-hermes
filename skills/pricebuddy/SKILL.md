---
name: pricebuddy
description: Manage PriceBuddy products, product sources, stores, and tags with the typed ghostship-pricebuddy CLI. Output is native JSON.
---

# PriceBuddy Skill

Use `ghostship-pricebuddy` when you need to inspect or change PriceBuddy state.

## Prerequisites

- `PRICEBUDDY_URL`
- `PRICEBUDDY_TOKEN`

## Contract

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Every invocation accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete commands support `--dry-run` and print the exact request object without calling the API.
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Commands

- `ghostship-pricebuddy request`
- `ghostship-pricebuddy get_current_user`
- `ghostship-pricebuddy list_products`
- `ghostship-pricebuddy get_product`
- `ghostship-pricebuddy create_product`
- `ghostship-pricebuddy update_product`
- `ghostship-pricebuddy delete_product`
- `ghostship-pricebuddy list_product_sources`
- `ghostship-pricebuddy get_product_source`
- `ghostship-pricebuddy create_product_source`
- `ghostship-pricebuddy update_product_source`
- `ghostship-pricebuddy delete_product_source`
- `ghostship-pricebuddy search_product_source`
- `ghostship-pricebuddy search_all_product_sources`
- `ghostship-pricebuddy list_stores`
- `ghostship-pricebuddy get_store`
- `ghostship-pricebuddy create_store`
- `ghostship-pricebuddy update_store`
- `ghostship-pricebuddy delete_store`
- `ghostship-pricebuddy list_tags`
- `ghostship-pricebuddy get_tag`
- `ghostship-pricebuddy create_tag`
- `ghostship-pricebuddy update_tag`
- `ghostship-pricebuddy delete_tag`

## Guidance

- Prefer `create_tag`, `update_tag`, and `delete_tag` for disposable write-path tests because tags are small and easy to create, update, and delete safely.
- Use `search_all_product_sources` when you want to see how saved source definitions search the web without creating a product.
- Store and product-source creation require nested scraping strategy data. Read `ghostship-pricebuddy <command> --help` carefully; the CLI exposes those nested fields as explicit flags instead of opaque untyped blobs.
- All commands emit JSON. Use `--pretty` only for inspection.
