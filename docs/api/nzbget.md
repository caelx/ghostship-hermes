# NZBGet API Spec Sheet

## Service Identity

- Product: NZBGet
- Base RPC URL: `http(s)://<host>/jsonrpc`
- Protocol: JSON-RPC
- Primary auth: HTTP Basic auth

## Canonical Source Quality

- Official RPC reference
- No mirrored OpenAPI artifact is currently stored in this repo

## Full Method and Use-Case Inventory

The official NZBGet reference for version `13.0` and later documents these JSON-RPC methods:

### Core program control
- `version`: server version
- `status`: current queue and service status
- `reload`: reload configuration
- `shutdown`: stop NZBGet

### Queue and download management
- `append`: add an NZB or URL to the queue
- `listgroups`: list grouped downloads
- `listfiles`: list files in a group
- `editqueue`: mutate queue state, priorities, names, categories, and post-process parameters
- `scan`: rescan incoming or watched directories

### Logging and diagnostics
- `log`: read recent log entries
- `loadlog`: load a range of persisted log messages
- `writelog`: append a log message

### Pause, resume, and throughput control
- `rate`: get or set speed limit
- `pausedownload`: pause downloads
- `resumedownload`: resume downloads
- `pausepost`: pause post-processing
- `resumepost`: resume post-processing
- `pausescan`: pause queue scanning
- `resumescan`: resume queue scanning
- `scheduleresume`: schedule automatic resume

### Configuration and templates
- `loadconfig`: read configuration values
- `saveconfig`: write configuration values
- `configtemplates`: fetch available config templates

### Storage and server volumes
- `servervolumes`: inspect server storage volumes
- `resetservervolume`: reset stored volume information

## Repo Utility Surface

`ghostship-nzbget` currently uses version, shutdown, reload, status, queue, append, editqueue, scan, log, rate, pause/resume, and selected config methods, but the official RPC surface above is broader.

## Notes

- NZBGet uses JSON-RPC request envelopes with positional `params`.
- The repo client automatically appends `/jsonrpc` when the caller supplies only the server base URL.

## Source Material

- Official API reference index: <https://nzbget.net/api/index>
