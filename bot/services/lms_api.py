from __future__ import annotations

from typing import Any

import requests


class LMSClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _handle_error(self, url: str, exc: Exception) -> RuntimeError:
        if isinstance(exc, requests.HTTPError):
            response = exc.response
            if response is not None:
                return RuntimeError(f"HTTP {response.status_code} {response.reason}")
            return RuntimeError("HTTP error")
        if isinstance(exc, requests.ConnectionError):
            return RuntimeError(f"connection refused ({url})")
        if isinstance(exc, requests.Timeout):
            return RuntimeError(f"timeout while connecting to {url}")
        return RuntimeError(str(exc))

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise self._handle_error(url, exc) from None

    def _post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.post(url, json=payload or {}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise self._handle_error(url, exc) from None

    def get_items(self) -> list[dict[str, Any]]:
        data = self._get("/items/")
        return data if isinstance(data, list) else []

    def get_learners(self) -> list[dict[str, Any]]:
        data = self._get("/learners/")
        return data if isinstance(data, list) else []

    def get_scores(self, lab: str) -> Any:
        return self._get("/analytics/scores", params={"lab": lab})

    def get_pass_rates(self, lab: str) -> Any:
        return self._get("/analytics/pass-rates", params={"lab": lab})

    def get_timeline(self, lab: str) -> Any:
        return self._get("/analytics/timeline", params={"lab": lab})

    def get_groups(self, lab: str) -> Any:
        return self._get("/analytics/groups", params={"lab": lab})

    def get_top_learners(self, lab: str | None = None, limit: int = 5) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if lab:
            params["lab"] = lab
        return self._get("/analytics/top-learners", params=params)

    def get_completion_rate(self, lab: str) -> Any:
        return self._get("/analytics/completion-rate", params={"lab": lab})

    def trigger_sync(self) -> Any:
        return self._post("/pipeline/sync", payload={})
