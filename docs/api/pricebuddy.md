# PriceBuddy API

- Canonical utility: `ghostship-pricebuddy`
- Raw spec mirror: None currently checked in
- Source quality: Official docs plus upstream tests/source code

## Auth

PriceBuddy uses bearer-token auth.

- Header: `Authorization: Bearer <token>`
- Config source for this repo: `PRICEBUDDY_TOKEN`
- Base URL env: `PRICEBUDDY_URL`

The upstream docs state that `/docs/api` can export an OpenAPI spec, but the live export is token-gated and is not mirrored in this repo yet.

## Confirmed Endpoints

### User

- `GET /api/user`

Returns the authenticated user summary with `id`, `name`, and `email`.

### Products

- `GET /api/products`
- `GET /api/products/{id}`
- `POST /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`

Supported list parameters confirmed from upstream tests/handlers:
- `include=tags,user,urls`
- `sort=id,title,status,notify_price,favourite,created_at,updated_at`
- `filter[status]`
- `filter[favourite]`
- `filter[only_official]`
- `per_page`
- `page`

Create payload fields:
- `title` required
- `url` required
- `product_id` optional
- `image` optional
- `status` optional (`p`, `a`)
- `weight` optional
- `notify_price` optional
- `notify_percent` optional
- `favourite` optional
- `only_official` optional
- `create_store` optional

Update payload fields:
- `title` required
- `image` required
- `status`, `weight`, `notify_price`, `notify_percent`, `favourite`, `only_official` optional
- the upstream tests also exercise `current_price`, `price_cache`, `ignored_urls`, and `user_id`

### Product Sources

- `GET /api/product-sources`
- `GET /api/product-sources/{id}`
- `POST /api/product-sources`
- `PUT /api/product-sources/{id}`
- `DELETE /api/product-sources/{id}`
- `GET /api/product-sources/search/{query}`
- `GET /api/product-sources/{id}/search/{query}`

Supported list parameters:
- `include=store,user`
- `sort=id,name,slug,type,status,created_at,updated_at`
- `filter[type]`
- `filter[status]`
- `filter[store_id]`
- `search`
- `per_page`
- `page`

Create/update fields:
- `name`
- `search_url` containing `:search_term`
- `type` (`deals_site`, `online_store`)
- `store_id` optional
- `extraction_strategy.list_container.{type,value}`
- `extraction_strategy.product_title.{type,value}`
- `extraction_strategy.product_url.{type,value}`
- `settings` optional object
- `status` (`active`, `inactive`, `draft`)
- `notes`

Search result shape:
- `title`
- `url`
- optional `source`
- optional `source_id`

### Stores

- `GET /api/stores`
- `GET /api/stores/{id}`
- `POST /api/stores`
- `PUT /api/stores/{id}`
- `DELETE /api/stores/{id}`

Supported list parameters:
- `include=user,urls,products`
- `sort=id,name,created_at,updated_at`
- `filter[domains]`
- `filter[scraper_service]`
- `search`
- `per_page`
- `page`

Create/update fields:
- `name`
- `slug` optional
- `initials` optional
- `domains` array of `{domain}`
- `scrape_strategy.title.{type,value,prepend,append}`
- `scrape_strategy.price.{type,value,prepend,append}`
- `scrape_strategy.image.{type,value,prepend,append}`
- `settings.scraper_service` (`http`, `api`)
- `settings.scraper_service_settings`
- `settings.locale_settings.locale`
- `settings.locale_settings.currency`
- `notes`
- `user_id` constrained to the authenticated user

### Tags

- `GET /api/tags`
- `GET /api/tags/{id}`
- `POST /api/tags`
- `PUT /api/tags/{id}`
- `DELETE /api/tags/{id}`

Supported list parameters:
- `include=products`
- `sort=id,name,created_at,updated_at`
- `filter[name]`
- `search`
- `per_page`
- `page`

Create/update fields:
- `name`
- optional `user_id` constrained to the authenticated user

## Utility Coverage

`ghostship-pricebuddy` exposes:
- `whoami`
- full CRUD for `products`, `product-sources`, `stores`, and `tags`
- product-source search across one source or all sources
- typed request models for nested store and extraction-strategy payloads

## Sources

- Upstream docs: <https://pricebuddy.jez.me/api.html>
- Upstream repo: <https://github.com/jez500/pricebuddy>
