#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

runtime_path="$(nix build --no-link --print-out-paths .#ghostship-hermes-runtime)"
skills_path="$(nix build --no-link --print-out-paths .#ghostship-hermes-skills)"
seed_path="$(nix build --no-link --print-out-paths .#ghostship-hermes-workstation-seed)"

runtime_bin="$runtime_path/bin/ghostship-hermes-runtime"
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT

home_dir="$tmp_root/home/hermes"
runtime_dir="$tmp_root/run"
nix_profile="$home_dir/.local/state/nix/profiles/workstation-validation"

mkdir -p "$home_dir" "$runtime_dir"

export HOME="$home_dir"
export HERMES_HOME="$home_dir/.hermes"
export XDG_CONFIG_HOME="$home_dir/.config"
export XDG_DATA_HOME="$home_dir/.local/share"
export XDG_STATE_HOME="$home_dir/.local/state"
export XDG_CACHE_HOME="$home_dir/.cache"
export XDG_RUNTIME_DIR="$runtime_dir"
export GHOSTSHIP_WORKSTATION_SEED="$seed_path"
export GHOSTSHIP_DEFAULT_SKILLS="$skills_path"
export HERMES_UID="$(id -u)"
export HERMES_GID="$(id -g)"

"$runtime_bin" seed-workstation
"$runtime_bin" seed-skills
"$runtime_bin" refresh-opencode-models-once
"$runtime_bin" update-apps-once

nix profile install --accept-flake-config --profile "$nix_profile" nixpkgs#hello >/dev/null
"$nix_profile/bin/hello" >/dev/null

printf '\n# preserved edit\n' >> "$HOME/.agents/AGENTS.md"
printf 'custom workstation state\n' > "$HOME/.hermes/custom-persist.txt"

"$runtime_bin" seed-workstation
"$runtime_bin" seed-skills
"$runtime_bin" refresh-opencode-models-once
"$nix_profile/bin/hello" >/dev/null

tail -n 1 "$HOME/.agents/AGENTS.md" | grep -Fx '# preserved edit' >/dev/null
grep -Fx 'custom workstation state' "$HOME/.hermes/custom-persist.txt" >/dev/null
test -f "$HOME/.local/state/opencode/programming-free-models.json"
test -f "$HOME/.local/state/opencode/programming-free-models.date"
test -x "$HOME/.local/bin/codex"
test -x "$HOME/.local/bin/gemini"
test -x "$HOME/.local/bin/opencode"
test -x "$HOME/.local/bin/openspec"
test -x "$HOME/.local/bin/skills"

for skill_name in brainstorming find-skills using-git-worktrees systematic-debugging; do
  test -f "$HOME/.agents/skills/$skill_name/SKILL.md"
done

for skill_name in current-environment hermes-nix gws-gmail; do
  test -f "$HOME/.hermes/skills/$skill_name/SKILL.md"
done

for unit_name in \
  ghostship-workstation-bootstrap.service \
  ghostship-caddy.service \
  ghostship-profile-reconciler.service \
  ghostship-app-update.timer \
  ghostship-asset-refresh.timer \
  ghostship-opencode-model-refresh.timer
do
  test -L "$HOME/.config/systemd/user/$unit_name"
done

printf 'validated workstation persistence under %s\n' "$tmp_root"
