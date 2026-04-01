from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient, RequestSpec


class FlareSolverrClient(BaseHttpClient):
    def __init__(self, base_url: str, *, default_timeout: float = 30.0):
        super().__init__(base_url.rstrip('/'), default_timeout=default_timeout)

    def build_command(self, cmd: str, **kwargs: Any) -> RequestSpec:
        payload = {'cmd': cmd, **kwargs}
        payload = {key: value for key, value in payload.items() if value is not None}
        return self.build_request_spec('POST', '/v1', json_body=payload)

    def command(self, cmd: str, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        spec = self.build_command(cmd, **kwargs)
        return self.request_json(spec.method, spec.path, json_body=spec.json_body, timeout=timeout if timeout is not None else spec.timeout)

    def request_get(self, url: str, session: str | None = None, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        return self.command('request.get', url=url, session=session, timeout=timeout, **kwargs)

    def build_request_post(self, url: str, post_data: str, session: str | None = None, **kwargs: Any) -> RequestSpec:
        return self.build_command('request.post', url=url, postData=post_data, session=session, **kwargs)

    def request_post(self, url: str, post_data: str, session: str | None = None, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        spec = self.build_request_post(url, post_data, session=session, **kwargs)
        return self.command(spec.json_body['cmd'], timeout=timeout, **{k: v for k, v in spec.json_body.items() if k != 'cmd'})

    def build_sessions_create(self, session: str | None = None, **kwargs: Any) -> RequestSpec:
        return self.build_command('sessions.create', session=session, **kwargs)

    def sessions_create(self, session: str | None = None, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        spec = self.build_sessions_create(session=session, **kwargs)
        return self.command(spec.json_body['cmd'], timeout=timeout, **{k: v for k, v in spec.json_body.items() if k != 'cmd'})

    def sessions_list(self, timeout: float | None = None) -> dict[str, Any]:
        return self.command('sessions.list', timeout=timeout)

    def build_sessions_destroy(self, session: str) -> RequestSpec:
        return self.build_command('sessions.destroy', session=session)

    def sessions_destroy(self, session: str, timeout: float | None = None) -> dict[str, Any]:
        spec = self.build_sessions_destroy(session)
        return self.command(spec.json_body['cmd'], timeout=timeout, **{k: v for k, v in spec.json_body.items() if k != 'cmd'})
