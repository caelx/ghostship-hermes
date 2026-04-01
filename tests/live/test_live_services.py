from __future__ import annotations

from typing import Any
import time

import pytest

pytestmark = pytest.mark.integration


def assert_or_skip_known_live_failure(exc: AssertionError, *patterns: str) -> None:
    message = str(exc)
    for pattern in patterns:
        if pattern in message:
            pytest.skip(message)
    raise exc


def assert_json_payload(payload: Any) -> None:
    assert isinstance(payload, (dict, list)), f"expected JSON object or array, got {type(payload)!r}"


def first_item(payload: Any) -> Any | None:
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict):
        for key in ("records", "results", "series", "movies", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list) and value:
                return value[0]
        for value in payload.values():
            if isinstance(value, list) and value:
                return value[0]
    return None


def pick_id(item: Any, *keys: str) -> Any | None:
    if not isinstance(item, dict):
        return None
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None


def test_live_searxng(cli_runner) -> None:
    payload = cli_runner(
        "ghostship_searxng.cli",
        "search",
        "web",
        "ghostship hermes",
        "--limit",
        "3",
    )
    assert_json_payload(payload)
    assert "results" in payload
    assert isinstance(payload["results"], list)


def test_live_sonarr(cli_runner) -> None:
    info = cli_runner("ghostship_sonarr.cli", "info")
    series = cli_runner("ghostship_sonarr.cli", "list-series")
    lookup = cli_runner("ghostship_sonarr.cli", "lookup", "the office")
    history = cli_runner("ghostship_sonarr.cli", "history", "--page-size", "5")
    queue = cli_runner("ghostship_sonarr.cli", "queue")
    missing = cli_runner("ghostship_sonarr.cli", "missing", "--page-size", "5")
    blocklist = cli_runner("ghostship_sonarr.cli", "blocklist", "--page-size", "5")
    tags = cli_runner("ghostship_sonarr.cli", "tags")
    rootfolders = cli_runner("ghostship_sonarr.cli", "rootfolders")
    profiles = cli_runner("ghostship_sonarr.cli", "profiles")

    for payload in (info, series, lookup, history, queue, missing, blocklist, tags, rootfolders, profiles):
        assert_json_payload(payload)

    item = first_item(series)
    series_id = pick_id(item, "id", "seriesId")
    if series_id is not None:
        detail = cli_runner("ghostship_sonarr.cli", "get-series", str(series_id))
        assert_json_payload(detail)


def test_live_radarr(cli_runner) -> None:
    info = cli_runner("ghostship_radarr.cli", "info")
    movies = cli_runner("ghostship_radarr.cli", "list-movies")
    lookup = cli_runner("ghostship_radarr.cli", "lookup", "inception")
    history = cli_runner("ghostship_radarr.cli", "history", "--page-size", "5")
    queue = cli_runner("ghostship_radarr.cli", "queue")
    missing = cli_runner("ghostship_radarr.cli", "missing", "--page-size", "5")
    blocklist = cli_runner("ghostship_radarr.cli", "blocklist", "--page-size", "5")
    tags = cli_runner("ghostship_radarr.cli", "tags")
    rootfolders = cli_runner("ghostship_radarr.cli", "rootfolders")
    profiles = cli_runner("ghostship_radarr.cli", "profiles")

    for payload in (info, movies, lookup, history, queue, missing, blocklist, tags, rootfolders, profiles):
        assert_json_payload(payload)

    item = first_item(movies)
    movie_id = pick_id(item, "id", "movieFileId")
    if movie_id is not None:
        detail = cli_runner("ghostship_radarr.cli", "get-movie", str(movie_id))
        assert_json_payload(detail)


def test_live_prowlarr(cli_runner) -> None:
    info = cli_runner("ghostship_prowlarr.cli", "info")
    indexers = cli_runner("ghostship_prowlarr.cli", "list-indexers")
    apps = cli_runner("ghostship_prowlarr.cli", "list-apps")
    stats = cli_runner("ghostship_prowlarr.cli", "indexer-stats")
    status = cli_runner("ghostship_prowlarr.cli", "indexer-status")
    try:
        search = cli_runner("ghostship_prowlarr.cli", "search", "ubuntu")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "timed out")
    else:
        assert_json_payload(search)

    for payload in (info, indexers, apps, stats, status):
        assert_json_payload(payload)


