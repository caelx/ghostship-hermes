from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient, HttpStatusError, RequestSpec


class TautulliClient(BaseHttpClient):
    def __init__(self, base_url: str, api_key: str, *, default_timeout: float = 30.0):
        base = base_url.rstrip('/')
        if not base.endswith('/api/v2'):
            base = f'{base}/api/v2'
        super().__init__(base, default_timeout=default_timeout)
        self.api_key = api_key

    def build_call(self, cmd: str, **kwargs: Any) -> RequestSpec:
        params = {'apikey': self.api_key, 'cmd': cmd}
        params.update({key: value for key, value in kwargs.items() if value is not None})
        return self.build_request_spec('GET', '', params=params)

    def call(self, cmd: str, timeout: float | None = None, **kwargs: Any) -> Any:
        spec = self.build_call(cmd, **kwargs)
        payload = self.request_json(spec.method, spec.path, params=spec.params, timeout=timeout if timeout is not None else spec.timeout)
        response = payload.get('response', {})
        if response.get('result') != 'success':
            raise HttpStatusError('remote service returned API error', status_code=200, details=response.get('message'))
        return response.get('data')

    def get_server_status(self, timeout: float | None = None) -> Any:
        return self.call('server_status', timeout=timeout)

    def get_tautulli_info(self, timeout: float | None = None) -> Any:
        return self.call('get_tautulli_info', timeout=timeout)

    def get_status(self, timeout: float | None = None) -> Any:
        return self.call('status', timeout=timeout)

    def get_activity(self, timeout: float | None = None) -> Any:
        return self.call('get_activity', timeout=timeout)

    def build_terminate_session(self, session_id: str, message: str | None = None) -> RequestSpec:
        kwargs: dict[str, Any] = {'session_id': session_id}
        if message:
            kwargs['message'] = message
        return self.build_call('terminate_session', **kwargs)

    def terminate_session(self, session_id: str, message: str | None = None, timeout: float | None = None) -> Any:
        spec = self.build_terminate_session(session_id, message=message)
        return self.call(spec.params['cmd'], timeout=timeout, **{k: v for k, v in spec.params.items() if k not in {'apikey', 'cmd'}})

    def get_history(self, page: int = 1, length: int = 10, search: str | None = None, order_column: str = 'date', order_dir: str = 'desc', timeout: float | None = None) -> Any:
        kwargs: dict[str, Any] = {'start': (page - 1) * length, 'length': length, 'order_column': order_column, 'order_dir': order_dir}
        if search:
            kwargs['search'] = search
        return self.call('get_history', timeout=timeout, **kwargs)

    def get_libraries(self, timeout: float | None = None) -> Any:
        return self.call('get_libraries', timeout=timeout)

    def get_library_user_stats(self, section_id: int, timeout: float | None = None) -> Any:
        return self.call('get_library_user_stats', timeout=timeout, section_id=section_id)

    def get_users(self, timeout: float | None = None) -> Any:
        return self.call('get_users', timeout=timeout)

    def get_user_player_stats(self, user_id: int, timeout: float | None = None) -> Any:
        return self.call('get_user_player_stats', timeout=timeout, user_id=user_id)

    def get_user_watch_time_stats(self, user_id: int, timeout: float | None = None) -> Any:
        return self.call('get_user_watch_time_stats', timeout=timeout, user_id=user_id)

    def get_metadata(self, rating_key: int, timeout: float | None = None) -> Any:
        return self.call('get_metadata', timeout=timeout, rating_key=rating_key)

    def search(self, query: str, limit: int = 10, timeout: float | None = None) -> Any:
        return self.call('search', timeout=timeout, query=query, limit=limit)

    def build_restart(self) -> RequestSpec:
        return self.build_call('restart')

    def restart(self, timeout: float | None = None) -> Any:
        return self.call('restart', timeout=timeout)
