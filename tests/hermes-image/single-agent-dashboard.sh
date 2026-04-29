#!/usr/bin/env bash
set -Eeuo pipefail

image_ref="${1:?usage: single-agent-dashboard.sh <image-ref>}"
container_name="ghostship-hermes-dashboard-test"
dashboard_port="${GHOSTSHIP_TEST_DASHBOARD_PORT:-}"
tmp_root="$(mktemp -d)"
home_dir="$tmp_root/home"
workspace_dir="$tmp_root/workspace"
nix_dir="$tmp_root/nix"
host_uid="$(id -u)"
host_gid="$(id -g)"

container_engine="${CONTAINER_ENGINE:-}"
if [ -z "$container_engine" ]; then
  if command -v docker >/dev/null 2>&1; then
    container_engine="docker"
  elif command -v podman >/dev/null 2>&1; then
    container_engine="podman"
  else
    echo "docker or podman is required for image testing" >&2
    exit 1
  fi
fi

cleanup() {
  "$container_engine" rm -f "$container_name" >/dev/null 2>&1 || true
  if "$container_engine" image inspect "$image_ref" >/dev/null 2>&1; then
    "$container_engine" run --rm --entrypoint /bin/sh -u 0:0 -v "$tmp_root:/cleanup" "$image_ref" -lc '
      chown -R '"$host_uid:$host_gid"' /cleanup >/dev/null 2>&1 || true
      chmod -R u+w /cleanup >/dev/null 2>&1 || true
    ' >/dev/null 2>&1 || true
  fi
  rm -rf "$tmp_root" >/dev/null 2>&1 || true
}
trap cleanup EXIT

dump_failure_state() {
  local exit_code="$1"
  local failed_line="${2:-unknown}"
  local failed_command="${3:-unknown}"
  if [ "$exit_code" -eq 0 ]; then
    return
  fi
  echo "failed at line ${failed_line}: ${failed_command}" >&2
  if ! "$container_engine" ps -a --format '{{.Names}}' | grep -Fx "$container_name" >/dev/null 2>&1; then
    return
  fi

  echo "===== container logs: $container_name =====" >&2
  "$container_engine" logs "$container_name" >&2 || true

  echo "===== browser profile tree =====" >&2
  "$container_engine" exec "$container_name" /bin/sh -lc "find /home/hermes/.local/state/cloakbrowser -maxdepth 4 -printf '%u:%g %y %p -> %l\\n' 2>/dev/null | sed -n '1,120p'" >&2 || true
  echo >&2

  echo "===== non-hermes owned paths =====" >&2
  "$container_engine" exec "$container_name" /bin/sh -lc "find /home/hermes \\! -user hermes -printf '%u:%g %y %p -> %l\\n' | sed -n '1,80p'" >&2 || true
  echo >&2
}
trap 'status=$?; failed_line=$LINENO; failed_command=$BASH_COMMAND; dump_failure_state "$status" "$failed_line" "$failed_command"' ERR