def test_live_plex(cli_runner) -> None:
    info = cli_runner("ghostship_plex.cli", "info")
    libraries = cli_runner("ghostship_plex.cli", "libraries")
    sessions = cli_runner("ghostship_plex.cli", "sessions")
    playlists = cli_runner("ghostship_plex.cli", "playlists")
    prefs = cli_runner("ghostship_plex.cli", "prefs")
    tasks = cli_runner("ghostship_plex.cli", "tasks")

    for payload in (info, libraries, sessions, playlists, prefs, tasks):
        assert_json_payload(payload)

    section = first_item(libraries)
    section_id = pick_id(section, "key", "id")
    if section_id is not None:
        library = cli_runner("ghostship_plex.cli", "library", str(section_id))
        collections = cli_runner("ghostship_plex.cli", "collections", str(section_id))
        assert_json_payload(library)
        assert_json_payload(collections)

        item = first_item(library)
        rating_key = pick_id(item, "ratingKey", "rating_key")
        if rating_key is not None:
            metadata = cli_runner("ghostship_plex.cli", "metadata", str(rating_key))
            assert_json_payload(metadata)


def test_live_romm(cli_runner) -> None:
    heartbeat = cli_runner("ghostship_romm.cli", "heartbeat")
    config = cli_runner("ghostship_romm.cli", "config")

    for payload in (heartbeat, config):
        assert_json_payload(payload)

    optional_reads = [
        ("platforms",),
        ("list-collections",),
        ("saves", "--page-size", "5"),
        ("saves-summary",),
        ("users",),
        ("me",),
        ("list-roms", "--page-size", "5"),
    ]
    for command in optional_reads:
        try:
            payload = cli_runner("ghostship_romm.cli", *command)
        except AssertionError as exc:
            assert_or_skip_known_live_failure(exc, "403 Forbidden", "422 Unprocessable Entity")
        else:
            assert_json_payload(payload)
            if command[0] == "list-roms":
                item = first_item(payload)
                rom_id = pick_id(item, "id", "rom_id")
                if rom_id is not None:
                    detail = cli_runner("ghostship_romm.cli", "get-rom", str(rom_id))
                    assert_json_payload(detail)


def test_live_nzbget(cli_runner) -> None:
    info = cli_runner("ghostship_nzbget.cli", "info")
    version = cli_runner("ghostship_nzbget.cli", "version")
    queue = cli_runner("ghostship_nzbget.cli", "list-queue")
    history = cli_runner("ghostship_nzbget.cli", "history")
    config = cli_runner("ghostship_nzbget.cli", "config")

    for payload in (info, version, queue, history, config):
        assert_json_payload(payload)

    item = first_item(queue)
    nzb_id = pick_id(item, "NZBID", "NzbID", "ID")
    if nzb_id is not None:
        files = cli_runner("ghostship_nzbget.cli", "list-files", str(nzb_id))
        assert_json_payload(files)


def test_live_qbittorrent(cli_runner) -> None:
    info = cli_runner("ghostship_qbittorrent.cli", "info")
    app_info = cli_runner("ghostship_qbittorrent.cli", "app-info")
    prefs = cli_runner("ghostship_qbittorrent.cli", "prefs")
    log = cli_runner("ghostship_qbittorrent.cli", "log")
    torrents = cli_runner("ghostship_qbittorrent.cli", "list-torrents")
    rss = cli_runner("ghostship_qbittorrent.cli", "rss")

    for payload in (info, app_info, prefs, log, torrents, rss):
        assert_json_payload(payload)


def test_live_grimmory(cli_runner) -> None:
    info = cli_runner("ghostship_grimmory.cli", "info")
    books = cli_runner("ghostship_grimmory.cli", "list-books")
    libraries = cli_runner("ghostship_grimmory.cli", "list-libraries")
    authors = cli_runner("ghostship_grimmory.cli", "list-authors")
    shelves = cli_runner("ghostship_grimmory.cli", "list-shelves")
    tasks = cli_runner("ghostship_grimmory.cli", "list-tasks")

    for payload in (info, books, libraries, authors, shelves, tasks):
        assert_json_payload(payload)

    item = first_item(books)
    book_id = pick_id(item, "id", "bookId")
    if book_id is not None:
        detail = cli_runner("ghostship_grimmory.cli", "get-book", str(book_id))
        assert_json_payload(detail)


def test_live_tautulli(cli_runner) -> None:
    info = cli_runner("ghostship_tautulli.cli", "info")
    activity = cli_runner("ghostship_tautulli.cli", "activity")
    history = cli_runner("ghostship_tautulli.cli", "history", "--length", "5")
    users = cli_runner("ghostship_tautulli.cli", "users")
    libraries = cli_runner("ghostship_tautulli.cli", "libraries")
    search = cli_runner("ghostship_tautulli.cli", "search", "office", "--limit", "5")

    for payload in (info, activity, history, users, libraries, search):
        assert_json_payload(payload)

    item = first_item(users)
    user_id = pick_id(item, "user_id", "userId")
    if user_id is not None:
        stats = cli_runner("ghostship_tautulli.cli", "user-stats", str(user_id))
        assert_json_payload(stats)


