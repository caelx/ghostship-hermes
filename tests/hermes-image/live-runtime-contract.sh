#!/usr/bin/env bash
set -euo pipefail

remote="${1:?usage: live-runtime-contract.sh <ssh-target> [service-name] [container-name]}"
service_name="${2:-podman-hermes.service}"
container_name="${3:-hermes}"
container_shell_path='PATH=/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin'

run_remote() {
  ssh "$remote" "$@"
}

service_logs_since() {
  local since="$1"
  run_remote "journalctl -u '$service_name' --since '$since' --no-pager -o short-iso"
}

stop_started_at="$(date -u +%FT%TZ)"
run_remote "systemctl stop '$service_name'"
stop_state="$(run_remote "systemctl show '$service_name' -p ActiveState -p SubState -p Result")"
printf '%s\n' "$stop_state" | grep -F 'Result=success' >/dev/null
printf '%s\n' "$stop_state" | grep -F 'ActiveState=inactive' >/dev/null
! service_logs_since "$stop_started_at" | grep -F 'resorting to SIGKILL' >/dev/null
! service_logs_since "$stop_started_at" | grep -F "Failed with result 'exit-code'" >/dev/null

run_remote "systemctl start '$service_name'"
run_remote "systemctl is-active '$service_name' | grep -Fx active >/dev/null"

restart_started_at="$(date -u +%FT%TZ)"
run_remote "systemctl restart '$service_name'"
run_remote "systemctl is-active '$service_name' | grep -Fx active >/dev/null"
! service_logs_since "$restart_started_at" | grep -F 'resorting to SIGKILL' >/dev/null
! service_logs_since "$restart_started_at" | grep -F "Failed with result 'exit-code'" >/dev/null

boot_started_at="$(run_remote "systemctl show '$service_name' -p ExecMainStartTimestamp --value")"
boot_logs="$(service_logs_since "$boot_started_at")"
! printf '%s\n' "$boot_logs" | grep -F 'could not create symlink /etc/hostname' >/dev/null
! printf '%s\n' "$boot_logs" | grep -F '/nix/var/nix/profiles/per-user/root/channels exists, but channels have been disabled.' >/dev/null
! printf '%s\n' "$boot_logs" | grep -F '/root/.nix-defexpr/channels/channels' >/dev/null

tooling_started_at="$(date -u +%FT%TZ)"
run_remote "podman exec '$container_name' /bin/sh -lc '$container_shell_path systemctl start ghostship-hermes-user-tooling.service'"
tooling_logs="$(run_remote "podman exec '$container_name' /bin/sh -lc '$container_shell_path journalctl -u ghostship-hermes-user-tooling.service --since \"$tooling_started_at\" --no-pager'")"
! printf '%s\n' "$tooling_logs" | grep -F 'removing ' >/dev/null
