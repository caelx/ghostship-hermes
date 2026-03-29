from typing import Any, Dict, List, Optional
import httpx


class CloakBrowserClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.post(url, json=json_data, params=params)
            response.raise_for_status()
            return response.json()

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.delete(url, params=params)
            response.raise_for_status()
            return response.status_code == 200

    def _put(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.put(url, json=json_data)
            response.raise_for_status()
            return response.json()

    def get_auth_status(self) -> Dict[str, Any]:
        return self._get("/api/auth/status")

    def login(self, token: str) -> Dict[str, Any]:
        return self._post("/api/auth/login", json_data={"token": token})

    def logout(self) -> Dict[str, Any]:
        return self._post("/api/auth/logout")

    def get_system_status(self) -> Dict[str, Any]:
        return self._get("/api/status")

    def list_profiles(self) -> List[Dict[str, Any]]:
        return self._get("/api/profiles")

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        return self._get(f"/api/profiles/{profile_id}")

    def create_profile(
        self,
        name: str,
        fingerprint_seed: Optional[int] = None,
        proxy: Optional[str] = None,
        timezone: Optional[str] = None,
        locale: Optional[str] = None,
        platform: str = "windows",
        user_agent: Optional[str] = None,
        screen_width: int = 1920,
        screen_height: int = 1080,
        gpu_vendor: Optional[str] = None,
        gpu_renderer: Optional[str] = None,
        hardware_concurrency: Optional[int] = None,
        humanize: bool = False,
        human_preset: str = "default",
        headless: bool = False,
        geoip: bool = False,
        clipboard_sync: bool = True,
        color_scheme: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        data = {"name": name}
        if fingerprint_seed is not None:
            data["fingerprint_seed"] = fingerprint_seed
        if proxy is not None:
            data["proxy"] = proxy
        if timezone is not None:
            data["timezone"] = timezone
        if locale is not None:
            data["locale"] = locale
        data["platform"] = platform
        if user_agent is not None:
            data["user_agent"] = user_agent
        data["screen_width"] = screen_width
        data["screen_height"] = screen_height
        if gpu_vendor is not None:
            data["gpu_vendor"] = gpu_vendor
        if gpu_renderer is not None:
            data["gpu_renderer"] = gpu_renderer
        if hardware_concurrency is not None:
            data["hardware_concurrency"] = hardware_concurrency
        data["humanize"] = humanize
        data["human_preset"] = human_preset
        data["headless"] = headless
        data["geoip"] = geoip
        data["clipboard_sync"] = clipboard_sync
        if color_scheme is not None:
            data["color_scheme"] = color_scheme
        if notes is not None:
            data["notes"] = notes
        if tags is not None:
            data["tags"] = tags
        return self._post("/api/profiles", json_data=data)

    def update_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        fingerprint_seed: Optional[int] = None,
        proxy: Optional[str] = None,
        timezone: Optional[str] = None,
        locale: Optional[str] = None,
        platform: Optional[str] = None,
        user_agent: Optional[str] = None,
        screen_width: Optional[int] = None,
        screen_height: Optional[int] = None,
        gpu_vendor: Optional[str] = None,
        gpu_renderer: Optional[str] = None,
        hardware_concurrency: Optional[int] = None,
        humanize: Optional[bool] = None,
        human_preset: Optional[str] = None,
        headless: Optional[bool] = None,
        geoip: Optional[bool] = None,
        clipboard_sync: Optional[bool] = None,
        color_scheme: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        data = {}
        if name is not None:
            data["name"] = name
        if fingerprint_seed is not None:
            data["fingerprint_seed"] = fingerprint_seed
        if proxy is not None:
            data["proxy"] = proxy
        if timezone is not None:
            data["timezone"] = timezone
        if locale is not None:
            data["locale"] = locale
        if platform is not None:
            data["platform"] = platform
        if user_agent is not None:
            data["user_agent"] = user_agent
        if screen_width is not None:
            data["screen_width"] = screen_width
        if screen_height is not None:
            data["screen_height"] = screen_height
        if gpu_vendor is not None:
            data["gpu_vendor"] = gpu_vendor
        if gpu_renderer is not None:
            data["gpu_renderer"] = gpu_renderer
        if hardware_concurrency is not None:
            data["hardware_concurrency"] = hardware_concurrency
        if humanize is not None:
            data["humanize"] = humanize
        if human_preset is not None:
            data["human_preset"] = human_preset
        if headless is not None:
            data["headless"] = headless
        if geoip is not None:
            data["geoip"] = geoip
        if clipboard_sync is not None:
            data["clipboard_sync"] = clipboard_sync
        if color_scheme is not None:
            data["color_scheme"] = color_scheme
        if notes is not None:
            data["notes"] = notes
        if tags is not None:
            data["tags"] = tags
        return self._put(f"/api/profiles/{profile_id}", json_data=data)

    def delete_profile(self, profile_id: str) -> bool:
        return self._delete(f"/api/profiles/{profile_id}")

    def launch_profile(self, profile_id: str) -> Dict[str, Any]:
        return self._post(f"/api/profiles/{profile_id}/launch")

    def stop_profile(self, profile_id: str) -> Dict[str, Any]:
        return self._post(f"/api/profiles/{profile_id}/stop")

    def get_profile_status(self, profile_id: str) -> Dict[str, Any]:
        return self._get(f"/api/profiles/{profile_id}/status")

    def get_clipboard(self, profile_id: str) -> Dict[str, Any]:
        return self._get(f"/api/profiles/{profile_id}/clipboard")

    def set_clipboard(self, profile_id: str, text: str) -> Dict[str, Any]:
        return self._post(
            f"/api/profiles/{profile_id}/clipboard",
            json_data={"text": text},
        )

    def get_cdp_info(self, profile_id: str) -> Dict[str, Any]:
        return self._get(f"/api/profiles/{profile_id}/cdp")
