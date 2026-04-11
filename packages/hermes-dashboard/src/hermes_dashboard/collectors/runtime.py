from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Iterable

DEFAULT_GATEWAY_SERVICE = 'ghostship-hermes-gateway.service'


@dataclass
class ServiceProbe:
    service: str
    scope: str | None
    active: bool
    note: str = ''


def managed_gateway_service_candidates() -> list[str]:
    candidates: list[str] = []
    for raw in (
        os.environ.get('GHOSTSHIP_HERMES_GATEWAY_SERVICE'),
        os.environ.get('HERMES_GATEWAY_SERVICE'),
        DEFAULT_GATEWAY_SERVICE,
        'hermes-gateway.service',
        'hermes-gateway',
    ):
        if raw and raw not in candidates:
            candidates.append(raw)
    return candidates


def default_profile_name() -> str:
    return os.environ.get('GHOSTSHIP_HUD_DEFAULT_PROFILE_NAME', 'Managed Agent')


def _check_systemd_service(service: str, scope: str | None) -> ServiceProbe:
    command = ['systemctl']
    if scope == 'user':
        command.append('--user')
    command.extend(['is-active', service])
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ServiceProbe(service=service, scope=scope, active=False, note='systemctl unavailable')
    status = result.stdout.strip() or result.stderr.strip() or 'unknown'
    return ServiceProbe(service=service, scope=scope, active=status == 'active', note=status)


def probe_services(services: Iterable[str]) -> list[ServiceProbe]:
    probes: list[ServiceProbe] = []
    for service in services:
        for scope in (None, 'user'):
            probe = _check_systemd_service(service, scope)
            probes.append(probe)
            if probe.active:
                return probes
    return probes


def gateway_service_probe() -> ServiceProbe:
    probes = probe_services(managed_gateway_service_candidates())
    for probe in probes:
        if probe.active:
            return probe
    if probes:
        return probes[0]
    return ServiceProbe(service=DEFAULT_GATEWAY_SERVICE, scope=None, active=False, note='unconfigured')
