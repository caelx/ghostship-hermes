# RSS-Bridge API

- Canonical utility: `ghostship-rss-bridge`
- Raw spec mirror: None
- Source quality: Official docs and source code

## Auth

The standard RSS-Bridge actions documented here do not require a repo-managed token in this project.

- Base URL env: `RSS_BRIDGE_URL`

## Model

RSS-Bridge is action-driven, not CRUD-driven. It does not create persistent server-side feed objects for clients by default.

The operational model is:
1. discover bridges and their parameter schemas
2. choose a bridge/context/format
3. construct a `display` URL with typed parameters
4. hand that URL to an RSS reader or fetch the feed immediately

## Core Actions

### `action=list`

- Request: `GET /?action=list`
- Returns JSON describing every bridge in the instance.
- Important fields per bridge:
  - `status`
  - `uri`
  - `donationUri`
  - `name`
  - `icon`
  - `parameters`
  - `maintainer`
  - `description`

`parameters` is the key contract for automation. Live instances may expose it in either of two compatible shapes:
- a nested map of contexts to parameter definitions
- a legacy list of parameter-group objects that should be treated as the global/default context

Parameter metadata may include:
- `name`
- `type`
- `required`
- `defaultValue`
- `exampleValue`
- `title`
- `pattern`
- `values`

### `action=findfeed`

- Request: `GET /?action=findfeed&url=<target>&format=<Format>`
- Returns discovered feed candidates for a target URL.
- Each result includes:
  - `url`
  - `bridgeParams`
  - `bridgeData`
  - `bridgeMeta`

### `action=detect`

- Request: `GET /?action=detect&url=<target>&format=<Format>`
- Behaves like the frontpage detect flow and typically responds with a redirect target.

### `action=display`

- Request: `GET /?action=display&bridge=<Bridge>&format=<Format>&...bridge params...`
- Generates the actual feed payload.
- This is the canonical “create a feed URL” operation for automation.

## Global Parameters

Depending on instance configuration, bridges may expose global parameters such as:
- `_noproxy`
- `_cache_timeout`

These appear in the `parameters` map and should be treated the same way as bridge-specific parameters.

## Formats

Built-in upstream formats confirmed from source:
- `Atom`
- `Html`
- `Json`
- `Mrss`
- `Plaintext`
- `Sfeed`

Instances may add custom formats. `ghostship-rss-bridge` accepts arbitrary `--format` strings and separately documents the built-in set.

## Utility Coverage

`ghostship-rss-bridge` exposes:
- `list-bridges`
- `describe-bridge`
- `list-contexts`
- `list-known-formats`
- `build-url`
- `find-feed`
- `detect`
- `display`
- `fetch-url`

The utility returns JSON by default even for XML/HTML/plaintext feed responses by wrapping them in a JSON object with metadata and raw body text.

## Sources

- Upstream actions docs: <https://rss-bridge.github.io/rss-bridge/For_Developers/Actions.html>
- Upstream bridge API docs: <https://rss-bridge.github.io/rss-bridge/Bridge_API/index.html>
- Upstream repo: <https://github.com/RSS-Bridge/rss-bridge>
