from __future__ import annotations

import httpx
from backend.config import settings


async def call_ai_or_placeholder(
    path: str,
    payload: dict,
    placeholder: dict,
    timeout: float = 60.0,
) -> dict:
    """Call the Java AI service at `path`.

    If the Java service is unreachable or returns an error, return `placeholder`
    so the module stays testable until the AI integration is built.
    """
    url = f"{settings.ai_service_url}{path}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
        return response.json()
    except Exception:
        # AI service not ready yet -> serve placeholder so flows remain testable
        return placeholder
