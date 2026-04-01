from __future__ import annotations

from dataclasses import dataclass, field, asdict, is_dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Generic, Mapping, TypeVar
from urllib.parse import quote

from ghostship_cli_contract import BaseHttpClient, RequestSpec


T = TypeVar("T")


def _compact_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


def _serialize_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


class ProductStatus(str, Enum):
    PUBLISHED = "p"
    ARCHIVED = "a"


class ProductSourceType(str, Enum):
    DEALS_SITE = "deals_site"
    ONLINE_STORE = "online_store"


class ProductSourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class ScraperService(str, Enum):
    HTTP = "http"
    API = "api"


class ScraperStrategyType(str, Enum):
    SCHEMA_ORG = "schema_org"
    SELECTOR = "selector"
    XPATH = "xpath"
    REGEX = "regex"
    JSON = "json"


@dataclass(slots=True)
class DomainEntry:
    domain: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DomainEntry":
        return cls(domain=str(data.get("domain", "")))

    def to_dict(self) -> dict[str, Any]:
        return {"domain": self.domain}


@dataclass(slots=True)
class ScrapeStrategyRule:
    type: str
    value: str | None = None
    prepend: str | None = None
    append: str | None = None
    data: Any = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ScrapeStrategyRule":
        return cls(
            type=str(data.get("type", "")),
            value=data.get("value"),
            prepend=data.get("prepend"),
            append=data.get("append"),
            data=data.get("data"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "type": self.type,
            "value": self.value,
            "prepend": self.prepend,
            "append": self.append,
        }
        if self.data is not None:
            payload["data"] = self.data
        return _compact_dict(payload)


@dataclass(slots=True)
class StoreLocaleSettings:
    locale: str | None = None
    currency: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "StoreLocaleSettings | None":
        if data is None:
            return None
        return cls(locale=data.get("locale"), currency=data.get("currency"))

    def to_dict(self) -> dict[str, Any]:
        return _compact_dict({"locale": self.locale, "currency": self.currency})


@dataclass(slots=True)
class StoreSettings:
    scraper_service: str
    scraper_service_settings: str | None = None
    locale_settings: StoreLocaleSettings | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StoreSettings":
        return cls(
            scraper_service=str(data.get("scraper_service", "")),
            scraper_service_settings=data.get("scraper_service_settings"),
            locale_settings=StoreLocaleSettings.from_dict(data.get("locale_settings")),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "scraper_service": self.scraper_service,
            "scraper_service_settings": self.scraper_service_settings,
        }
        if self.locale_settings is not None:
            payload["locale_settings"] = self.locale_settings.to_dict()
        return _compact_dict(payload)


@dataclass(slots=True)
class ProductSourceExtractionStrategy:
    list_container: ScrapeStrategyRule
    product_title: ScrapeStrategyRule
    product_url: ScrapeStrategyRule

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProductSourceExtractionStrategy":
        return cls(
            list_container=ScrapeStrategyRule.from_dict(data.get("list_container", {})),
            product_title=ScrapeStrategyRule.from_dict(data.get("product_title", {})),
            product_url=ScrapeStrategyRule.from_dict(data.get("product_url", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "list_container": self.list_container.to_dict(),
            "product_title": self.product_title.to_dict(),
            "product_url": self.product_url.to_dict(),
        }


@dataclass(slots=True)
class StoreScrapeStrategy:
    title: ScrapeStrategyRule
    price: ScrapeStrategyRule
    image: ScrapeStrategyRule

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StoreScrapeStrategy":
        return cls(
            title=ScrapeStrategyRule.from_dict(data.get("title", {})),
            price=ScrapeStrategyRule.from_dict(data.get("price", {})),
            image=ScrapeStrategyRule.from_dict(data.get("image", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title.to_dict(),
            "price": self.price.to_dict(),
            "image": self.image.to_dict(),
        }


@dataclass(slots=True)
class UserSummary:
    id: int
    name: str
    email: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "UserSummary":
        return cls(id=int(data["id"]), name=str(data.get("name", "")), email=data.get("email"))

    def to_dict(self) -> dict[str, Any]:
        return _compact_dict({"id": self.id, "name": self.name, "email": self.email})


@dataclass(slots=True)
class Tag:
    id: int
    name: str
    user_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    products: list[dict[str, Any]] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Tag":
        known = {"id", "name", "user_id", "created_at", "updated_at", "products"}
        return cls(
            id=int(data["id"]),
            name=str(data.get("name", "")),
            user_id=int(data["user_id"]) if data.get("user_id") is not None else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            products=list(data["products"]) if data.get("products") is not None else None,
            extra={k: v for k, v in data.items() if k not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "products": self.products,
        }
        data.update(self.extra)
        return _compact_dict(data)


@dataclass(slots=True)
class Product:
    id: int
    title: str
    image: str | None = None
    status: str | None = None
    notify_price: Decimal | None = None
    notify_percent: Decimal | None = None
    favourite: bool | None = None
    only_official: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    weight: Decimal | None = None
    current_price: Decimal | None = None
    tags: list[dict[str, Any]] | None = None
    user: dict[str, Any] | None = None
    urls: list[dict[str, Any]] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Product":
        known = {
            "id", "title", "image", "status", "notify_price", "notify_percent", "favourite",
            "only_official", "created_at", "updated_at", "weight", "current_price", "tags", "user", "urls",
        }
        return cls(
            id=int(data["id"]),
            title=str(data.get("title", "")),
            image=data.get("image"),
            status=data.get("status"),
            notify_price=_decimal(data.get("notify_price")),
            notify_percent=_decimal(data.get("notify_percent")),
            favourite=data.get("favourite"),
            only_official=data.get("only_official"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            weight=_decimal(data.get("weight")),
            current_price=_decimal(data.get("current_price")),
            tags=list(data["tags"]) if data.get("tags") is not None else None,
            user=dict(data["user"]) if isinstance(data.get("user"), Mapping) else None,
            urls=list(data["urls"]) if data.get("urls") is not None else None,
            extra={k: v for k, v in data.items() if k not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "title": self.title,
            "image": self.image,
            "status": self.status,
            "notify_price": _serialize_decimal(self.notify_price),
            "notify_percent": _serialize_decimal(self.notify_percent),
            "favourite": self.favourite,
            "only_official": self.only_official,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "weight": _serialize_decimal(self.weight),
            "current_price": _serialize_decimal(self.current_price),
            "tags": self.tags,
            "user": self.user,
            "urls": self.urls,
        }
        data.update(self.extra)
        return _compact_dict(data)


@dataclass(slots=True)
class ProductSource:
    id: int
    name: str
    slug: str | None = None
    type: str | None = None
    status: str | None = None
    user_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    store: dict[str, Any] | None = None
    user: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProductSource":
        known = {"id", "name", "slug", "type", "status", "user_id", "created_at", "updated_at", "store", "user"}
        return cls(
            id=int(data["id"]),
            name=str(data.get("name", "")),
            slug=data.get("slug"),
            type=data.get("type"),
            status=data.get("status"),
            user_id=int(data["user_id"]) if data.get("user_id") is not None else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            store=dict(data["store"]) if isinstance(data.get("store"), Mapping) else None,
            user=dict(data["user"]) if isinstance(data.get("user"), Mapping) else None,
            extra={k: v for k, v in data.items() if k not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "type": self.type,
            "status": self.status,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "store": self.store,
            "user": self.user,
        }
        data.update(self.extra)
        return _compact_dict(data)


@dataclass(slots=True)
class Store:
    id: int
    name: str
    slug: str | None = None
    initials: str | None = None
    domains: list[dict[str, Any]] | None = None
    scrape_strategy: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    user: dict[str, Any] | None = None
    urls: list[dict[str, Any]] | None = None
    products: list[dict[str, Any]] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Store":
        known = {"id", "name", "slug", "initials", "domains", "scrape_strategy", "settings", "created_at", "updated_at", "user", "urls", "products"}
        return cls(
            id=int(data["id"]),
            name=str(data.get("name", "")),
            slug=data.get("slug"),
            initials=data.get("initials"),
            domains=list(data["domains"]) if data.get("domains") is not None else None,
            scrape_strategy=dict(data["scrape_strategy"]) if isinstance(data.get("scrape_strategy"), Mapping) else None,
            settings=dict(data["settings"]) if isinstance(data.get("settings"), Mapping) else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            user=dict(data["user"]) if isinstance(data.get("user"), Mapping) else None,
            urls=list(data["urls"]) if data.get("urls") is not None else None,
            products=list(data["products"]) if data.get("products") is not None else None,
            extra={k: v for k, v in data.items() if k not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "initials": self.initials,
            "domains": self.domains,
            "scrape_strategy": self.scrape_strategy,
            "settings": self.settings,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user": self.user,
            "urls": self.urls,
            "products": self.products,
        }
        data.update(self.extra)
        return _compact_dict(data)


@dataclass(slots=True)
class ProductSourceSearchResult:
    title: str
    url: str
    source: str | None = None
    source_id: int | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProductSourceSearchResult":
        return cls(
            title=str(data.get("title", "")),
            url=str(data.get("url", "")),
            source=data.get("source"),
            source_id=int(data["source_id"]) if data.get("source_id") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return _compact_dict({
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "source_id": self.source_id,
        })


@dataclass(slots=True)
class PaginatedResponse(Generic[T]):
    data: list[T]
    links: dict[str, Any]
    meta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": [to_jsonable(item) for item in self.data],
            "links": self.links,
            "meta": self.meta,
        }


@dataclass(slots=True)
class ProductCreateRequest:
    title: str
    url: str
    product_id: int | None = None
    image: str | None = None
    status: ProductStatus | str | None = None
    weight: Decimal | None = None
    notify_price: Decimal | None = None
    notify_percent: Decimal | None = None
    favourite: bool | None = None
    only_official: bool | None = None
    create_store: bool | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": self.title,
            "url": self.url,
            "product_id": self.product_id,
            "image": self.image,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "weight": _serialize_decimal(self.weight),
            "notify_price": _serialize_decimal(self.notify_price),
            "notify_percent": _serialize_decimal(self.notify_percent),
            "favourite": self.favourite,
            "only_official": self.only_official,
            "create_store": self.create_store,
        }
        return _compact_dict(payload)


@dataclass(slots=True)
class ProductUpdateRequest:
    title: str
    image: str
    status: ProductStatus | str | None = None
    weight: Decimal | None = None
    notify_price: Decimal | None = None
    notify_percent: Decimal | None = None
    favourite: bool | None = None
    only_official: bool | None = None
    current_price: Decimal | None = None
    price_cache: list[dict[str, Any]] | None = None
    ignored_urls: list[str] | None = None
    user_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": self.title,
            "image": self.image,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "weight": _serialize_decimal(self.weight),
            "notify_price": _serialize_decimal(self.notify_price),
            "notify_percent": _serialize_decimal(self.notify_percent),
            "favourite": self.favourite,
            "only_official": self.only_official,
            "current_price": _serialize_decimal(self.current_price),
            "price_cache": self.price_cache,
            "ignored_urls": self.ignored_urls,
            "user_id": self.user_id,
        }
        return _compact_dict(payload)


@dataclass(slots=True)
class ProductSourceCreateRequest:
    name: str
    search_url: str
    type: ProductSourceType | str
    extraction_strategy: ProductSourceExtractionStrategy
    store_id: int | None = None
    settings: dict[str, Any] | None = None
    status: ProductSourceStatus | str | None = None
    notes: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "search_url": self.search_url,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "store_id": self.store_id,
            "extraction_strategy": self.extraction_strategy.to_dict(),
            "settings": self.settings,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "notes": self.notes,
        }
        return _compact_dict(payload)


@dataclass(slots=True)
class ProductSourceUpdateRequest:
    name: str | None = None
    search_url: str | None = None
    type: ProductSourceType | str | None = None
    extraction_strategy: ProductSourceExtractionStrategy | None = None
    store_id: int | None = None
    settings: dict[str, Any] | None = None
    status: ProductSourceStatus | str | None = None
    notes: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "search_url": self.search_url,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "store_id": self.store_id,
            "settings": self.settings,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "notes": self.notes,
        }
        if self.extraction_strategy is not None:
            payload["extraction_strategy"] = self.extraction_strategy.to_dict()
        return _compact_dict(payload)


@dataclass(slots=True)
class StoreCreateRequest:
    name: str
    domains: list[DomainEntry]
    scrape_strategy: StoreScrapeStrategy
    settings: StoreSettings
    slug: str | None = None
    initials: str | None = None
    notes: str | None = None
    user_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "slug": self.slug,
            "initials": self.initials,
            "domains": [domain.to_dict() for domain in self.domains],
            "scrape_strategy": self.scrape_strategy.to_dict(),
            "settings": self.settings.to_dict(),
            "notes": self.notes,
            "user_id": self.user_id,
        }
        return _compact_dict(payload)


@dataclass(slots=True)
class StoreUpdateRequest:
    name: str | None = None
    slug: str | None = None
    initials: str | None = None
    domains: list[DomainEntry] | None = None
    scrape_strategy: StoreScrapeStrategy | None = None
    settings: StoreSettings | None = None
    notes: str | None = None
    user_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "slug": self.slug,
            "initials": self.initials,
            "notes": self.notes,
            "user_id": self.user_id,
        }
        if self.domains is not None:
            payload["domains"] = [domain.to_dict() for domain in self.domains]
        if self.scrape_strategy is not None:
            payload["scrape_strategy"] = self.scrape_strategy.to_dict()
        if self.settings is not None:
            payload["settings"] = self.settings.to_dict()
        return _compact_dict(payload)


@dataclass(slots=True)
class TagCreateRequest:
    name: str
    user_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        return _compact_dict({"name": self.name, "user_id": self.user_id})


@dataclass(slots=True)
class TagUpdateRequest:
    name: str | None = None
    user_id: int | None = None

    def to_payload(self) -> dict[str, Any]:
        return _compact_dict({"name": self.name, "user_id": self.user_id})


def to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


class PriceBuddyClient(BaseHttpClient):
    def __init__(self, base_url: str, token: str, *, default_timeout: float = 30.0):
        super().__init__(
            base_url,
            default_headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            default_timeout=default_timeout,
        )

    def _api_path(self, path: str) -> str:
        if path.startswith('/api/'):
            return path
        if path.startswith('/'):
            return f'/api{path}'
        return f'/api/{path}'

    def build_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_data: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        return self.build_request_spec(method, self._api_path(path), params=dict(params) if params else None, json_body=json_data, timeout=timeout)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_data: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        return self.request_json(method, self._api_path(path), params=dict(params) if params else None, json_body=json_data, timeout=timeout)

    def _build_collection_params(
        self,
        *,
        include: list[str] | None = None,
        sort: str | None = None,
        filters: Mapping[str, Any] | None = None,
        per_page: int | None = None,
        page: int | None = None,
        search: str | None = None,
    ) -> dict[str, str]:
        params: dict[str, str] = {}
        if include:
            params['include'] = ','.join(include)
        if sort:
            params['sort'] = sort
        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                params[f'filter[{key}]'] = str(value)
        if per_page is not None:
            params['per_page'] = str(per_page)
        if page is not None:
            params['page'] = str(page)
        if search:
            params['search'] = search
        return params

    def _parse_page(self, payload: Mapping[str, Any], item_parser: Callable[[Mapping[str, Any]], T]) -> PaginatedResponse[T]:
        return PaginatedResponse(
            data=[item_parser(item) for item in payload.get('data', [])],
            links=dict(payload.get('links', {})),
            meta=dict(payload.get('meta', {})),
        )

    def get_current_user(self, *, timeout: float | None = None) -> UserSummary:
        return UserSummary.from_dict(self.request('GET', 'user', timeout=timeout))

    def list_products(
        self,
        *,
        include: list[str] | None = None,
        sort: str | None = None,
        filters: Mapping[str, Any] | None = None,
        per_page: int | None = None,
        page: int | None = None,
        timeout: float | None = None,
    ) -> PaginatedResponse[Product]:
        params = self._build_collection_params(include=include, sort=sort, filters=filters, per_page=per_page, page=page)
        return self._parse_page(self.request('GET', 'products', params=params, timeout=timeout), Product.from_dict)

    def get_product(self, product_id: int, *, include: list[str] | None = None, timeout: float | None = None) -> Product:
        params = {'include': ','.join(include)} if include else None
        return Product.from_dict(self.request('GET', f'products/{product_id}', params=params, timeout=timeout)['data'])

    def build_create_product(self, request: ProductCreateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('POST', 'products', json_data=request.to_payload(), timeout=timeout)

    def create_product(self, request: ProductCreateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('POST', 'products', json_data=request.to_payload(), timeout=timeout)

    def build_update_product(self, product_id: int, request: ProductUpdateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('PUT', f'products/{product_id}', json_data=request.to_payload(), timeout=timeout)

    def update_product(self, product_id: int, request: ProductUpdateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('PUT', f'products/{product_id}', json_data=request.to_payload(), timeout=timeout)

    def build_delete_product(self, product_id: int, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('DELETE', f'products/{product_id}', timeout=timeout)

    def delete_product(self, product_id: int, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('DELETE', f'products/{product_id}', timeout=timeout)

    def list_product_sources(
        self,
        *,
        include: list[str] | None = None,
        sort: str | None = None,
        filters: Mapping[str, Any] | None = None,
        per_page: int | None = None,
        page: int | None = None,
        search: str | None = None,
        timeout: float | None = None,
    ) -> PaginatedResponse[ProductSource]:
        params = self._build_collection_params(include=include, sort=sort, filters=filters, per_page=per_page, page=page, search=search)
        return self._parse_page(self.request('GET', 'product-sources', params=params, timeout=timeout), ProductSource.from_dict)

    def get_product_source(self, source_id: int, *, include: list[str] | None = None, timeout: float | None = None) -> ProductSource:
        params = {'include': ','.join(include)} if include else None
        return ProductSource.from_dict(self.request('GET', f'product-sources/{source_id}', params=params, timeout=timeout)['data'])

    def build_create_product_source(self, request: ProductSourceCreateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('POST', 'product-sources', json_data=request.to_payload(), timeout=timeout)

    def create_product_source(self, request: ProductSourceCreateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('POST', 'product-sources', json_data=request.to_payload(), timeout=timeout)

    def build_update_product_source(self, source_id: int, request: ProductSourceUpdateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('PUT', f'product-sources/{source_id}', json_data=request.to_payload(), timeout=timeout)

    def update_product_source(self, source_id: int, request: ProductSourceUpdateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('PUT', f'product-sources/{source_id}', json_data=request.to_payload(), timeout=timeout)

    def build_delete_product_source(self, source_id: int, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('DELETE', f'product-sources/{source_id}', timeout=timeout)

    def delete_product_source(self, source_id: int, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('DELETE', f'product-sources/{source_id}', timeout=timeout)

    def search_product_source(self, source_id: int, query: str, *, timeout: float | None = None) -> list[ProductSourceSearchResult]:
        encoded = quote(query, safe='')
        payload = self.request('GET', f'product-sources/{source_id}/search/{encoded}', timeout=timeout)
        items = payload.get('data', payload) if isinstance(payload, Mapping) else payload
        return [ProductSourceSearchResult.from_dict(item) for item in items]

    def search_all_product_sources(self, query: str, *, timeout: float | None = None) -> list[ProductSourceSearchResult]:
        encoded = quote(query, safe='')
        payload = self.request('GET', f'product-sources/search/{encoded}', timeout=timeout)
        items = payload.get('data', payload) if isinstance(payload, Mapping) else payload
        return [ProductSourceSearchResult.from_dict(item) for item in items]

    def list_stores(
        self,
        *,
        include: list[str] | None = None,
        sort: str | None = None,
        filters: Mapping[str, Any] | None = None,
        per_page: int | None = None,
        page: int | None = None,
        search: str | None = None,
        timeout: float | None = None,
    ) -> PaginatedResponse[Store]:
        params = self._build_collection_params(include=include, sort=sort, filters=filters, per_page=per_page, page=page, search=search)
        return self._parse_page(self.request('GET', 'stores', params=params, timeout=timeout), Store.from_dict)

    def get_store(self, store_id: int, *, include: list[str] | None = None, timeout: float | None = None) -> Store:
        params = {'include': ','.join(include)} if include else None
        return Store.from_dict(self.request('GET', f'stores/{store_id}', params=params, timeout=timeout)['data'])

    def build_create_store(self, request: StoreCreateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('POST', 'stores', json_data=request.to_payload(), timeout=timeout)

    def create_store(self, request: StoreCreateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('POST', 'stores', json_data=request.to_payload(), timeout=timeout)

    def build_update_store(self, store_id: int, request: StoreUpdateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('PUT', f'stores/{store_id}', json_data=request.to_payload(), timeout=timeout)

    def update_store(self, store_id: int, request: StoreUpdateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('PUT', f'stores/{store_id}', json_data=request.to_payload(), timeout=timeout)

    def build_delete_store(self, store_id: int, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('DELETE', f'stores/{store_id}', timeout=timeout)

    def delete_store(self, store_id: int, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('DELETE', f'stores/{store_id}', timeout=timeout)

    def list_tags(
        self,
        *,
        include: list[str] | None = None,
        sort: str | None = None,
        filters: Mapping[str, Any] | None = None,
        per_page: int | None = None,
        page: int | None = None,
        search: str | None = None,
        timeout: float | None = None,
    ) -> PaginatedResponse[Tag]:
        params = self._build_collection_params(include=include, sort=sort, filters=filters, per_page=per_page, page=page, search=search)
        return self._parse_page(self.request('GET', 'tags', params=params, timeout=timeout), Tag.from_dict)

    def get_tag(self, tag_id: int, *, include: list[str] | None = None, timeout: float | None = None) -> Tag:
        params = {'include': ','.join(include)} if include else None
        return Tag.from_dict(self.request('GET', f'tags/{tag_id}', params=params, timeout=timeout)['data'])

    def build_create_tag(self, request: TagCreateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('POST', 'tags', json_data=request.to_payload(), timeout=timeout)

    def create_tag(self, request: TagCreateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('POST', 'tags', json_data=request.to_payload(), timeout=timeout)

    def build_update_tag(self, tag_id: int, request: TagUpdateRequest, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('PUT', f'tags/{tag_id}', json_data=request.to_payload(), timeout=timeout)

    def update_tag(self, tag_id: int, request: TagUpdateRequest, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('PUT', f'tags/{tag_id}', json_data=request.to_payload(), timeout=timeout)

    def build_delete_tag(self, tag_id: int, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request('DELETE', f'tags/{tag_id}', timeout=timeout)

    def delete_tag(self, tag_id: int, *, timeout: float | None = None) -> dict[str, Any]:
        return self.request('DELETE', f'tags/{tag_id}', timeout=timeout)
