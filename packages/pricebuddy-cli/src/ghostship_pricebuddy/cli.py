from __future__ import annotations

from decimal import Decimal
import os
from typing import Any

import typer

from ghostship_cli_contract import (
    DEFAULT_TIMEOUT,
    echo_json,
    handle_cli_error,
    parse_json_option,
    parse_params,
    require_env,
    run_app,
    run_cli_command,
)

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
    ProductUpdateRequest,
    ScrapeStrategyRule,
    ScraperService,
    StoreCreateRequest,
    StoreLocaleSettings,
    StoreScrapeStrategy,
    StoreSettings,
    StoreUpdateRequest,
    TagCreateRequest,
    TagUpdateRequest,
)

app = typer.Typer(help='Typed PriceBuddy API CLI.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def _emit(data: Any, *, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _parse_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value)


def _parse_params(values: list[str]) -> dict[str, str] | None:
    parsed = parse_params(values)
    return parsed or None


def get_client() -> PriceBuddyClient:
    base_url = require_env('PRICEBUDDY_URL', os.getenv('PRICEBUDDY_URL'))
    token = require_env('PRICEBUDDY_TOKEN', os.getenv('PRICEBUDDY_TOKEN'))
    return PriceBuddyClient(base_url, token, default_timeout=APP_STATE['timeout'])


def _run(execute, *, pretty: bool) -> None:
    try:
        result = execute(get_client(), APP_STATE['timeout'])
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    try:
        client = get_client()
        result = run_cli_command(lambda: build_request(client), lambda timeout: execute(client, timeout), timeout=APP_STATE['timeout'], dry_run=dry_run)
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


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


def _build_store_scrape_strategy(
    *,
    title_type: str,
    title_value: str,
    price_type: str,
    price_value: str,
    image_type: str,
    image_value: str,
) -> StoreScrapeStrategy:
    return StoreScrapeStrategy(
        title=ScrapeStrategyRule(type=title_type, value=title_value),
        price=ScrapeStrategyRule(type=price_type, value=price_value),
        image=ScrapeStrategyRule(type=image_type, value=image_value),
    )


@app.command('request')
def request(
    method: str,
    path: str,
    param: list[str] = typer.Option([], '--param', help='Repeat key=value query parameters.'),
    body_json: str | None = typer.Option(None, '--body-json', help='Optional JSON request body.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    params = _parse_params(param)
    payload = parse_json_option(body_json, '--body-json')
    _run_write(
        lambda client: client.build_request(method, path, params=params, json_data=payload, timeout=APP_STATE['timeout']),
        lambda client, timeout: client.request(method, path, params=params, json_data=payload, timeout=timeout),
        dry_run=dry_run,
        pretty=pretty,
    )


@app.command('get_current_user')
def get_current_user(pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run(lambda client, timeout: client.get_current_user(timeout=timeout), pretty=pretty)


@app.command('list_products')
def list_products(
    include: list[str] = typer.Option([], '--include', help='Repeat to include related resources such as tags or user.'),
    sort: str | None = typer.Option(None, '--sort', help='Sort field, optionally prefixed with - for descending.'),
    status: ProductStatus | None = typer.Option(None, '--status', help='Filter by product status.'),
    favourite: bool | None = typer.Option(None, '--favourite/--no-favourite', help='Filter by favourite flag.'),
    only_official: bool | None = typer.Option(None, '--only-official/--not-only-official', help='Filter by only_official flag.'),
    per_page: int = typer.Option(25, '--per-page', help='Page size.'),
    page: int = typer.Option(1, '--page', help='Page number.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    filters = {
        'status': status.value if status else None,
        'favourite': str(favourite).lower() if favourite is not None else None,
        'only_official': str(only_official).lower() if only_official is not None else None,
    }
    _run(lambda client, timeout: client.list_products(include=include or None, sort=sort, filters=filters, per_page=per_page, page=page, timeout=timeout), pretty=pretty)


@app.command('get_product')
def get_product(product_id: int, include: list[str] = typer.Option([], '--include', help='Repeat to include related resources such as tags or user.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run(lambda client, timeout: client.get_product(product_id, include=include or None, timeout=timeout), pretty=pretty)


@app.command('create_product')
def create_product(
    title: str = typer.Option(..., '--title', help='Product title.'),
    url: str = typer.Option(..., '--url', help='Product URL to scrape.'),
    product_id: int | None = typer.Option(None, '--product-id', help='Optional parent product id.'),
    image: str | None = typer.Option(None, '--image', help='Optional image URL override.'),
    status: ProductStatus | None = typer.Option(None, '--status', help='Product status.'),
    weight: str | None = typer.Option(None, '--weight', help='Numeric weight for ranking.'),
    notify_price: str | None = typer.Option(None, '--notify-price', help='Target price threshold.'),
    notify_percent: str | None = typer.Option(None, '--notify-percent', help='Target percent threshold.'),
    favourite: bool | None = typer.Option(None, '--favourite/--no-favourite', help='Mark as favourite.'),
    only_official: bool | None = typer.Option(None, '--only-official/--not-only-official', help='Restrict to official sources.'),
    create_store: bool | None = typer.Option(None, '--create-store/--no-create-store', help='Auto-create a store from the URL when supported.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    request_obj = ProductCreateRequest(
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
    _run_write(lambda client: client.build_create_product(request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.create_product(request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('update_product')
def update_product(
    product_id: int,
    title: str = typer.Option(..., '--title', help='Updated product title.'),
    image: str = typer.Option(..., '--image', help='Current or updated image URL.'),
    status: ProductStatus | None = typer.Option(None, '--status', help='Updated product status.'),
    weight: str | None = typer.Option(None, '--weight', help='Numeric weight for ranking.'),
    notify_price: str | None = typer.Option(None, '--notify-price', help='Target price threshold.'),
    notify_percent: str | None = typer.Option(None, '--notify-percent', help='Target percent threshold.'),
    favourite: bool | None = typer.Option(None, '--favourite/--no-favourite', help='Mark as favourite.'),
    only_official: bool | None = typer.Option(None, '--only-official/--not-only-official', help='Restrict to official sources.'),
    current_price: str | None = typer.Option(None, '--current-price', help='Current observed price.'),
    price_cache_json: str | None = typer.Option(None, '--price-cache-json', help='JSON array for price_cache.'),
    ignored_urls_json: str | None = typer.Option(None, '--ignored-urls-json', help='JSON array of ignored URLs.'),
    user_id: int | None = typer.Option(None, '--user-id', help='Authenticated user id when required by the API.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    request_obj = ProductUpdateRequest(
        title=title,
        image=image,
        status=status,
        weight=_parse_decimal(weight),
        notify_price=_parse_decimal(notify_price),
        notify_percent=_parse_decimal(notify_percent),
        favourite=favourite,
        only_official=only_official,
        current_price=_parse_decimal(current_price),
        price_cache=parse_json_option(price_cache_json, '--price-cache-json'),
        ignored_urls=parse_json_option(ignored_urls_json, '--ignored-urls-json'),
        user_id=user_id,
    )
    _run_write(lambda client: client.build_update_product(product_id, request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.update_product(product_id, request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('delete_product')
def delete_product(product_id: int, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_delete_product(product_id, timeout=APP_STATE['timeout']), lambda client, timeout: client.delete_product(product_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('list_product_sources')
def list_product_sources(
    include: list[str] = typer.Option([], '--include', help='Repeat to include store or user.'),
    sort: str | None = typer.Option(None, '--sort', help='Sort field, optionally prefixed with -.'),
    search: str | None = typer.Option(None, '--search', help='Name search string.'),
    source_type: ProductSourceType | None = typer.Option(None, '--type', help='Filter by source type.'),
    status: ProductSourceStatus | None = typer.Option(None, '--status', help='Filter by source status.'),
    store_id: int | None = typer.Option(None, '--store-id', help='Filter by associated store.'),
    per_page: int = typer.Option(25, '--per-page', help='Page size.'),
    page: int = typer.Option(1, '--page', help='Page number.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    filters = {'type': source_type.value if source_type else None, 'status': status.value if status else None, 'store_id': store_id}
    _run(lambda client, timeout: client.list_product_sources(include=include or None, sort=sort, filters=filters, per_page=per_page, page=page, search=search, timeout=timeout), pretty=pretty)


@app.command('get_product_source')
def get_product_source(source_id: int, include: list[str] = typer.Option([], '--include', help='Repeat to include store or user.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run(lambda client, timeout: client.get_product_source(source_id, include=include or None, timeout=timeout), pretty=pretty)


@app.command('create_product_source')
def create_product_source(
    name: str = typer.Option(..., '--name', help='Source name.'),
    search_url: str = typer.Option(..., '--search-url', help='Search URL containing :search_term.'),
    source_type: ProductSourceType = typer.Option(..., '--type', help='Source type.'),
    list_container_type: str = typer.Option(..., '--list-container-type', help='Extraction strategy type for list wrapper.'),
    list_container_value: str = typer.Option(..., '--list-container-value', help='Selector/xpath/regex/jsonpath for result wrapper.'),
    product_title_type: str = typer.Option(..., '--product-title-type', help='Extraction strategy type for result title.'),
    product_title_value: str = typer.Option(..., '--product-title-value', help='Selector/xpath/regex/jsonpath for title.'),
    product_url_type: str = typer.Option(..., '--product-url-type', help='Extraction strategy type for result URL.'),
    product_url_value: str = typer.Option(..., '--product-url-value', help='Selector/xpath/regex/jsonpath for URL.'),
    store_id: int | None = typer.Option(None, '--store-id', help='Associated store id for online stores.'),
    settings_json: str | None = typer.Option(None, '--settings-json', help='Optional JSON object for source settings.'),
    status: ProductSourceStatus | None = typer.Option(None, '--status', help='Source status.'),
    notes: str | None = typer.Option(None, '--notes', help='Optional operator notes.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    request_obj = ProductSourceCreateRequest(
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
        settings=parse_json_option(settings_json, '--settings-json'),
        status=status,
        notes=notes,
    )
    _run_write(lambda client: client.build_create_product_source(request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.create_product_source(request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('update_product_source')
def update_product_source(
    source_id: int,
    name: str | None = typer.Option(None, '--name', help='Updated source name.'),
    search_url: str | None = typer.Option(None, '--search-url', help='Updated search URL containing :search_term.'),
    source_type: ProductSourceType | None = typer.Option(None, '--type', help='Updated source type.'),
    list_container_type: str | None = typer.Option(None, '--list-container-type', help='Extraction strategy type for list wrapper.'),
    list_container_value: str | None = typer.Option(None, '--list-container-value', help='Selector/xpath/regex/jsonpath for result wrapper.'),
    product_title_type: str | None = typer.Option(None, '--product-title-type', help='Extraction strategy type for result title.'),
    product_title_value: str | None = typer.Option(None, '--product-title-value', help='Selector/xpath/regex/jsonpath for title.'),
    product_url_type: str | None = typer.Option(None, '--product-url-type', help='Extraction strategy type for result URL.'),
    product_url_value: str | None = typer.Option(None, '--product-url-value', help='Selector/xpath/regex/jsonpath for URL.'),
    store_id: int | None = typer.Option(None, '--store-id', help='Associated store id.'),
    settings_json: str | None = typer.Option(None, '--settings-json', help='Optional JSON object for source settings.'),
    status: ProductSourceStatus | None = typer.Option(None, '--status', help='Updated source status.'),
    notes: str | None = typer.Option(None, '--notes', help='Optional operator notes.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    strategy = None
    if any(value is not None for value in (list_container_type, list_container_value, product_title_type, product_title_value, product_url_type, product_url_value)):
        required = {
            'list_container_type': list_container_type,
            'list_container_value': list_container_value,
            'product_title_type': product_title_type,
            'product_title_value': product_title_value,
            'product_url_type': product_url_type,
            'product_url_value': product_url_value,
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
    request_obj = ProductSourceUpdateRequest(
        name=name,
        search_url=search_url,
        type=source_type,
        extraction_strategy=strategy,
        store_id=store_id,
        settings=parse_json_option(settings_json, '--settings-json'),
        status=status,
        notes=notes,
    )
    _run_write(lambda client: client.build_update_product_source(source_id, request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.update_product_source(source_id, request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('delete_product_source')
def delete_product_source(source_id: int, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_delete_product_source(source_id, timeout=APP_STATE['timeout']), lambda client, timeout: client.delete_product_source(source_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('search_product_source')
def search_product_source(source_id: int, query: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run(lambda client, timeout: client.search_product_source(source_id, query, timeout=timeout), pretty=pretty)


@app.command('search_all_product_sources')
def search_all_product_sources(query: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run(lambda client, timeout: client.search_all_product_sources(query, timeout=timeout), pretty=pretty)


@app.command('list_stores')
def list_stores(
    include: list[str] = typer.Option([], '--include', help='Repeat to include user, urls, or products.'),
    sort: str | None = typer.Option(None, '--sort', help='Sort field, optionally prefixed with -.'),
    search: str | None = typer.Option(None, '--search', help='Name search string.'),
    domain: str | None = typer.Option(None, '--domain', help='Filter by one of the store domains.'),
    scraper_service: ScraperService | None = typer.Option(None, '--scraper-service', help='Filter by scraper service.'),
    per_page: int = typer.Option(25, '--per-page', help='Page size.'),
    page: int = typer.Option(1, '--page', help='Page number.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    filters = {'domains': domain, 'scraper_service': scraper_service.value if scraper_service else None}
    _run(lambda client, timeout: client.list_stores(include=include or None, sort=sort, filters=filters, per_page=per_page, page=page, search=search, timeout=timeout), pretty=pretty)


@app.command('get_store')
def get_store(store_id: int, include: list[str] = typer.Option([], '--include', help='Repeat to include user, urls, or products.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run(lambda client, timeout: client.get_store(store_id, include=include or None, timeout=timeout), pretty=pretty)


@app.command('create_store')
def create_store(
    name: str = typer.Option(..., '--name', help='Store name.'),
    domain: list[str] = typer.Option(..., '--domain', help='Repeat for each store domain.'),
    title_type: str = typer.Option(..., '--title-type', help='Strategy type for extracting the product title.'),
    title_value: str = typer.Option(..., '--title-value', help='Selector/xpath/regex/jsonpath for title.'),
    price_type: str = typer.Option(..., '--price-type', help='Strategy type for extracting the product price.'),
    price_value: str = typer.Option(..., '--price-value', help='Selector/xpath/regex/jsonpath for price.'),
    image_type: str = typer.Option(..., '--image-type', help='Strategy type for extracting the product image.'),
    image_value: str = typer.Option(..., '--image-value', help='Selector/xpath/regex/jsonpath for image.'),
    scraper_service: ScraperService = typer.Option(..., '--scraper-service', help='HTTP or API scraping backend.'),
    scraper_service_settings: str | None = typer.Option(None, '--scraper-service-settings', help='Opaque scraper-service config string.'),
    locale: str | None = typer.Option(None, '--locale', help='Optional locale for parsing site prices.'),
    currency: str | None = typer.Option(None, '--currency', help='Optional currency override.'),
    slug: str | None = typer.Option(None, '--slug', help='Optional explicit slug.'),
    initials: str | None = typer.Option(None, '--initials', help='Optional two-character initials.'),
    notes: str | None = typer.Option(None, '--notes', help='Optional operator notes.'),
    user_id: int | None = typer.Option(None, '--user-id', help='Authenticated user id when required by the API.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    request_obj = StoreCreateRequest(
        name=name,
        slug=slug,
        initials=initials,
        domains=[DomainEntry(item) for item in domain],
        scrape_strategy=_build_store_scrape_strategy(
            title_type=title_type,
            title_value=title_value,
            price_type=price_type,
            price_value=price_value,
            image_type=image_type,
            image_value=image_value,
        ),
        settings=StoreSettings(
            scraper_service=scraper_service.value,
            scraper_service_settings=scraper_service_settings,
            locale_settings=StoreLocaleSettings(locale=locale, currency=currency) if (locale or currency) else None,
        ),
        notes=notes,
        user_id=user_id,
    )
    _run_write(lambda client: client.build_create_store(request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.create_store(request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('update_store')
def update_store(
    store_id: int,
    name: str | None = typer.Option(None, '--name', help='Updated store name.'),
    slug: str | None = typer.Option(None, '--slug', help='Optional explicit slug.'),
    initials: str | None = typer.Option(None, '--initials', help='Optional two-character initials.'),
    domain: list[str] = typer.Option([], '--domain', help='Repeat for each store domain.'),
    title_type: str | None = typer.Option(None, '--title-type', help='Strategy type for extracting the product title.'),
    title_value: str | None = typer.Option(None, '--title-value', help='Selector/xpath/regex/jsonpath for title.'),
    price_type: str | None = typer.Option(None, '--price-type', help='Strategy type for extracting the product price.'),
    price_value: str | None = typer.Option(None, '--price-value', help='Selector/xpath/regex/jsonpath for price.'),
    image_type: str | None = typer.Option(None, '--image-type', help='Strategy type for extracting the product image.'),
    image_value: str | None = typer.Option(None, '--image-value', help='Selector/xpath/regex/jsonpath for image.'),
    scraper_service: ScraperService | None = typer.Option(None, '--scraper-service', help='HTTP or API scraping backend.'),
    scraper_service_settings: str | None = typer.Option(None, '--scraper-service-settings', help='Opaque scraper-service config string.'),
    locale: str | None = typer.Option(None, '--locale', help='Optional locale for parsing site prices.'),
    currency: str | None = typer.Option(None, '--currency', help='Optional currency override.'),
    notes: str | None = typer.Option(None, '--notes', help='Optional operator notes.'),
    user_id: int | None = typer.Option(None, '--user-id', help='Authenticated user id when required by the API.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    domains = [DomainEntry(item) for item in domain] if domain else None
    scrape_strategy = None
    if any(value is not None for value in (title_type, title_value, price_type, price_value, image_type, image_value)):
        required = {
            'title_type': title_type,
            'title_value': title_value,
            'price_type': price_type,
            'price_value': price_value,
            'image_type': image_type,
            'image_value': image_value,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise typer.BadParameter(f"partial scrape strategy updates are not supported; missing {', '.join(missing)}")
        scrape_strategy = _build_store_scrape_strategy(
            title_type=title_type,
            title_value=title_value,
            price_type=price_type,
            price_value=price_value,
            image_type=image_type,
            image_value=image_value,
        )
    settings = None
    if any(value is not None for value in (scraper_service, scraper_service_settings, locale, currency)):
        settings = StoreSettings(
            scraper_service=(scraper_service.value if scraper_service else ScraperService.HTTP.value),
            scraper_service_settings=scraper_service_settings,
            locale_settings=StoreLocaleSettings(locale=locale, currency=currency) if (locale or currency) else None,
        )
    request_obj = StoreUpdateRequest(
        name=name,
        slug=slug,
        initials=initials,
        domains=domains,
        scrape_strategy=scrape_strategy,
        settings=settings,
        notes=notes,
        user_id=user_id,
    )
    _run_write(lambda client: client.build_update_store(store_id, request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.update_store(store_id, request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('delete_store')
def delete_store(store_id: int, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_delete_store(store_id, timeout=APP_STATE['timeout']), lambda client, timeout: client.delete_store(store_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('list_tags')
def list_tags(
    include: list[str] = typer.Option([], '--include', help='Repeat to include products.'),
    sort: str | None = typer.Option(None, '--sort', help='Sort field, optionally prefixed with -.'),
    search: str | None = typer.Option(None, '--search', help='Name search string.'),
    exact_name: str | None = typer.Option(None, '--name', help='Exact name filter.'),
    per_page: int = typer.Option(25, '--per-page', help='Page size.'),
    page: int = typer.Option(1, '--page', help='Page number.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    filters = {'name': exact_name}
    _run(lambda client, timeout: client.list_tags(include=include or None, sort=sort, filters=filters, per_page=per_page, page=page, search=search, timeout=timeout), pretty=pretty)


@app.command('get_tag')
def get_tag(tag_id: int, include: list[str] = typer.Option([], '--include', help='Repeat to include related products.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run(lambda client, timeout: client.get_tag(tag_id, include=include or None, timeout=timeout), pretty=pretty)


@app.command('create_tag')
def create_tag(name: str = typer.Option(..., '--name', help='Tag name.'), user_id: int | None = typer.Option(None, '--user-id', help='Authenticated user id when required by the API.'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    request_obj = TagCreateRequest(name=name, user_id=user_id)
    _run_write(lambda client: client.build_create_tag(request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.create_tag(request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('update_tag')
def update_tag(tag_id: int, name: str | None = typer.Option(None, '--name', help='Updated tag name.'), user_id: int | None = typer.Option(None, '--user-id', help='Authenticated user id when required by the API.'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    request_obj = TagUpdateRequest(name=name, user_id=user_id)
    _run_write(lambda client: client.build_update_tag(tag_id, request_obj, timeout=APP_STATE['timeout']), lambda client, timeout: client.update_tag(tag_id, request_obj, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('delete_tag')
def delete_tag(tag_id: int, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_delete_tag(tag_id, timeout=APP_STATE['timeout']), lambda client, timeout: client.delete_tag(tag_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
