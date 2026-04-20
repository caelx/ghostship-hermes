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
        "search_web",
        "ghostship hermes",
        "--limit",
        "3",
    )
    assert_json_payload(payload)
    assert "results" in payload
    assert isinstance(payload["results"], list)


def test_live_sonarr(cli_runner) -> None:
    info = cli_runner("ghostship_sonarr.cli", "get_status")
    series = cli_runner("ghostship_sonarr.cli", "get_series")
    try:
        lookup = cli_runner("ghostship_sonarr.cli", "lookup_series", "the office")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "timed out", "ReadTimeout")
        raise
    history = cli_runner("ghostship_sonarr.cli", "get_history", "--page-size", "5")
    queue = cli_runner("ghostship_sonarr.cli", "get_queue")
    missing = cli_runner("ghostship_sonarr.cli", "get_wanted_missing", "--page-size", "5")
    blocklist = cli_runner("ghostship_sonarr.cli", "get_blocklist", "--page-size", "5")
    tags = cli_runner("ghostship_sonarr.cli", "get_tags")
    rootfolders = cli_runner("ghostship_sonarr.cli", "get_root_folders")
    profiles = cli_runner("ghostship_sonarr.cli", "get_quality_profiles")

    for payload in (info, series, lookup, history, queue, missing, blocklist, tags, rootfolders, profiles):
        assert_json_payload(payload)

    item = first_item(series)
    series_id = pick_id(item, "id", "seriesId")
    if series_id is not None:
        detail = cli_runner("ghostship_sonarr.cli", "get_series", "--series-id", str(series_id))
        assert_json_payload(detail)


def test_live_radarr(cli_runner) -> None:
    info = cli_runner("ghostship_radarr.cli", "get_status")
    movies = cli_runner("ghostship_radarr.cli", "get_movies")
    lookup = cli_runner("ghostship_radarr.cli", "lookup_movie", "inception")
    history = cli_runner("ghostship_radarr.cli", "get_history", "--page-size", "5")
    queue = cli_runner("ghostship_radarr.cli", "get_queue")
    missing = cli_runner("ghostship_radarr.cli", "get_wanted_missing", "--page-size", "5")
    blocklist = cli_runner("ghostship_radarr.cli", "get_blocklist", "--page-size", "5")
    tags = cli_runner("ghostship_radarr.cli", "get_tags")
    rootfolders = cli_runner("ghostship_radarr.cli", "get_root_folders")
    profiles = cli_runner("ghostship_radarr.cli", "get_quality_profiles")

    for payload in (info, movies, lookup, history, queue, missing, blocklist, tags, rootfolders, profiles):
        assert_json_payload(payload)

    item = first_item(movies)
    movie_id = pick_id(item, "id", "movieFileId")
    if movie_id is not None:
        detail = cli_runner("ghostship_radarr.cli", "get_movies", "--movie-id", str(movie_id))
        assert_json_payload(detail)


def test_live_prowlarr(cli_runner) -> None:
    info = cli_runner("ghostship_prowlarr.cli", "get_status")
    indexers = cli_runner("ghostship_prowlarr.cli", "get_indexers")
    apps = cli_runner("ghostship_prowlarr.cli", "get_applications")
    stats = cli_runner("ghostship_prowlarr.cli", "get_indexer_stats")
    status = cli_runner("ghostship_prowlarr.cli", "get_indexer_status")
    try:
        search = cli_runner("ghostship_prowlarr.cli", "search", "ubuntu")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "timed out")
    else:
        assert_json_payload(search)

    for payload in (info, indexers, apps, stats, status):
        assert_json_payload(payload)


def test_live_plex(cli_runner) -> None:
    info = cli_runner("ghostship_plex.cli", "get_server_info")
    libraries = cli_runner("ghostship_plex.cli", "get_library_sections")
    sessions = cli_runner("ghostship_plex.cli", "get_status_sessions")
    playlists = cli_runner("ghostship_plex.cli", "get_playlists")
    prefs = cli_runner("ghostship_plex.cli", "get_preferences")
    tasks = cli_runner("ghostship_plex.cli", "get_butler_tasks")

    for payload in (info, libraries, sessions, playlists, prefs, tasks):
        assert_json_payload(payload)

    section = first_item(libraries)
    section_id = pick_id(section, "key", "id")
    if section_id is not None:
        library = cli_runner("ghostship_plex.cli", "get_library_section", str(section_id))
        collections = cli_runner("ghostship_plex.cli", "get_collections", str(section_id))
        assert_json_payload(library)
        assert_json_payload(collections)

        item = first_item(library)
        rating_key = pick_id(item, "ratingKey", "rating_key")
        if rating_key is not None:
            metadata = cli_runner("ghostship_plex.cli", "get_metadata", str(rating_key))
            assert_json_payload(metadata)


