from __future__ import annotations

from ghostship_cloakbrowser.client import CloakBrowserClient


class DummyCloakBrowserClient(CloakBrowserClient):
    def __init__(self) -> None:
        super().__init__('https://cloak.example', token='secret')
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {'params': params, 'json_data': json_data, 'timeout': timeout}))
        return {'ok': True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyCloakBrowserClient()
    client.get_auth_status(timeout=1)
    client.auth_login('secret', timeout=2)
    client.auth_logout(timeout=3)
    client.get_system_status(timeout=4)
    client.list_profiles(timeout=5)
    client.get_profile('profile-1', timeout=6)
    client.create_profile(name='name', humanize=True, timeout=7)
    client.update_profile('profile-1', notes='updated', timeout=8)
    client.delete_profile('profile-1', timeout=9)
    client.launch_profile('profile-1', timeout=10)
    client.stop_profile('profile-1', timeout=11)
    client.get_profile_status('profile-1', timeout=12)
    client.get_clipboard('profile-1', timeout=13)
    client.set_clipboard('profile-1', 'hello', timeout=14)
    client.get_cdp_info('profile-1', timeout=15)

    assert client.calls == [
        ('GET', '/api/auth/status', {'params': None, 'json_data': None, 'timeout': 1}),
        ('POST', '/api/auth/login', {'params': None, 'json_data': {'token': 'secret'}, 'timeout': 2}),
        ('POST', '/api/auth/logout', {'params': None, 'json_data': None, 'timeout': 3}),
        ('GET', '/api/status', {'params': None, 'json_data': None, 'timeout': 4}),
        ('GET', '/api/profiles', {'params': None, 'json_data': None, 'timeout': 5}),
        ('GET', '/api/profiles/profile-1', {'params': None, 'json_data': None, 'timeout': 6}),
        ('POST', '/api/profiles', {'params': None, 'json_data': {'name': 'name', 'platform': 'windows', 'screen_width': 1920, 'screen_height': 1080, 'humanize': True, 'human_preset': 'default', 'headless': False, 'geoip': False, 'clipboard_sync': True}, 'timeout': 7}),
        ('PUT', '/api/profiles/profile-1', {'params': None, 'json_data': {'notes': 'updated'}, 'timeout': 8}),
        ('DELETE', '/api/profiles/profile-1', {'params': None, 'json_data': None, 'timeout': 9}),
        ('POST', '/api/profiles/profile-1/launch', {'params': None, 'json_data': None, 'timeout': 10}),
        ('POST', '/api/profiles/profile-1/stop', {'params': None, 'json_data': None, 'timeout': 11}),
        ('GET', '/api/profiles/profile-1/status', {'params': None, 'json_data': None, 'timeout': 12}),
        ('GET', '/api/profiles/profile-1/clipboard', {'params': None, 'json_data': None, 'timeout': 13}),
        ('POST', '/api/profiles/profile-1/clipboard', {'params': None, 'json_data': {'text': 'hello'}, 'timeout': 14}),
        ('GET', '/api/profiles/profile-1/cdp', {'params': None, 'json_data': None, 'timeout': 15}),
    ]


def test_request_builders() -> None:
    client = CloakBrowserClient('https://cloak.example', token='secret')
    assert client.build_create_profile(name='demo').to_dict()['json_body']['name'] == 'demo'
    assert client.build_update_profile('profile-1', notes='memo').to_dict()['path'] == '/api/profiles/profile-1'
    assert client.build_set_clipboard('profile-1', 'hello').to_dict()['json_body'] == {'text': 'hello'}
