from __future__ import annotations

from typing import Any

import requests


class LMSClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            reason = exc.response.reason if exc.response is not None else "HTTP error"
            raise RuntimeError(f"HTTP {status} {reason}") from None
        except requests.ConnectionError as exc:
            raise RuntimeError(f"connection refused ({url})") from None
        except requests.Timeout as exc:
            raise RuntimeError(f"timeout while connecting to {url}") from None
        except requests.RequestException as exc:
            raise RuntimeError(str(exc)) from None

    def get_items(self) -> list[dict[str, Any]]:
        data = self._get("/items/")
        return data if isinstance(data, list) else []

    def get_pass_rates(self, lab: str) -> list[dict[str, Any]]:
        data = self._get("/analytics/pass-rates", params={"lab": lab})
        return data if isinstance(data, list) else []
