"""Polite HTTP client with per-host rate limiting and retries."""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

DESKTOP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
}


def _is_third_party_connection_failure(error: Exception, target_host: str) -> bool:
    """True when a connection error names a host other than the one requested."""
    if not isinstance(error, requests.ConnectionError) or not target_host:
        return False
    message = str(error)
    match = re.search(r"host='([^']+)'", message)
    return bool(match and match.group(1).lower() != target_host.lower())


class RateLimitedHttpClient:
    """Shared session with ~1 req/s per host and exponential backoff."""

    def __init__(self, delay_seconds: float = 1.0, max_retries: int = 3, timeout: int = 25):
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(DESKTOP_HEADERS)
        self._last_request_at: dict[str, float] = {}

    def _host(self, url: str) -> str:
        return urlparse(url).netloc or "unknown"

    def _respect_rate_limit(self, url: str) -> None:
        host = self._host(url)
        last = self._last_request_at.get(host, 0.0)
        elapsed = time.monotonic() - last
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)

    def get_text(
        self,
        url: str,
        *,
        headers: dict | None = None,
        max_retries: int | None = None,
    ) -> str:
        """Fetch a URL, retrying transient failures.

        `max_retries` overrides the client default for one call — useful for
        optional feeds where a 429 means "not today" and burning 14 seconds of
        backoff buys nothing.
        """
        retries = self.max_retries if max_retries is None else max(1, max_retries)
        target_host = self._host(url)
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            self._respect_rate_limit(url)
            self._last_request_at[self._host(url)] = time.monotonic()
            try:
                response = self._session.get(url, timeout=self.timeout, headers=headers)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait = int(retry_after) if retry_after else 2 ** attempt
                    except ValueError:
                        wait = 2 ** attempt
                    wait = min(max(wait, 2 ** (attempt - 1)), 60)
                    last_error = requests.HTTPError("429 Too Many Requests", response=response)
                    if attempt >= retries:
                        break
                    logger.warning(
                        "GET rate-limited (%d/%d) %s — retry in %ds",
                        attempt, retries, url, wait,
                    )
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                status = getattr(getattr(e, "response", None), "status_code", None)
                if status is not None and 400 <= status < 500 and status != 429:
                    raise
                last_error = e
                # A connection failure against some *other* host means the site
                # redirected us somewhere unreachable — typically a tracking or
                # consent domain that a DNS blocker is refusing. Retrying just
                # repeats the same redirect, so give up immediately and quietly.
                if _is_third_party_connection_failure(e, target_host):
                    logger.info(
                        "Skipping %s: redirects to an unreachable third-party host",
                        url,
                    )
                    break
                if attempt >= retries:
                    break
                backoff = 2 ** (attempt - 1)
                logger.warning(
                    "GET failed (%d/%d) %s: %s — retry in %ds",
                    attempt, retries, url, e, backoff,
                )
                time.sleep(backoff)
        raise requests.RequestException(f"All retries failed for {url}") from last_error

    def get_json(self, url: str, *, headers: dict | None = None) -> dict | list:
        import json
        return json.loads(self.get_text(url, headers=headers))
