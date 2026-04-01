---
name: agent-browser
description: Use agent-browser with CloakBrowser-launched profiles and CDP endpoints inside the Hermes container.
---

# Hermes Agent Browser Skill

Use this skill when Hermes needs browser automation through CloakBrowser profiles. Do not treat local Chrome/CDP or ad hoc browser launches as the supported path here.

## Core Rules

- Use `ghostship-cloakbrowser` to inspect, create, launch, and stop profiles.
- There are two default profiles available initially.
- More profiles can be created as needed.
- One default profile routes through a VPN and is useful for more anonymous calls, but it is more likely to trigger CAPTCHA or bot defenses.
- Use the non-VPN profile when reliability matters more than anonymity.
- Connect `agent-browser` only to the CDP endpoint exposed by a launched CloakBrowser profile.
- Always verify state after each browser action.
- If you need a different identity or routing pattern, create or launch the correct CloakBrowser profile first, then connect `agent-browser`.

## Workflow

1. List profiles with `ghostship-cloakbrowser list_profiles`.
2. Launch the chosen profile.
3. Copy the returned CDP URL.
4. Connect `agent-browser` to that URL.
5. Use snapshots/refs for interaction.
6. Re-check the page after each mutation.

## Profile Strategy

- Start with the non-VPN default profile for most research and account-based work.
- Switch to the VPN-backed default profile when you need a less-attributed request path and can tolerate more anti-bot friction.
- Create a new profile when a task needs its own cookies, login state, or browser fingerprint.
- Do not reuse a profile that already contains unrelated authenticated state if the task should remain isolated.

## Common Commands

- `ghostship-cloakbrowser auth_status`
- `ghostship-cloakbrowser list_profiles`
- `ghostship-cloakbrowser launch_profile <profile-id>`
- `ghostship-cloakbrowser get_profile_status <profile-id>`
- `ghostship-cloakbrowser stop_profile <profile-id>`
- `agent-browser snapshot -i`
- `agent-browser click @e1`
- `agent-browser fill @e2 "text"`
- `agent-browser press Enter`
- `agent-browser screenshot --annotate`

## Session Hygiene

- Verify the launched profile before connecting.
- Use `agent-browser snapshot -i` after every meaningful click, form fill, or navigation.
- Prefer refs from the latest snapshot rather than guessing selectors.
- Stop the profile when the task is complete if it should not remain running.

## Connection Notes

- Prefer the full CDP URL from CloakBrowser.
- If the returned URL is relative, prefix it with the manager host before connecting.
- Do not assume direct browser access if no profile has been launched.
- This skill is only for CloakBrowser-backed profiles. If no CloakBrowser profile is available, treat browser automation as unavailable until one is created and launched.
