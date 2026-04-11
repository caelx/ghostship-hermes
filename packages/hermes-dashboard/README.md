# hermes-dashboard

This package ships a HUDUI-aligned browser surface for `ghostship-hermes`.

The packaged artifact contains:
- the Hermes HUDUI-style FastAPI backend
- a compiled React/Vite frontend built during the Nix package build
- Ghostship image compatibility patches for `/home/hermes/.hermes` and `/workspace`
- a `Console` tab backed by on-demand same-origin `ttyd`
