from __future__ import annotations

from decimal import Decimal
import json
import os
from typing import Any, Optional

import typer

from .client import (
    DomainEntry,
    PriceBuddyClient,
    ProductCreateRequest,
    ProductSourceCreateRequest,
    ProductSourceExtractionStrategy,
    ProductSourceStatus,
    ProductSourceType,
    ProductSourceUpdateRequest,
    ProductStatus,
    ScrapeStrategyRule,
    ScraperService,
    StoreCreateRequest,
    StoreLocaleSettings,
    StoreScrapeStrategy,
    StoreSettings,
    StoreUpdateRequest,
    TagCreateRequest,
    TagUpdateRequest,
    to_jsonable,
    ProductUpdateRequest,
)

app = typer.Typer(help="Typed PriceBuddy API CLI.", no_args_is_help=True)
products_app = typer.Typer(help="Manage PriceBuddy products.", no_args_is_help=True)
product_sources_app = typer.Typer(help="Manage PriceBuddy product sources.", no_args_is_help=True)
stores_app = typer.Typer(help="Manage PriceBuddy stores.", no_args_is_help=True)
tags_app = typer.Typer(help="Manage PriceBuddy tags.", no_args_is_help=True)
app.add_typer(products_app, name="products")
app.add_typer(product_sources_app, name="product-sources")
app.add_typer(stores_app, name="stores")
app.add_typer(tags_app, name="tags")


def echo_json(data: Any, pretty: bool = False) -> None:
    typer.echo(json.dumps(to_jsonable(data), indent=2 if pretty else None))


def _parse_json_option(value: Optional[str], option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def _parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"parameter must use key=value form: {value}")
        key, raw = value.split("=", 1)
        params[key] = raw
    return params


def _parse_decimal(value: Optional[str]) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value)


def _parse_bool(value: Optional[bool]) -> bool | None:
    return value


def get_client() -> PriceBuddyClient:
    base_url = os.getenv("PRICEBUDDY_URL")
    token = os.getenv("PRICEBUDDY_TOKEN")
    if not base_url:
        raise typer.BadParameter("PRICEBUDDY_URL environment variable must be set.")
    if not token:
        raise typer.BadParameter("PRICEBUDDY_TOKEN environment variable must be set.")
    return PriceBuddyClient(base_url, token)


def _build_source_strategy(
    *,
    list_container_type: str,
    list_container_value: str,
    product_title_type: str,
    product_title_value: str,
    product_url_type: str,
    product_url_value: str,
) -> ProductSourceExtractionStrategy:
    return ProductSourceExtractionStrategy(
        list_container=ScrapeStrategyRule(type=list_container_type, value=list_container_value),
        product_title=ScrapeStrategyRule(type=product_title_type, value=product_title_value),
        product_url=ScrapeStrategyRule(type=product_url_type, value=product_url_value),
    )


