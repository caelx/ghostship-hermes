# hermes-dashboard

Packaged Hermes-tailored dashboard for `ghostship-hermes`.

It serves the bundled Hermes shell frontend, reports dashboard status over FastAPI, and proxies on-demand `ttyd` terminals from the same origin used by the Hermes container dashboard.

Build it directly with:

```fish
nix build .#packages.x86_64-linux.hermes-dashboard
```

The runtime entrypoint is:

```fish
hermes-dashboard
```

The home view is an environment console for the current runtime: the managed single-agent surface, provider metadata, and Hermes paths.