def test_live_romm(cli_runner) -> None:
    heartbeat = cli_runner("ghostship_romm.cli", "get_heartbeat")
    config = cli_runner("ghostship_romm.cli", "get_config")

    for payload in (heartbeat, config):
        assert_json_payload(payload)

    optional_reads = [
        ("get_platforms",),
        ("get_collections",),
        ("get_saves", "--page-size", "5"),
        ("get_saves_summary",),
        ("get_users",),
        ("get_user_me",),
        ("get_roms", "--page-size", "5"),
    ]
    for command in optional_reads:
        try:
            payload = cli_runner("ghostship_romm.cli", *command)
        except AssertionError as exc:
            assert_or_skip_known_live_failure(exc, "403 Forbidden", "HTTP 403", "422 Unprocessable Entity")
        else:
            assert_json_payload(payload)
            if command[0] == "get_roms":
                item = first_item(payload)
                rom_id = pick_id(item, "id", "rom_id")
                if rom_id is not None:
                    detail = cli_runner("ghostship_romm.cli", "get_rom", str(rom_id))
                    assert_json_payload(detail)


def test_live_nzbget(cli_runner) -> None:
    info = cli_runner("ghostship_nzbget.cli", "get_status")
    version = cli_runner("ghostship_nzbget.cli", "get_version")
    queue = cli_runner("ghostship_nzbget.cli", "list_groups")
    history = cli_runner("ghostship_nzbget.cli", "get_history")
    config = cli_runner("ghostship_nzbget.cli", "get_config")

    for payload in (info, queue, history, config):
        assert_json_payload(payload)
    assert isinstance(version, dict), f"expected version payload, got {type(version)!r}"
    assert "version" in version

    item = first_item(queue)
    nzb_id = pick_id(item, "NZBID", "NzbID", "ID")
    if nzb_id is not None:
        files = cli_runner("ghostship_nzbget.cli", "list_files", str(nzb_id))
        assert_json_payload(files)


def test_live_qbittorrent(cli_runner) -> None:
    info = cli_runner("ghostship_qbittorrent.cli", "get_transfer_info")
    app_info = cli_runner("ghostship_qbittorrent.cli", "get_app_version")
    prefs = cli_runner("ghostship_qbittorrent.cli", "get_preferences")
    log = cli_runner("ghostship_qbittorrent.cli", "get_log", "--last-known-id", "-1")
    torrents = cli_runner("ghostship_qbittorrent.cli", "get_torrents")
    rss = cli_runner("ghostship_qbittorrent.cli", "get_rss_data")

    for payload in (info, prefs, log, torrents, rss):
        assert_json_payload(payload)
    assert isinstance(app_info, dict), f"expected app version payload, got {type(app_info)!r}"
    assert "version" in app_info


def test_live_grimmory(cli_runner) -> None:
    info = cli_runner("ghostship_grimmory.cli", "get_version")
    books = cli_runner("ghostship_grimmory.cli", "get_books")
    libraries = cli_runner("ghostship_grimmory.cli", "get_libraries")
    authors = cli_runner("ghostship_grimmory.cli", "get_authors")
    shelves = cli_runner("ghostship_grimmory.cli", "get_shelves")
    tasks = cli_runner("ghostship_grimmory.cli", "get_tasks")

    for payload in (info, books, libraries, authors, shelves, tasks):
        assert_json_payload(payload)

    item = first_item(books)
    book_id = pick_id(item, "id", "bookId")
    if book_id is not None:
        detail = cli_runner("ghostship_grimmory.cli", "get_book", str(book_id))
        assert_json_payload(detail)


def test_live_tautulli(cli_runner) -> None:
    info = cli_runner("ghostship_tautulli.cli", "get_tautulli_info")
    activity = cli_runner("ghostship_tautulli.cli", "get_activity")
    history = cli_runner("ghostship_tautulli.cli", "get_history", "--length", "5")
    users = cli_runner("ghostship_tautulli.cli", "get_users")
    libraries = cli_runner("ghostship_tautulli.cli", "get_libraries")
    search = cli_runner("ghostship_tautulli.cli", "search", "office", "--limit", "5")

    for payload in (info, activity, history, users, libraries, search):
        assert_json_payload(payload)

    item = first_item(users)
    user_id = pick_id(item, "user_id", "userId")
    if user_id is not None:
        stats = cli_runner("ghostship_tautulli.cli", "get_user_player_stats", str(user_id))
        assert_json_payload(stats)


def test_live_bazarr(cli_runner) -> None:
    info = cli_runner("ghostship_bazarr.cli", "get_system_status")
    badges = cli_runner("ghostship_bazarr.cli", "get_badges")
    wanted_episodes = cli_runner("ghostship_bazarr.cli", "get_wanted_episodes")
    movies = cli_runner("ghostship_bazarr.cli", "get_movies")
    wanted_movies = cli_runner("ghostship_bazarr.cli", "get_wanted_movies")
    series = cli_runner("ghostship_bazarr.cli", "get_series")
    providers = cli_runner("ghostship_bazarr.cli", "get_providers")
    health = cli_runner("ghostship_bazarr.cli", "get_system_health")
    jobs = cli_runner("ghostship_bazarr.cli", "get_system_jobs")
    tasks = cli_runner("ghostship_bazarr.cli", "get_system_tasks")
    history = cli_runner("ghostship_bazarr.cli", "get_episodes_history")
    blacklist = cli_runner("ghostship_bazarr.cli", "get_episodes_blacklist")

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
        episodes = cli_runner("ghostship_bazarr.cli", "get_episodes", "--series-id", str(series_id))
        assert_json_payload(episodes)