@app.command("whoami")
def whoami(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    """Show the current authenticated PriceBuddy user."""
    client = get_client()
    echo_json(client.get_current_user(), pretty=pretty)


@products_app.command("list")
def list_products(
    include: list[str] = typer.Option([], "--include", help="Repeat to include related resources such as tags or user."),
    sort: Optional[str] = typer.Option(None, "--sort", help="Sort field, optionally prefixed with - for descending."),
    status: Optional[ProductStatus] = typer.Option(None, "--status", help="Filter by product status."),
    favourite: Optional[bool] = typer.Option(None, "--favourite/--no-favourite", help="Filter by favourite flag."),
    only_official: Optional[bool] = typer.Option(None, "--only-official/--not-only-official", help="Filter by only_official flag."),
    per_page: int = typer.Option(25, "--per-page", help="Page size."),
    page: int = typer.Option(1, "--page", help="Page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """List products with filters, sorting, includes, and pagination."""
    client = get_client()
    filters = {
        "status": status.value if status else None,
        "favourite": str(favourite).lower() if favourite is not None else None,
        "only_official": str(only_official).lower() if only_official is not None else None,
    }
    echo_json(client.list_products(include=include or None, sort=sort, filters=filters, per_page=per_page, page=page), pretty=pretty)


@products_app.command("get")
def get_product(
    product_id: int,
    include: list[str] = typer.Option([], "--include", help="Repeat to include related resources such as tags or user."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get a single product by id."""
    echo_json(get_client().get_product(product_id, include=include or None), pretty=pretty)


@products_app.command("create")
def create_product(
    title: str = typer.Option(..., "--title", help="Product title."),
    url: str = typer.Option(..., "--url", help="Product URL to scrape."),
    product_id: Optional[int] = typer.Option(None, "--product-id", help="Optional parent product id."),
    image: Optional[str] = typer.Option(None, "--image", help="Optional image URL override."),
    status: Optional[ProductStatus] = typer.Option(None, "--status", help="Product status."),
    weight: Optional[str] = typer.Option(None, "--weight", help="Numeric weight for ranking."),
    notify_price: Optional[str] = typer.Option(None, "--notify-price", help="Target price threshold."),
    notify_percent: Optional[str] = typer.Option(None, "--notify-percent", help="Target percent threshold."),
    favourite: Optional[bool] = typer.Option(None, "--favourite/--no-favourite", help="Mark as favourite."),
    only_official: Optional[bool] = typer.Option(None, "--only-official/--not-only-official", help="Restrict to official sources."),
    create_store: Optional[bool] = typer.Option(None, "--create-store/--no-create-store", help="Auto-create a store from the URL when supported."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Create a product from a URL and notification thresholds."""
    request = ProductCreateRequest(
        title=title,
        url=url,
        product_id=product_id,
        image=image,
        status=status,
        weight=_parse_decimal(weight),
        notify_price=_parse_decimal(notify_price),
        notify_percent=_parse_decimal(notify_percent),
        favourite=favourite,
        only_official=only_official,
        create_store=create_store,
    )
    echo_json(get_client().create_product(request), pretty=pretty)


@products_app.command("update")
def update_product(
    product_id: int,
    title: str = typer.Option(..., "--title", help="Updated product title."),
    image: str = typer.Option(..., "--image", help="Current or updated image URL."),
    status: Optional[ProductStatus] = typer.Option(None, "--status", help="Updated product status."),
    weight: Optional[str] = typer.Option(None, "--weight", help="Numeric weight for ranking."),
    notify_price: Optional[str] = typer.Option(None, "--notify-price", help="Target price threshold."),
    notify_percent: Optional[str] = typer.Option(None, "--notify-percent", help="Target percent threshold."),
    favourite: Optional[bool] = typer.Option(None, "--favourite/--no-favourite", help="Mark as favourite."),
    only_official: Optional[bool] = typer.Option(None, "--only-official/--not-only-official", help="Restrict to official sources."),
    current_price: Optional[str] = typer.Option(None, "--current-price", help="Current observed price."),
    price_cache_json: Optional[str] = typer.Option(None, "--price-cache-json", help="JSON array for price_cache."),
    ignored_urls_json: Optional[str] = typer.Option(None, "--ignored-urls-json", help="JSON array of ignored URLs."),
    user_id: Optional[int] = typer.Option(None, "--user-id", help="Authenticated user id when required by the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Update a product using the full upstream update payload."""
    request = ProductUpdateRequest(
        title=title,
        image=image,
        status=status,
        weight=_parse_decimal(weight),
        notify_price=_parse_decimal(notify_price),
        notify_percent=_parse_decimal(notify_percent),
        favourite=favourite,
        only_official=only_official,
        current_price=_parse_decimal(current_price),
        price_cache=_parse_json_option(price_cache_json, "--price-cache-json"),
        ignored_urls=_parse_json_option(ignored_urls_json, "--ignored-urls-json"),
        user_id=user_id,
    )
    echo_json(get_client().update_product(product_id, request), pretty=pretty)


@products_app.command("delete")
def delete_product(
    product_id: int,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Delete a product by id."""
    echo_json(get_client().delete_product(product_id), pretty=pretty)


@product_sources_app.command("list")
def list_product_sources(
    include: list[str] = typer.Option([], "--include", help="Repeat to include store or user."),
    sort: Optional[str] = typer.Option(None, "--sort", help="Sort field, optionally prefixed with -."),
    search: Optional[str] = typer.Option(None, "--search", help="Name search string."),
    source_type: Optional[ProductSourceType] = typer.Option(None, "--type", help="Filter by source type."),
    status: Optional[ProductSourceStatus] = typer.Option(None, "--status", help="Filter by source status."),
    store_id: Optional[int] = typer.Option(None, "--store-id", help="Filter by associated store."),
    per_page: int = typer.Option(25, "--per-page", help="Page size."),
    page: int = typer.Option(1, "--page", help="Page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """List product sources with search, filters, includes, and pagination."""
    filters = {
        "type": source_type.value if source_type else None,
        "status": status.value if status else None,
        "store_id": store_id,
    }
    echo_json(
        get_client().list_product_sources(
            include=include or None,
            sort=sort,
            filters=filters,
            per_page=per_page,
            page=page,
            search=search,
        ),
        pretty=pretty,
    )


@product_sources_app.command("get")
def get_product_source(
    source_id: int,
    include: list[str] = typer.Option([], "--include", help="Repeat to include store or user."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get a single product source by id."""
    echo_json(get_client().get_product_source(source_id, include=include or None), pretty=pretty)


@product_sources_app.command("create")
def create_product_source(
    name: str = typer.Option(..., "--name", help="Source name."),
    search_url: str = typer.Option(..., "--search-url", help="Search URL containing :search_term."),
    source_type: ProductSourceType = typer.Option(..., "--type", help="Source type."),
    list_container_type: str = typer.Option(..., "--list-container-type", help="Extraction strategy type for list wrapper."),
    list_container_value: str = typer.Option(..., "--list-container-value", help="Selector/xpath/regex/jsonpath for result wrapper."),
    product_title_type: str = typer.Option(..., "--product-title-type", help="Extraction strategy type for result title."),
    product_title_value: str = typer.Option(..., "--product-title-value", help="Selector/xpath/regex/jsonpath for title."),
    product_url_type: str = typer.Option(..., "--product-url-type", help="Extraction strategy type for result URL."),
    product_url_value: str = typer.Option(..., "--product-url-value", help="Selector/xpath/regex/jsonpath for URL."),
    store_id: Optional[int] = typer.Option(None, "--store-id", help="Associated store id for online stores."),
    settings_json: Optional[str] = typer.Option(None, "--settings-json", help="Optional JSON object for source settings."),
    status: Optional[ProductSourceStatus] = typer.Option(None, "--status", help="Source status."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Optional operator notes."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Create a product source with a typed extraction strategy."""
    request = ProductSourceCreateRequest(
        name=name,
        search_url=search_url,
        type=source_type,
        extraction_strategy=_build_source_strategy(
            list_container_type=list_container_type,
            list_container_value=list_container_value,
            product_title_type=product_title_type,
            product_title_value=product_title_value,
            product_url_type=product_url_type,
            product_url_value=product_url_value,
        ),
        store_id=store_id,
        settings=_parse_json_option(settings_json, "--settings-json"),
        status=status,
        notes=notes,
    )
    echo_json(get_client().create_product_source(request), pretty=pretty)


@product_sources_app.command("update")
def update_product_source(
    source_id: int,
    name: Optional[str] = typer.Option(None, "--name", help="Updated source name."),
    search_url: Optional[str] = typer.Option(None, "--search-url", help="Updated search URL containing :search_term."),
    source_type: Optional[ProductSourceType] = typer.Option(None, "--type", help="Updated source type."),
    list_container_type: Optional[str] = typer.Option(None, "--list-container-type", help="Extraction strategy type for list wrapper."),
    list_container_value: Optional[str] = typer.Option(None, "--list-container-value", help="Selector/xpath/regex/jsonpath for result wrapper."),
    product_title_type: Optional[str] = typer.Option(None, "--product-title-type", help="Extraction strategy type for result title."),
    product_title_value: Optional[str] = typer.Option(None, "--product-title-value", help="Selector/xpath/regex/jsonpath for title."),
    product_url_type: Optional[str] = typer.Option(None, "--product-url-type", help="Extraction strategy type for result URL."),
    product_url_value: Optional[str] = typer.Option(None, "--product-url-value", help="Selector/xpath/regex/jsonpath for URL."),
    store_id: Optional[int] = typer.Option(None, "--store-id", help="Associated store id."),
    settings_json: Optional[str] = typer.Option(None, "--settings-json", help="Optional JSON object for source settings."),
    status: Optional[ProductSourceStatus] = typer.Option(None, "--status", help="Updated source status."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Optional operator notes."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Update a product source; strategy flags may be omitted for partial updates."""
    strategy = None
    if any(
        value is not None
        for value in (
            list_container_type,
            list_container_value,
            product_title_type,
            product_title_value,
            product_url_type,
            product_url_value,
        )
    ):
        required = {
            "list_container_type": list_container_type,
            "list_container_value": list_container_value,
            "product_title_type": product_title_type,
            "product_title_value": product_title_value,
            "product_url_type": product_url_type,
            "product_url_value": product_url_value,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise typer.BadParameter(f"partial strategy updates are not supported; missing {', '.join(missing)}")
        strategy = _build_source_strategy(
            list_container_type=list_container_type,
            list_container_value=list_container_value,
            product_title_type=product_title_type,
            product_title_value=product_title_value,
            product_url_type=product_url_type,
            product_url_value=product_url_value,
        )
    request = ProductSourceUpdateRequest(
        name=name,
        search_url=search_url,
        type=source_type,
        extraction_strategy=strategy,
        store_id=store_id,
        settings=_parse_json_option(settings_json, "--settings-json"),
        status=status,
        notes=notes,
    )
    echo_json(get_client().update_product_source(source_id, request), pretty=pretty)


@product_sources_app.command("delete")
def delete_product_source(source_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    """Delete a product source by id."""
    echo_json(get_client().delete_product_source(source_id), pretty=pretty)


@product_sources_app.command("search")
def search_product_source(
    source_id: int,
    query: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Run a search through one product source and return the typed result list."""
    echo_json(get_client().search_product_source(source_id, query), pretty=pretty)


@product_sources_app.command("search-all")
def search_all_product_sources(
    query: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Run a search through every configured product source."""
    echo_json(get_client().search_all_product_sources(query), pretty=pretty)


@stores_app.command("list")
def list_stores(
    include: list[str] = typer.Option([], "--include", help="Repeat to include user, urls, or products."),
    sort: Optional[str] = typer.Option(None, "--sort", help="Sort field, optionally prefixed with -."),
    search: Optional[str] = typer.Option(None, "--search", help="Name search string."),
    domain: Optional[str] = typer.Option(None, "--domain", help="Filter by one of the store domains."),
    scraper_service: Optional[ScraperService] = typer.Option(None, "--scraper-service", help="Filter by scraper service."),
    per_page: int = typer.Option(25, "--per-page", help="Page size."),
    page: int = typer.Option(1, "--page", help="Page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """List stores with search, filters, includes, and pagination."""
    filters = {
        "domains": domain,
        "scraper_service": scraper_service.value if scraper_service else None,
    }
    echo_json(get_client().list_stores(include=include or None, sort=sort, filters=filters, per_page=per_page, page=page, search=search), pretty=pretty)


@stores_app.command("get")
def get_store(
    store_id: int,
    include: list[str] = typer.Option([], "--include", help="Repeat to include user, urls, or products."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get a single store by id."""
    echo_json(get_client().get_store(store_id, include=include or None), pretty=pretty)


@stores_app.command("create")
def create_store(
    name: str = typer.Option(..., "--name", help="Store name."),
    domain: list[str] = typer.Option(..., "--domain", help="Repeat for each store domain."),
    title_type: str = typer.Option(..., "--title-type", help="Strategy type for extracting the product title."),
    title_value: str = typer.Option(..., "--title-value", help="Selector/xpath/regex/jsonpath for title."),
    price_type: str = typer.Option(..., "--price-type", help="Strategy type for extracting the product price."),
    price_value: str = typer.Option(..., "--price-value", help="Selector/xpath/regex/jsonpath for price."),
    image_type: str = typer.Option(..., "--image-type", help="Strategy type for extracting the product image."),
    image_value: str = typer.Option(..., "--image-value", help="Selector/xpath/regex/jsonpath for image."),
    scraper_service: ScraperService = typer.Option(..., "--scraper-service", help="HTTP or API scraping backend."),
    scraper_service_settings: Optional[str] = typer.Option(None, "--scraper-service-settings", help="Opaque scraper-service config string."),
    locale: Optional[str] = typer.Option(None, "--locale", help="Optional locale for parsing site prices."),
    currency: Optional[str] = typer.Option(None, "--currency", help="Optional currency override."),
    slug: Optional[str] = typer.Option(None, "--slug", help="Optional explicit slug."),
    initials: Optional[str] = typer.Option(None, "--initials", help="Optional two-character initials."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Optional operator notes."),
    user_id: Optional[int] = typer.Option(None, "--user-id", help="Authenticated user id when required by the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Create a store with typed domain, scraping, and locale settings."""
    request = StoreCreateRequest(
        name=name,
        slug=slug,
        initials=initials,
        domains=[DomainEntry(item) for item in domain],
        scrape_strategy=StoreScrapeStrategy(
            title=ScrapeStrategyRule(type=title_type, value=title_value),
            price=ScrapeStrategyRule(type=price_type, value=price_value),
            image=ScrapeStrategyRule(type=image_type, value=image_value),
        ),
        settings=StoreSettings(
            scraper_service=scraper_service.value,
            scraper_service_settings=scraper_service_settings,
            locale_settings=StoreLocaleSettings(locale=locale, currency=currency) if (locale or currency) else None,
        ),
        notes=notes,
        user_id=user_id,
    )
    echo_json(get_client().create_store(request), pretty=pretty)


@stores_app.command("update")
def update_store(
    store_id: int,
    name: Optional[str] = typer.Option(None, "--name", help="Updated store name."),
    slug: Optional[str] = typer.Option(None, "--slug", help="Optional explicit slug."),
    initials: Optional[str] = typer.Option(None, "--initials", help="Optional two-character initials."),
    domain: list[str] = typer.Option([], "--domain", help="Repeat for each store domain."),
    title_type: Optional[str] = typer.Option(None, "--title-type", help="Strategy type for extracting the product title."),
    title_value: Optional[str] = typer.Option(None, "--title-value", help="Selector/xpath/regex/jsonpath for title."),
    price_type: Optional[str] = typer.Option(None, "--price-type", help="Strategy type for extracting the product price."),
    price_value: Optional[str] = typer.Option(None, "--price-value", help="Selector/xpath/regex/jsonpath for price."),
    image_type: Optional[str] = typer.Option(None, "--image-type", help="Strategy type for extracting the product image."),
    image_value: Optional[str] = typer.Option(None, "--image-value", help="Selector/xpath/regex/jsonpath for image."),
    scraper_service: Optional[ScraperService] = typer.Option(None, "--scraper-service", help="HTTP or API scraping backend."),
    scraper_service_settings: Optional[str] = typer.Option(None, "--scraper-service-settings", help="Opaque scraper-service config string."),
    locale: Optional[str] = typer.Option(None, "--locale", help="Optional locale for parsing site prices."),
    currency: Optional[str] = typer.Option(None, "--currency", help="Optional currency override."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Optional operator notes."),
    user_id: Optional[int] = typer.Option(None, "--user-id", help="Authenticated user id when required by the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Update a store; strategy flags may be omitted for partial updates."""
    domains = [DomainEntry(item) for item in domain] if domain else None
    scrape_strategy = None
    if any(value is not None for value in (title_type, title_value, price_type, price_value, image_type, image_value)):
        required = {
            "title_type": title_type,
            "title_value": title_value,
            "price_type": price_type,
            "price_value": price_value,
            "image_type": image_type,
            "image_value": image_value,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise typer.BadParameter(f"partial scrape strategy updates are not supported; missing {', '.join(missing)}")
        scrape_strategy = StoreScrapeStrategy(
            title=ScrapeStrategyRule(type=title_type, value=title_value),
            price=ScrapeStrategyRule(type=price_type, value=price_value),
            image=ScrapeStrategyRule(type=image_type, value=image_value),
        )
    settings = None
    if any(value is not None for value in (scraper_service, scraper_service_settings, locale, currency)):
        settings = StoreSettings(
            scraper_service=(scraper_service.value if scraper_service else ScraperService.HTTP.value),
            scraper_service_settings=scraper_service_settings,
            locale_settings=StoreLocaleSettings(locale=locale, currency=currency) if (locale or currency) else None,
        )
    request = StoreUpdateRequest(
        name=name,
        slug=slug,
        initials=initials,
        domains=domains,
        scrape_strategy=scrape_strategy,
        settings=settings,
        notes=notes,
        user_id=user_id,
    )
    echo_json(get_client().update_store(store_id, request), pretty=pretty)


@stores_app.command("delete")
def delete_store(store_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    """Delete a store by id."""
    echo_json(get_client().delete_store(store_id), pretty=pretty)


@tags_app.command("list")
def list_tags(
    include: list[str] = typer.Option([], "--include", help="Repeat to include products."),
    sort: Optional[str] = typer.Option(None, "--sort", help="Sort field, optionally prefixed with -."),
    search: Optional[str] = typer.Option(None, "--search", help="Name search string."),
    exact_name: Optional[str] = typer.Option(None, "--name", help="Exact name filter."),
    per_page: int = typer.Option(25, "--per-page", help="Page size."),
    page: int = typer.Option(1, "--page", help="Page number."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """List tags with search, filters, includes, and pagination."""
    filters = {"name": exact_name}
    echo_json(get_client().list_tags(include=include or None, sort=sort, filters=filters, per_page=per_page, page=page, search=search), pretty=pretty)


@tags_app.command("get")
def get_tag(
    tag_id: int,
    include: list[str] = typer.Option([], "--include", help="Repeat to include related products."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get a single tag by id."""
    echo_json(get_client().get_tag(tag_id, include=include or None), pretty=pretty)


@tags_app.command("create")
def create_tag(
    name: str = typer.Option(..., "--name", help="Tag name."),
    user_id: Optional[int] = typer.Option(None, "--user-id", help="Authenticated user id when required by the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Create a tag."""
    echo_json(get_client().create_tag(TagCreateRequest(name=name, user_id=user_id)), pretty=pretty)


@tags_app.command("update")
def update_tag(
    tag_id: int,
    name: Optional[str] = typer.Option(None, "--name", help="Updated tag name."),
    user_id: Optional[int] = typer.Option(None, "--user-id", help="Authenticated user id when required by the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Update a tag."""
    echo_json(get_client().update_tag(tag_id, TagUpdateRequest(name=name, user_id=user_id)), pretty=pretty)


@tags_app.command("delete")
def delete_tag(tag_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    """Delete a tag by id."""
    echo_json(get_client().delete_tag(tag_id), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