def test_live_bazarr(cli_runner) -> None:
    info = cli_runner("ghostship_bazarr.cli", "info")
    badges = cli_runner("ghostship_bazarr.cli", "badges")
    wanted_episodes = cli_runner("ghostship_bazarr.cli", "wanted-episodes")
    movies = cli_runner("ghostship_bazarr.cli", "movies")
    wanted_movies = cli_runner("ghostship_bazarr.cli", "wanted-movies")
    series = cli_runner("ghostship_bazarr.cli", "series")
    providers = cli_runner("ghostship_bazarr.cli", "providers")
    health = cli_runner("ghostship_bazarr.cli", "health")
    jobs = cli_runner("ghostship_bazarr.cli", "jobs")
    tasks = cli_runner("ghostship_bazarr.cli", "tasks")
    history = cli_runner("ghostship_bazarr.cli", "history")
    blacklist = cli_runner("ghostship_bazarr.cli", "blacklist")

    for payload in (
        info,
        badges,
        wanted_episodes,
        movies,
        wanted_movies,
        series,
        providers,
        health,
        jobs,
        tasks,
        history,
        blacklist,
    ):
        assert_json_payload(payload)

    series_item = first_item(series)
    series_id = pick_id(series_item, "sonarrSeriesId", "seriesId", "id")
    if series_id is not None:
        episodes = cli_runner("ghostship_bazarr.cli", "episodes", "--series-id", str(series_id))
        assert_json_payload(episodes)


def test_live_synology(cli_runner) -> None:
    shares = cli_runner("ghostship_synology.cli", "list-shares")
    assert_json_payload(shares)

    share = first_item(shares)
    share_path = pick_id(share, "path")
    if share_path is not None:
        info = cli_runner("ghostship_synology.cli", "info", str(share_path))
        files = cli_runner("ghostship_synology.cli", "list-files", str(share_path), "--limit", "10")
        assert_json_payload(info)
        assert_json_payload(files)


def test_live_flaresolverr(cli_runner) -> None:
    try:
        sessions = cli_runner("ghostship_flaresolverr.cli", "list-sessions")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "Name or service not known", "Network is unreachable")
    else:
        assert_json_payload(sessions)


def test_live_pyload_ng(cli_runner) -> None:
    try:
        status = cli_runner("ghostship_pyload_ng.cli", "status")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "401 Unauthorized", "Invalid API credentials")
    else:
        downloads = cli_runner("ghostship_pyload_ng.cli", "downloads")
        queue = cli_runner("ghostship_pyload_ng.cli", "queue")
        accounts = cli_runner("ghostship_pyload_ng.cli", "accounts")
        version = cli_runner("ghostship_pyload_ng.cli", "version")
        freespace = cli_runner("ghostship_pyload_ng.cli", "freespace")

        for payload in (status, downloads, queue, accounts):
            assert_json_payload(payload)
        assert isinstance(version, str), f"expected version string, got {type(version)!r}"
        assert isinstance(freespace, int), f"expected freespace integer, got {type(freespace)!r}"


def test_live_cloakbrowser(cli_runner) -> None:
    status = cli_runner("ghostship_cloakbrowser.cli", "status")
    auth_status = cli_runner("ghostship_cloakbrowser.cli", "auth-status")
    profiles = cli_runner("ghostship_cloakbrowser.cli", "list")

    for payload in (status, auth_status, profiles):
        assert_json_payload(payload)

    item = first_item(profiles)
    profile_id = pick_id(item, "id", "profileId")
    if profile_id is not None:
        detail = cli_runner("ghostship_cloakbrowser.cli", "get", str(profile_id))
        profile_status = cli_runner("ghostship_cloakbrowser.cli", "profile-status", str(profile_id))
        assert_json_payload(detail)
        assert_json_payload(profile_status)

        if isinstance(profile_status, dict) and (
            profile_status.get("status") == "running" or profile_status.get("cdp_url")
        ):
            cdp_info = cli_runner("ghostship_cloakbrowser.cli", "cdp-info", str(profile_id))
            assert_json_payload(cdp_info)


def _select_rss_bridge_candidate(bridge_map: dict[str, Any]) -> tuple[str, str | None, list[str]] | None:
    for bridge_name, bridge_payload in bridge_map.items():
        parameters = bridge_payload.get("parameters") if isinstance(bridge_payload, dict) else None
        if not isinstance(parameters, dict):
            continue
        for context_name, context_params in parameters.items():
            if not isinstance(context_params, dict):
                continue
            params: list[str] = []
            valid = True
            for param_name, param_spec in context_params.items():
                if not isinstance(param_spec, dict):
                    continue
                example = param_spec.get("exampleValue")
                default = param_spec.get("defaultValue")
                required = bool(param_spec.get("required"))
                value = example if example not in (None, "") else default
                if value in (None, ""):
                    if required:
                        valid = False
                        break
                    continue
                params.append(f"{param_name}={value}")
            if valid:
                return bridge_name, None if context_name == "global" else str(context_name), params
    return None


