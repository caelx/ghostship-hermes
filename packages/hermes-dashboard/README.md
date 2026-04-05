# hermes-dashboard

Packaged MMX dashboard for `ghostship-hermes`.

It serves the bundled MMX frontend, reports dashboard status over FastAPI, and proxies on-demand `ttyd` terminals from the same origin used by the Hermes container dashboard.

Build it directly with:

```fish
nix build .#packages.x86_64-linux.hermes-dashboard
```

The runtime entrypoint is:

```fish
hermes-dashboard
```
