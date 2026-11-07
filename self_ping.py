"""Optional self-ping loop for hosts that suspend idle free instances."""

import asyncio
import logging
from urllib.parse import urlparse

import httpx


logger = logging.getLogger(__name__)


def health_url(self_url: str) -> str | None:
    """Return a safe health URL, or None when SELF_URL is not usable."""
    value = (self_url or "").strip().rstrip("/")
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{value}/health"


async def keep_alive(client: httpx.AsyncClient, self_url: str, interval: int) -> None:
    """Ping SELF_URL/health until the application shuts down."""
    target = health_url(self_url)
    if target is None:
        logger.warning("SELF_URL is set but is not a valid http(s) URL; self-ping disabled")
        return

    interval = max(30, int(interval))
    logger.info("Self-ping enabled: %s immediately, then every %ss", target, interval)
    try:
        while True:
            try:
                response = await client.get(
                    target,
                    headers={"User-Agent": "MovieBox-API-self-ping/1.0", "Accept": "application/json"},
                    timeout=10.0,
                )
                if response.is_success:
                    logger.debug("Self-ping healthy: HTTP %s", response.status_code)
                else:
                    logger.warning("Self-ping returned HTTP %s", response.status_code)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Self-ping failed: %s", exc)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.debug("Self-ping stopped")
        raise