def test_live_rss_bridge(cli_runner) -> None:
    bridges = cli_runner("ghostship_rss_bridge.cli", "list-bridges")
    assert_json_payload(bridges)
    bridge_map = bridges.get("bridges", {}) if isinstance(bridges, dict) else {}
    assert isinstance(bridge_map, dict)
    assert bridge_map

    active = cli_runner("ghostship_rss_bridge.cli", "list-bridges", "--active-only")
    assert_json_payload(active)

    bridge_name = next(iter(bridge_map))
    detail = cli_runner("ghostship_rss_bridge.cli", "describe-bridge", bridge_name)
    contexts = cli_runner("ghostship_rss_bridge.cli", "list-contexts", bridge_name)
    formats = cli_runner("ghostship_rss_bridge.cli", "list-known-formats")

    for payload in (detail, contexts, formats):
        assert_json_payload(payload)

    candidate = _select_rss_bridge_candidate(bridge_map)
    if candidate is not None:
        candidate_bridge, candidate_context, candidate_params = candidate
        build_args = ["build-url", "--bridge", candidate_bridge, "--format", "Atom"]
        display_args = ["display", "--bridge", candidate_bridge, "--format", "Atom"]
        if candidate_context is not None:
            build_args.extend(["--context", candidate_context])
            display_args.extend(["--context", candidate_context])
        for param in candidate_params:
            build_args.extend(["--param", param])
            display_args.extend(["--param", param])

        built = cli_runner("ghostship_rss_bridge.cli", *build_args)
        assert_json_payload(built)
        assert isinstance(built.get("url"), str)

        try:
            displayed = cli_runner("ghostship_rss_bridge.cli", *display_args)
        except AssertionError as exc:
            assert_or_skip_known_live_failure(
                exc,
                "404 Not Found",
                "403 Forbidden",
                "429 Too Many Requests",
                "500 Internal Server Error",
                "503 Service Unavailable",
                "timed out",
                "SSL",
            )
        else:
            assert_json_payload(displayed)
            fetched = cli_runner("ghostship_rss_bridge.cli", "fetch-url", built["url"])
            assert_json_payload(fetched)

    for command in (
        ("find-feed", "https://github.com/openai/openai-python/releases"),
        ("detect", "https://github.com/openai/openai-python/releases"),
    ):
        try:
            payload = cli_runner("ghostship_rss_bridge.cli", *command)
        except AssertionError as exc:
            assert_or_skip_known_live_failure(
                exc,
                "404 Not Found",
                "403 Forbidden",
                "429 Too Many Requests",
                "500 Internal Server Error",
                "503 Service Unavailable",
                "timed out",
            )
        else:
            assert_json_payload(payload)


def test_live_pricebuddy(cli_runner, live_env) -> None:
    if not live_env.get("PRICEBUDDY_TOKEN"):
        pytest.skip("PRICEBUDDY_TOKEN is not configured")

    try:
        whoami = cli_runner("ghostship_pricebuddy.cli", "whoami")
        products = cli_runner("ghostship_pricebuddy.cli", "products", "list")
        product_sources = cli_runner("ghostship_pricebuddy.cli", "product-sources", "list")
        stores = cli_runner("ghostship_pricebuddy.cli", "stores", "list")
        tags = cli_runner("ghostship_pricebuddy.cli", "tags", "list")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "401 Unauthorized", "Unauthenticated", "500 Internal Server Error")
    else:
        for payload in (whoami, products, product_sources, stores, tags):
            assert_json_payload(payload)

        tag_name = f"ghostship-live-test-{int(time.time())}"
        updated_name = f"{tag_name}-updated"
        created_tag_id: int | None = None
        try:
            created = cli_runner("ghostship_pricebuddy.cli", "tags", "create", "--name", tag_name)
            assert_json_payload(created)
            created_tag_id = pick_id(created, "id")
            assert created_tag_id is not None

            detail = cli_runner("ghostship_pricebuddy.cli", "tags", "get", str(created_tag_id))
            assert_json_payload(detail)
            assert detail.get("name") == tag_name

            updated = cli_runner(
                "ghostship_pricebuddy.cli",
                "tags",
                "update",
                str(created_tag_id),
                "--name",
                updated_name,
            )
            assert_json_payload(updated)
            assert updated.get("name") == updated_name

            searched = cli_runner(
                "ghostship_pricebuddy.cli",
                "tags",
                "list",
                "--search",
                updated_name,
            )
            assert_json_payload(searched)
        finally:
            if created_tag_id is not None:
                try:
                    deleted = cli_runner("ghostship_pricebuddy.cli", "tags", "delete", str(created_tag_id))
                except AssertionError:
                    pass
                else:
                    assert_json_payload(deleted)
