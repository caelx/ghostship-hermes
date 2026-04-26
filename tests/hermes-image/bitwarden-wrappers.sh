#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT

mock_bin="$tmp_root/bin"
mock_state="$tmp_root/state"
mkdir -p "$mock_bin" "$mock_state"

cat >"$mock_bin/bw" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

log="${BW_MOCK_LOG:?}"
status_file="${BW_MOCK_STATUS_FILE:?}"

case "$1" in
  status)
    status="$(cat "$status_file")"
    printf '{"status":"%s"}\n' "$status"
    ;;
  login)
    if [ "${2:-}" != "--apikey" ]; then
      echo "unexpected login args: $*" >&2
      exit 2
    fi
    printf 'login --apikey client=%s secret_set=%s\n' "${BW_CLIENTID:-}" "$([ -n "${BW_CLIENTSECRET:-}" ] && printf yes || printf no)" >>"$log"
    printf 'locked\n' >"$status_file"
    ;;
  unlock)
    if [ "${2:-}" != "--passwordenv" ] || [ "${3:-}" != "BW_PASSWORD" ] || [ "${4:-}" != "--raw" ]; then
      echo "unexpected unlock args: $*" >&2
      exit 2
    fi
    printf 'unlock password_set=%s\n' "$([ -n "${BW_PASSWORD:-}" ] && printf yes || printf no)" >>"$log"
    printf 'mock-session-token\n'
    ;;
  lock)
    printf 'lock\n' >>"$log"
    printf 'locked\n' >"$status_file"
    ;;
  *)
    printf '%s\n' "$*" >>"$log"
    ;;
esac
EOF
chmod +x "$mock_bin/bw"

run_unlock() {
  env \
    PATH="$mock_bin:$PATH" \
    HOME="$tmp_root/home" \
    XDG_RUNTIME_DIR="$tmp_root/run" \
    BITWARDENCLI_APPDATA_DIR="$tmp_root/home/.local/state/bitwarden-cli" \
    BW_MOCK_LOG="$mock_state/bw.log" \
    BW_MOCK_STATUS_FILE="$mock_state/status" \
    "$repo_root/packages/bitwarden-wrappers/bin/bw-unlock"
}

run_lock() {
  env \
    PATH="$mock_bin:$PATH" \
    HOME="$tmp_root/home" \
    XDG_RUNTIME_DIR="$tmp_root/run" \
    BITWARDENCLI_APPDATA_DIR="$tmp_root/home/.local/state/bitwarden-cli" \
    BW_MOCK_LOG="$mock_state/bw.log" \
    BW_MOCK_STATUS_FILE="$mock_state/status" \
    "$repo_root/packages/bitwarden-wrappers/bin/bw-lock"
}

reset_case() {
  rm -rf "$tmp_root/home" "$tmp_root/run"
  : >"$mock_state/bw.log"
}

session_file="$tmp_root/run/ghostship-bitwarden/session.env"

reset_case
printf 'unauthenticated\n' >"$mock_state/status"
output="$(BW_CLIENTID=client-id BW_CLIENTSECRET=super-secret BW_PASSWORD=vault-password run_unlock)"
grep -Fx '{"ok":true,"status":"unlocked","session_file":"'"$session_file"'"}' <<<"$output" >/dev/null
grep -Fx 'login --apikey client=client-id secret_set=yes' "$mock_state/bw.log" >/dev/null
grep -Fx 'unlock password_set=yes' "$mock_state/bw.log" >/dev/null
grep -Fx "export BW_SESSION='mock-session-token'" "$session_file" >/dev/null
test "$(stat -c '%a' "$session_file")" = "600"
! grep -F 'super-secret' <<<"$output" >/dev/null
! grep -F 'vault-password' <<<"$output" >/dev/null
! grep -F 'mock-session-token' <<<"$output" >/dev/null

reset_case
printf 'locked\n' >"$mock_state/status"
output="$(BW_PASSWORD=vault-password run_unlock)"
grep -Fx '{"ok":true,"status":"unlocked","session_file":"'"$session_file"'"}' <<<"$output" >/dev/null
! grep -F 'login --apikey' "$mock_state/bw.log" >/dev/null
grep -Fx 'unlock password_set=yes' "$mock_state/bw.log" >/dev/null

reset_case
printf 'unlocked\n' >"$mock_state/status"
output="$(BW_SESSION=already-unlocked run_unlock)"
grep -Fx '{"ok":true,"status":"unlocked","session_file":"'"$session_file"'"}' <<<"$output" >/dev/null
grep -Fx "export BW_SESSION='already-unlocked'" "$session_file" >/dev/null
test ! -s "$mock_state/bw.log"

reset_case
printf 'unauthenticated\n' >"$mock_state/status"
if output="$(BW_CLIENTID=client-id BW_CLIENTSECRET=super-secret run_unlock)"; then
  echo "bw-unlock unexpectedly succeeded without BW_PASSWORD" >&2
  exit 1
fi
grep -Fx '{"ok":false,"error":"missing_bw_password_env"}' <<<"$output" >/dev/null
! grep -F 'super-secret' <<<"$output" >/dev/null

reset_case
printf 'locked\n' >"$mock_state/status"
if output="$(run_unlock)"; then
  echo "bw-unlock unexpectedly succeeded without BW_PASSWORD" >&2
  exit 1
fi
grep -Fx '{"ok":false,"error":"missing_bw_password_env"}' <<<"$output" >/dev/null

reset_case
printf 'locked\n' >"$mock_state/status"
mkdir -p "$(dirname "$session_file")"
printf "export BW_SESSION='active-session'\n" >"$session_file"
output="$(run_lock)"
grep -Fx '{"ok":true,"status":"locked"}' <<<"$output" >/dev/null
grep -Fx 'lock' "$mock_state/bw.log" >/dev/null
! grep -F 'logout' "$mock_state/bw.log" >/dev/null
test ! -e "$session_file"

"$repo_root/packages/bitwarden-wrappers/bin/bw-unlock" --help >/dev/null
"$repo_root/packages/bitwarden-wrappers/bin/bw-lock" --help >/dev/null

printf 'bitwarden wrapper tests passed\n'
