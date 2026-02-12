"""Telegram notification helpers via n8n webhook."""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

WEBHOOK_URL: str = "http://localhost:5678/webhook/send-telegram"


async def send_telegram(
    message: str,
    webhook_url: str | None = None,
) -> bool:
    """Send a Telegram notification via the n8n webhook (async).

    Parameters
    ----------
    message:
        Plain-text message to send.
    webhook_url:
        Override the default webhook URL if needed.

    Returns
    -------
    bool
        ``True`` if the webhook responded with a 2xx status code.
    """
    url = f"{webhook_url or WEBHOOK_URL}?message={quote(message)}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Telegram webhook returned %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Failed to reach Telegram webhook: %s", exc)
    return False


def send_telegram_sync(
    message: str,
    webhook_url: str | None = None,
) -> bool:
    """Send a Telegram notification via the n8n webhook (synchronous).

    Parameters
    ----------
    message:
        Plain-text message to send.
    webhook_url:
        Override the default webhook URL if needed.

    Returns
    -------
    bool
        ``True`` if the webhook responded with a 2xx status code.
    """
    url = f"{webhook_url or WEBHOOK_URL}?message={quote(message)}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
            return True
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Telegram webhook returned %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
    except httpx.RequestError as exc:
        logger.error("Failed to reach Telegram webhook: %s", exc)
    return False
