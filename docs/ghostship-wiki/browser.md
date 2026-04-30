# Browser

## Local Lane

Hermes uses the stock local `agent-browser` lane. The image exposes native
CloakBrowser as the standard Linux `google-chrome` binary, so `agent-browser`
discovers it without an executable-path override.

Important env:

- `AGENT_BROWSER_ARGS=--no-sandbox`
- `AGENT_BROWSER_EXTENSIONS=/opt/ghostship/extensions/ublock-origin-lite`
- `DISPLAY=:99`

Xvfb runs as an image-owned service because extension launches may need a headed
Chrome path inside the container.

## Profiles

The raw Chrome wrapper defaults to:

`/home/hermes/.local/state/cloakbrowser`

`agent-browser --session` still controls session isolation. Do not set
`AGENT_BROWSER_PROFILE` image-wide.

## Humanized Actions

The image replaces the packaged `agent-browser` native binary with a repo-built
binary patched in `cli/src/native/interaction.rs`. The patch keeps CDP/local
browser semantics while making actions more CloakBrowser-like:

- multi-step Bezier/wobbled mouse movement before click and hover;
- randomized click target jitter and press-hold-release timing;
- chunked wheel/scroll behavior with pauses;
- form fill/type uses per-character timing;
- shifted symbols route through CDP `Input.dispatchKeyEvent`.

Set `GHOSTSHIP_AGENT_BROWSER_HUMANIZE=0` only for debugging the patch.

## Remote CDP

`/browser connect` is a manual process-global override in Hermes. It is useful
for debugging but not the standard multi-session workflow. The supported default
is the in-container local browser path above.