def test_live_synology(cli_runner) -> None:
    shares = cli_runner("ghostship_synology.cli", "list_shares")
    assert_json_payload(shares)

    share = first_item(shares)
    share_path = pick_id(share, "path")
    if share_path is not None:
        info = cli_runner("ghostship_synology.cli", "get_file_info", str(share_path))
        files = cli_runner("ghostship_synology.cli", "list_files", str(share_path), "--limit", "10")
        assert_json_payload(info)
        assert_json_payload(files)


def test_live_flaresolverr(cli_runner) -> None:
    try:
        sessions = cli_runner("ghostship_flaresolverr.cli", "sessions_list")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "Name or service not known", "Network is unreachable")
    else:
        assert_json_payload(sessions)


def test_live_pyload_ng(cli_runner) -> None:
    try:
        status = cli_runner("ghostship_pyload_ng.cli", "get_server_status")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "401 Unauthorized", "Invalid API credentials")
    else:
        downloads = cli_runner("ghostship_pyload_ng.cli", "get_downloads")
        queue = cli_runner("ghostship_pyload_ng.cli", "get_queue")
        accounts = cli_runner("ghostship_pyload_ng.cli", "get_accounts")
        version = cli_runner("ghostship_pyload_ng.cli", "get_server_version")
        freespace = cli_runner("ghostship_pyload_ng.cli", "get_free_space")

        for payload in (status, downloads, queue, accounts):
            assert_json_payload(payload)
        assert isinstance(version, str), f"expected version string, got {type(version)!r}"
        assert isinstance(freespace, int), f"expected freespace integer, got {type(freespace)!r}"


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
    bridges = cli_runner("ghostship_rss_bridge.cli", "list_bridges")
    assert_json_payload(bridges)
    bridge_map = bridges.get("bridges", {}) if isinstance(bridges, dict) else {}
    assert isinstance(bridge_map, dict)
    assert bridge_map

    active = cli_runner("ghostship_rss_bridge.cli", "list_bridges", "--active-only")
    assert_json_payload(active)

    bridge_name = next(iter(bridge_map))
    detail = cli_runner("ghostship_rss_bridge.cli", "describe_bridge", bridge_name)
    contexts = cli_runner("ghostship_rss_bridge.cli", "list_contexts", bridge_name)
    formats = cli_runner("ghostship_rss_bridge.cli", "list_known_formats")

    for payload in (detail, contexts, formats):
        assert_json_payload(payload)

    candidate = _select_rss_bridge_candidate(bridge_map)
    if candidate is not None:
        candidate_bridge, candidate_context, candidate_params = candidate
        build_args = ["build_url", "--bridge", candidate_bridge, "--format", "Atom"]
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
            fetched = cli_runner("ghostship_rss_bridge.cli", "fetch_url", built["url"])
            assert_json_payload(fetched)

    for command in (
        ("find_feed", "https://github.com/openai/openai-python/releases"),
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
        whoami = cli_runner("ghostship_pricebuddy.cli", "get_current_user")
        products = cli_runner("ghostship_pricebuddy.cli", "list_products")
        product_sources = cli_runner("ghostship_pricebuddy.cli", "list_product_sources")
        stores = cli_runner("ghostship_pricebuddy.cli", "list_stores")
        tags = cli_runner("ghostship_pricebuddy.cli", "list_tags")
    except AssertionError as exc:
        assert_or_skip_known_live_failure(exc, "401 Unauthorized", "Unauthenticated", "500 Internal Server Error")
    else:
        for payload in (whoami, products, product_sources, stores, tags):
            assert_json_payload(payload)

        tag_name = f"ghostship-live-test-{int(time.time())}"
        updated_name = f"{tag_name}-updated"
        created_tag_id: int | None = None
        try:
            created = cli_runner("ghostship_pricebuddy.cli", "create_tag", "--name", tag_name)
            assert_json_payload(created)
            created_tag_id = pick_id(created, "id")
            assert created_tag_id is not None

            detail = cli_runner("ghostship_pricebuddy.cli", "get_tag", str(created_tag_id))
            assert_json_payload(detail)
            assert detail.get("name") == tag_name

            updated = cli_runner(
                "ghostship_pricebuddy.cli",
                "update_tag",
                str(created_tag_id),
                "--name",
                updated_name,
            )
            assert_json_payload(updated)
            assert updated.get("name") == updated_name

            searched = cli_runner(
                "ghostship_pricebuddy.cli",
                "list_tags",
                "--search",
                updated_name,
            )
            assert_json_payload(searched)
        finally:
            if created_tag_id is not None:
                try:
                    deleted = cli_runner("ghostship_pricebuddy.cli", "delete_tag", str(created_tag_id))
                except AssertionError:
                    pass
                else:
                    assert_json_payload(deleted)
