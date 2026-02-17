"""Telegram notification helpers via n8n webhook."""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

WEBHOOK_URL: str = "http://localhost:5678/webhook/send-telegram"


async def send_telegram(message: str, webhook_url: str | None = None) -> bool:
    url = f"{webhook_url or WEBHOOK_URL}?message={quote(message)}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return True
    except Exception:
        logger.warning("Telegram notification failed", exc_info=True)
        return False