wait_for_http() {
  local url="$1"
  local attempts="${2:-90}"
  local delay="${3:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

wait_for_container_http() {
  local target_container="$1"
  local url="$2"
  local attempts="${3:-90}"
  local delay="${4:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if "$container_engine" exec "$target_container" /bin/sh -lc "curl -fsS \"$url\" >/dev/null" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

wait_for_hermes_shell() {
  local target_container="$1"
  local command="$2"
  local attempts="${3:-90}"
  local delay="${4:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if run_as_hermes "$target_container" "$command" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

run_in_container() {
  local target_container="$1"
  shift
  "$container_engine" exec "$target_container" /bin/sh -lc "$*"
}

run_as_hermes() {
  local target_container="$1"
  shift
  "$container_engine" exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env BITWARDENCLI_APPDATA_DIR=/home/hermes/.local/state/bitwarden-cli --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults --env PATH=/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin "$target_container" /bin/sh -lc "$*"
}

run_browser_profile_probe() {
  local target_container="$1"
  local mode="$2"

  "$container_engine" exec -i --user 3000:3000 \
    --env HOME=/home/hermes \
    --env HERMES_HOME=/home/hermes/.hermes \
    --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults \
    --env PATH=/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    "$target_container" /usr/bin/timeout 90s /opt/cloakbrowser-venv/bin/python - "$mode" <<'PY'
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

mode = sys.argv[1]
profile_root = Path("/home/hermes/.local/state/cloakbrowser")
profile_root.mkdir(parents=True, exist_ok=True)

with sync_playwright() as playwright:
    context = playwright.chromium.launch_persistent_context(
        str(profile_root),
        executable_path="/usr/local/bin/google-chrome",
        headless=True,
        args=["--disable-dev-shm-usage", "--no-sandbox"],
    )
    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("http://127.0.0.1:7681/terminal/", wait_until="domcontentloaded", timeout=30_000)
        if mode == "write":
            page.evaluate("localStorage.setItem('ghostship-smoke', 'warm')")
        value = page.evaluate("localStorage.getItem('ghostship-smoke')")
        assert value == "warm", value
    finally:
        context.close()
PY
}

run_browser_adblock_probe() {
  local target_container="$1"

  "$container_engine" exec -i --user 3000:3000 \
    --env HOME=/home/hermes \
    --env HERMES_HOME=/home/hermes/.hermes \
    --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults \
    --env PATH=/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    "$target_container" /usr/bin/timeout 180s /opt/cloakbrowser-venv/bin/python - <<'PY'
from pathlib import Path
import shutil
import time

from playwright.sync_api import sync_playwright

extension_id = "ddkjiahejlhfcafbddmgiahcphecmpfh"
profile_root = Path("/home/hermes/.local/state/cloakbrowser")
control_profile = Path("/tmp/ghostship-cloakbrowser-control")
ad_test_url = "https://canyoublockit.com/extreme-test/"
ad_probe_urls = [
    "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js",
    "https://securepubads.g.doubleclick.net/tag/js/gpt.js",
    "https://www.googletagservices.com/tag/js/gpt.js",
    "https://googleads.g.doubleclick.net/pagead/id",
]
policy_names = [
    "ExtensionSettings",
    "DefaultNotificationsSetting",
    "DefaultGeolocationSetting",
    "DefaultPopupsSetting",
    "DefaultClipboardSetting",
    "DefaultSensorsSetting",
    "DefaultAutomaticDownloadsSetting",
    "AudioCaptureAllowed",
    "VideoCaptureAllowed",
    "ScreenCaptureAllowed",
    "DefaultSerialGuardSetting",
    "DefaultWebUsbGuardSetting",
    "DefaultWebBluetoothGuardSetting",
    "DefaultWebHidGuardSetting",
    "AutoplayAllowed",
    "FullscreenAllowed",
    "EnableMediaRouter",
    "BackgroundModeEnabled",
    "PromotionalTabsEnabled",
    "PaymentMethodQueryEnabled",
]
ad_markers = (
    "pagead2.googlesyndication.com",
    "securepubads.g.doubleclick.net",
    "googletagservices.com",
    "googleads.g.doubleclick.net",
    "doubleclick.net",
    "googlesyndication.com",
)


def extension_path(root: Path) -> Path:
    return root / "Default" / "Extensions" / extension_id


def launch(playwright, root: Path, extra_args=None):
    root.mkdir(parents=True, exist_ok=True)
    args = ["--disable-dev-shm-usage", "--no-sandbox"]
    if extra_args:
        args.extend(extra_args)
    return playwright.chromium.launch_persistent_context(
        str(root),
        executable_path="/usr/local/bin/google-chrome",
        headless=True,
        args=args,
    )


def assert_policy_visible(page):
    page.goto("chrome://policy/", wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_function(
        "() => document.body && document.body.innerText.includes('ExtensionSettings')",
        timeout=15_000,
    )
    text = page.locator("body").inner_text(timeout=5_000)
    missing = [name for name in policy_names if name not in text]
    assert not missing, f"managed policies missing from chrome://policy: {missing}"
    assert extension_id in text, "uBlock Origin Lite extension id missing from chrome://policy"


def wait_for_extension_install(playwright):
    deadline = time.monotonic() + 90
    last_error = None
    while time.monotonic() < deadline:
        context = launch(playwright, profile_root)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            try:
                assert_policy_visible(page)
            except Exception as exc:  # chrome://policy can lag on the first launch.
                last_error = exc
            page.goto("https://example.com/", wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(2_000)
        finally:
            context.close()
        if extension_path(profile_root).is_dir():
            return
        time.sleep(2)
    raise AssertionError(f"{extension_id} was not installed by managed policy; last policy error: {last_error}")


def browse_and_probe(playwright, root: Path, extra_args=None):
    blocked = []
    failed = []
    requested = []
    context = launch(playwright, root, extra_args=extra_args)
    try:
        page = context.pages[0] if context.pages else context.new_page()

        def is_ad_url(url: str) -> bool:
            return any(marker in url for marker in ad_markers)

        def on_request(request):
            if is_ad_url(request.url):
                requested.append(request.url)

        def on_request_failed(request):
            if not is_ad_url(request.url):
                return
            failure = request.failure or ""
            failed.append((request.url, failure))
            if "ERR_BLOCKED_BY_CLIENT" in failure:
                blocked.append(request.url)

        page.on("request", on_request)
        page.on("requestfailed", on_request_failed)
        page.goto(ad_test_url, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(5_000)
        page.evaluate(
            """async urls => {
                await Promise.all(urls.map(url => new Promise(resolve => {
                    const script = document.createElement('script');
                    script.src = `${url}${url.includes('?') ? '&' : '?'}ghostshipSmoke=${Date.now()}`;
                    script.onload = () => resolve();
                    script.onerror = () => resolve();
                    document.head.appendChild(script);
                    setTimeout(resolve, 6000);
                })));
            }""",
            ad_probe_urls,
        )
        page.wait_for_timeout(3_000)
    finally:
        context.close()
    return requested, failed, blocked


profile_root.mkdir(parents=True, exist_ok=True)
if control_profile.exists():
    shutil.rmtree(control_profile)

with sync_playwright() as playwright:
    wait_for_extension_install(playwright)

    managed_context = launch(playwright, profile_root)
    try:
        policy_page = managed_context.pages[0] if managed_context.pages else managed_context.new_page()
        assert_policy_visible(policy_page)
    finally:
        managed_context.close()

    requested, failed, blocked = browse_and_probe(playwright, profile_root)
    control_requested, control_failed, control_blocked = browse_and_probe(
        playwright,
        control_profile,
        extra_args=["--disable-extensions"],
    )

assert requested, "ad test page/probe made no recognized ad-network requests"
assert control_requested, "extension-disabled control made no recognized ad-network requests"
assert len(set(blocked)) >= 2, {
    "requested": requested,
    "failed": failed,
    "blocked": blocked,
}
assert not control_blocked, {
    "control_requested": control_requested,
    "control_failed": control_failed,
    "control_blocked": control_blocked,
}
PY
}

run_test_container() {
  local publish_arg=""
  if [ -n "${1:-}" ]; then
    publish_arg="${1:?missing host port}:7681"
    shift
  else
    shift || true
    publish_arg="127.0.0.1::7681"
  fi
  "$container_engine" run -d \
    --name "$container_name" \
    --publish "$publish_arg" \
    --volume "$home_dir:/home/hermes" \
    --volume "$workspace_dir:/workspace" \
    --volume "$nix_dir:/nix" \
    --env OPENROUTER_API_KEY=test-openrouter \
    --env OPENCODE_GO_API_KEY=test-opencode \
    --env GOOGLE_AI_STUDIO_API_KEY=test-google \
    --env DISCORD_ALLOWED_USERS=test-user \
    --env DISCORD_HOME_CHANNEL=assistant-channel \
    --env DISCORD_FREE_RESPONSE_CHANNELS=foodstamps-channel \
    --env GHOSTSHIP_CODEX_CHANNEL=foodstamps-channel \
    --env DISCORD_WEBHOOK_CHANNEL=webhooks-channel \
    --env FIRECRAWL_API_KEY=test-firecrawl \
    --env GHOSTSHIP_ROUTER_PORT=9999 \
    --env WEBHOOK_SECRET=test-webhook-secret \
    "$image_ref" "$@"
}

container_host_port() {
  "$container_engine" port "$container_name" 7681/tcp | sed -n 's/.*:\([0-9][0-9]*\)$/\1/p' | head -n1
}

start_test_container_with_retry() {
  local target_port="${1-}"
  local create_output=""
  local attempts=1

  if [ -z "$target_port" ]; then
    attempts=5
  fi

  for _ in $(seq 1 "$attempts"); do
    if create_output="$(run_test_container "$target_port" 2>&1)"; then
      return 0
    fi
    "$container_engine" rm -f "$container_name" >/dev/null 2>&1 || true
    if ! grep -F "Address already in use" <<<"$create_output" >/dev/null 2>&1; then
      printf '%s\n' "$create_output" >&2
      return 1
    fi
    sleep 1
  done

  printf '%s\n' "$create_output" >&2
  return 1
}

smoke_note() {
  printf '== smoke: %s ==\n' "$1" >&2
}

mkdir -p "$home_dir" "$workspace_dir" "$nix_dir"
mkdir -p "$home_dir/.hermes/skills/custom"
cat >"$home_dir/.hermes/skills/custom/SKILL.md" <<'EOF'
# Custom Skill

Custom downstream skill should survive image seeding.
EOF
cat >"$home_dir/.hermes/.env" <<'EOF'
CUSTOM_DOWNSTREAM_KEY=keep-me
FIRECRAWL_API_KEY=stale-firecrawl
STALE_ONLY_KEY=keep-me-too
EOF
cat >"$home_dir/.hermes/.ghostship-managed-env.keys" <<'EOF'
FIRECRAWL_API_KEY
REMOVED_MANAGED_KEY
EOF

"$container_engine" rm -f "$container_name" >/dev/null 2>&1 || true
start_test_container_with_retry "$dashboard_port"
[ -n "$dashboard_port" ] || dashboard_port="$(container_host_port)"

wait_for_http "http://127.0.0.1:${dashboard_port}/api/status"
wait_for_http "http://127.0.0.1:${dashboard_port}/terminal/"
wait_for_container_http "$container_name" "http://127.0.0.1:8788/readyz"

status_json="$(curl -fsS "http://127.0.0.1:${dashboard_port}/api/status")"
# Upstream Hermes does not guarantee that gateway_state is populated on the
# first healthy dashboard response.
printf '%s' "$status_json" | python3 -c 'import json, sys; data = json.load(sys.stdin); assert data["hermes_home"] == "/home/hermes/.hermes"; assert "gateway_state" in data'

run_in_container "$container_name" 'python3 -c '\''import json, urllib.request; data = json.load(urllib.request.urlopen("http://127.0.0.1:8788/readyz")); assert data["ok"] is True'\'''
curl -fsSI "http://127.0.0.1:${dashboard_port}/terminal/" >/dev/null
bundle="$(curl -fsS "http://127.0.0.1:${dashboard_port}/" | sed -n 's/.*src=\"\([^\"]*index-[^\"]*\.js\)\".*/\1/p' | head -n1)"
curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q '/terminal/'
curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q 'sandbox:"allow-same-origin allow-scripts allow-forms"'
! curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q 'allow-modals'
! curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q 'href:"/terminal/",target:"_blank"'

run_in_container "$container_name" '. /run/ghostship/hermes.env; [ "${FIRECRAWL_API_KEY:-}" = test-firecrawl ]'
run_in_container "$container_name" '. /run/ghostship/hermes.env; [ "${DISCORD_WEBHOOK_CHANNEL:-}" = webhooks-channel ]'
run_in_container "$container_name" "! grep -q '^GHOSTSHIP_ROUTER_PORT=' /run/ghostship/hermes.env"
run_in_container "$container_name" '. /home/hermes/.hermes/.env; [ "${FIRECRAWL_API_KEY:-}" = test-firecrawl ]'
run_in_container "$container_name" '. /home/hermes/.hermes/.env; [ "${DISCORD_WEBHOOK_CHANNEL:-}" = webhooks-channel ]'
run_in_container "$container_name" "grep -Fx 'CUSTOM_DOWNSTREAM_KEY=keep-me' /home/hermes/.hermes/.env >/dev/null"
run_in_container "$container_name" "grep -Fx 'STALE_ONLY_KEY=keep-me-too' /home/hermes/.hermes/.env >/dev/null"
run_in_container "$container_name" "! grep -q '^FIRECRAWL_API_KEY=stale-firecrawl$' /home/hermes/.hermes/.env"
run_in_container "$container_name" "! grep -q '^REMOVED_MANAGED_KEY=' /home/hermes/.hermes/.env"
run_in_container "$container_name" "! grep -q '^GHOSTSHIP_ROUTER_PORT=' /home/hermes/.hermes/.env"
run_in_container "$container_name" "grep -Fx 'FIRECRAWL_API_KEY' /home/hermes/.hermes/.ghostship-managed-env.keys >/dev/null"
run_in_container "$container_name" "stat -c '%U:%G %a' /home/hermes/.hermes/.env | grep -Fx 'hermes:hermes 600' >/dev/null"
run_in_container "$container_name" "stat -c '%U:%G %a' /home/hermes/.hermes/.ghostship-managed-env.keys | grep -Fx 'hermes:hermes 600' >/dev/null"
run_as_hermes "$container_name" '
gateway_pid="$(ps -u hermes -o pid=,args= | awk "/hermes gateway run --replace/ { print \$1; exit }")"
if [ -z "$gateway_pid" ]; then
  ps -u hermes -o pid=,args= >&2
  exit 1
fi
gateway_env="$(tr "\0" "\n" </proc/"$gateway_pid"/environ)"
printf "%s\n" "$gateway_env" | grep -Fx "FIRECRAWL_API_KEY=test-firecrawl" >/dev/null || {
  printf "%s\n" "$gateway_env" >&2
  exit 1
}
! printf "%s\n" "$gateway_env" | grep -q "^GHOSTSHIP_ROUTER_PORT="
'

run_in_container "$container_name" '
	for cmd in \
	  nix git rg ttyd tmux tirith jq fd yq uv gh gws bw gcloud blogwatcher-cli \
	  codex gemini agent-browser opencode \
	  ghostship-hermes-router
do
  command -v "$cmd" >/dev/null || { echo "missing command: $cmd" >&2; exit 1; }
done
'
	run_as_hermes "$container_name" 'for cmd in bw gws gh gcloud blogwatcher-cli; do command -v "$cmd" >/dev/null || exit 1; done'
	run_as_hermes "$container_name" 'bw --help >/dev/null'
run_as_hermes "$container_name" 'test -d /home/hermes/.local/state/bitwarden-cli'
run_as_hermes "$container_name" '! test -e "/home/hermes/.config/Bitwarden CLI"'
run_in_container "$container_name" 'test -d /run/user/3000'
run_in_container "$container_name" "grep -E \"^BITWARDENCLI_APPDATA_DIR='?/home/hermes/.local/state/bitwarden-cli'?$\" /home/hermes/.hermes/.env >/dev/null"
run_in_container "$container_name" "! grep -Eq '^(BW_CLIENTSECRET|BW_PASSWORD|BW_SESSION)=' /home/hermes/.hermes/.env"
run_as_hermes "$container_name" 'gws --help >/dev/null'
run_as_hermes "$container_name" 'gh --help >/dev/null'
run_as_hermes "$container_name" 'gcloud --help >/dev/null'
run_as_hermes "$container_name" 'blogwatcher-cli --help >/dev/null'
smoke_note "native browser persistence"
run_browser_profile_probe "$container_name" write
run_in_container "$container_name" 'test -d /home/hermes/.local/state/cloakbrowser'
run_in_container "$container_name" 'command -v google-chrome >/dev/null'
run_in_container "$container_name" 'test -f /etc/opt/chrome/policies/managed/ghostship-agent-browser.json'
run_in_container "$container_name" 'test -f /etc/chromium/policies/managed/ghostship-agent-browser.json'
smoke_note "native browser ad blocking"
run_browser_adblock_probe "$container_name"
smoke_note "home ownership"
run_in_container "$container_name" 'test -z "$(find /home/hermes \! -user hermes -print -quit)"'
smoke_note "memory plugin import"
run_as_hermes "$container_name" '/opt/hermes/venv/bin/python -c "import plugins.memory.holographic"'
smoke_note "gateway status"
run_as_hermes "$container_name" '/opt/hermes/venv/bin/hermes gateway status >/tmp/gateway-status.txt && cat /tmp/gateway-status.txt'
smoke_note "config assertions"
run_as_hermes "$container_name" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: custom:ghostship-router" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  default: deepseek-v4-pro" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^web:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  backend: firecrawl" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: custom:ghostship-router" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  model: minimax-m2.7" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^agent:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  reasoning_effort: high" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^agent:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  max_turns: 500" >/dev/null'
run_as_hermes "$container_name" '/opt/hermes/venv/bin/python - <<'\''PY'\''
import yaml
from pathlib import Path

config = yaml.safe_load(Path("/home/hermes/.hermes/config.yaml").read_text(encoding="utf-8"))
providers = config.get("custom_providers") or []
router = next((entry for entry in providers if entry.get("name") == "ghostship-router"), None)
assert router is not None
assert router.get("model") == "deepseek-v4-pro"
assert sorted((router.get("models") or {}).keys()) == ["deepseek-v4-pro", "minimax-m2.7"]
assert router.get("base_url") == "http://127.0.0.1:8788/v1"
PY'
run_as_hermes "$container_name" '/opt/hermes/venv/bin/python - <<'\''PY'\''
import inspect
from pathlib import Path
import gateway.run

source_path = Path(inspect.getsourcefile(gateway.run))
text = source_path.read_text(encoding="utf-8")
assert "\"model\": \"gpt-5.5\"" in text
assert "openai-codex (`gpt-5.5`)" in text
PY'
run_as_hermes "$container_name" 'sed -n "/^memory:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: holographic" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^plugins:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    db_path: \$HERMES_HOME/memory_store.db" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^auxiliary:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    model: gemini-2.5-flash-lite" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^auxiliary:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    base_url: https://generativelanguage.googleapis.com/v1beta/openai/" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^auxiliary:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    api_key: \${GOOGLE_AI_STUDIO_API_KEY}" >/dev/null'
run_as_hermes "$container_name" 'grep -F "group_sessions_per_user: true" /home/hermes/.hermes/config.yaml >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^terminal:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  timeout: 180" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^browser:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  cloud_provider: local" >/dev/null'
run_as_hermes "$container_name" '! sed -n "/^browser:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "camofox" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^discord:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  require_mention: false" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^discord:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  reactions: false" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^discord:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  auto_thread: true" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^session_reset:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  mode: daily" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^session_reset:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  at_hour: 4" >/dev/null'
run_as_hermes "$container_name" 'grep -F "unauthorized_dm_behavior: ignore" /home/hermes/.hermes/config.yaml >/dev/null'
run_in_container "$container_name" 'test -f /home/hermes/.hermes/skills/custom/SKILL.md'
run_in_container "$container_name" 'test -f /home/hermes/.hermes/skills/autonomous-ai-agents/codex/SKILL.md'

smoke_note "doctor"
doctor_output="$(run_as_hermes "$container_name" '/opt/hermes/venv/bin/hermes doctor' || true)"
grep -q '✓ git' <<<"$doctor_output"
grep -q '✓ ripgrep' <<<"$doctor_output"
grep -q '✓ codex CLI' <<<"$doctor_output"
grep -q '✓ ~/.hermes/skills/ exists' <<<"$doctor_output"

smoke_note "tmux theme"
run_as_hermes "$container_name" 'tmux kill-session -t themecheck >/dev/null 2>&1 || true; tmux new-session -d -s themecheck sleep 600; tmux show -gv status-style | grep -Fx "bg=#041C1C,fg=#FFE6CB"; tmux show -gv pane-active-border-style | grep -Fx "fg=#67E8F9"'

smoke_note "persistence warmup"
run_in_container "$container_name" 'printf smoke-home > /home/hermes/persist-home.txt && printf smoke-workspace > /workspace/persist-workspace.txt && chown hermes:hermes /home/hermes/persist-home.txt /workspace/persist-workspace.txt'
run_as_hermes "$container_name" "nix --extra-experimental-features 'nix-command flakes' profile add nixpkgs#hello"
run_as_hermes "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'

"$container_engine" restart "$container_name" >/dev/null
smoke_note "post-restart dashboard"
wait_for_container_http "$container_name" "http://127.0.0.1:7681/api/status"
smoke_note "post-restart persistence"
run_in_container "$container_name" 'grep -Fx "smoke-home" /home/hermes/persist-home.txt >/dev/null && grep -Fx "smoke-workspace" /workspace/persist-workspace.txt >/dev/null'
smoke_note "post-restart nix profile"
wait_for_hermes_shell "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'
smoke_note "post-restart managed tools"
	run_as_hermes "$container_name" 'for cmd in bw gws gh gcloud blogwatcher-cli; do command -v "$cmd" >/dev/null || exit 1; done'
	run_as_hermes "$container_name" 'bw --help >/dev/null'
run_as_hermes "$container_name" 'test -d /home/hermes/.local/state/bitwarden-cli'
run_as_hermes "$container_name" 'gws --help >/dev/null'
run_as_hermes "$container_name" 'gh --help >/dev/null'
run_as_hermes "$container_name" 'gcloud --help >/dev/null'
run_as_hermes "$container_name" 'blogwatcher-cli --help >/dev/null'
smoke_note "post-restart browser profile"
run_browser_profile_probe "$container_name" read

"$container_engine" rm -f "$container_name" >/dev/null
start_test_container_with_retry ""
recreate_dashboard_port="$(container_host_port)"
[ -n "$recreate_dashboard_port" ] || exit 1

smoke_note "post-recreate dashboard"
wait_for_container_http "$container_name" "http://127.0.0.1:7681/api/status"
smoke_note "post-recreate persistence"
run_in_container "$container_name" 'grep -Fx "smoke-home" /home/hermes/persist-home.txt >/dev/null && grep -Fx "smoke-workspace" /workspace/persist-workspace.txt >/dev/null'
smoke_note "post-recreate nix profile"
wait_for_hermes_shell "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'
smoke_note "post-recreate browser profile"
run_browser_profile_probe "$container_name" read
