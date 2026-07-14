"""
Vadoo AI API async HTTP client.
Base URL: https://aiapi.vadoo.tv
Authentication: X-Api-Key header
"""

import os
import httpx
from typing import Any

BASE_URL = "https://aiapi.vadoo.tv"


def _get_api_key() -> str:
    key = os.environ.get("VADOO_API_KEY", "")
    if not key:
        raise ValueError(
            "VADOO_API_KEY is not set. "
            "Add it to your .env file or environment variables."
        )
    return key


def _headers() -> dict[str, str]:
    return {"X-Api-Key": _get_api_key()}


async def get(path: str, params: dict[str, Any] | None = None) -> Any:
    """Perform an authenticated GET request."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        resp = await client.get(path, headers=_headers(), params=params or {})
        if resp.status_code >= 400:
            try:
                err_data = resp.json()
                if isinstance(err_data, dict) and "error" in err_data:
                    return {"error": err_data["error"]}
                elif isinstance(err_data, dict) and "message" in err_data:
                    return {"error": err_data["message"]}
                return {"error": err_data}
            except Exception:
                return {"error": resp.text}
        return resp.json()


async def post(path: str, body: dict[str, Any]) -> Any:
    """Perform an authenticated POST request with a JSON body."""
    # Remove keys whose value is None so optional params are omitted cleanly
    clean_body = {k: v for k, v in body.items() if v is not None}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        resp = await client.post(path, headers=_headers(), json=clean_body)
        if resp.status_code >= 400:
            try:
                err_data = resp.json()
                if isinstance(err_data, dict) and "error" in err_data:
                    return {"error": err_data["error"]}
                elif isinstance(err_data, dict) and "message" in err_data:
                    return {"error": err_data["message"]}
                return {"error": err_data}
            except Exception:
                return {"error": resp.text}
        return resp.json()
