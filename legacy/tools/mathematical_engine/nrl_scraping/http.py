"""Polite HTTP layer shared by all NRL scraping jobs.

Provides a single requests.Session with a desktop User-Agent, a minimum
delay between requests (rate limiting), and retries with exponential
backoff for transient failures.
"""

import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nrl.com"

DESKTOP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


class NRLHttpClient:
    """Rate-limited, retrying HTTP client for nrl.com pages."""

    def __init__(self, delay_seconds: float = 1.0, max_retries: int = 4, timeout: int = 30):
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(DESKTOP_HEADERS)
        self._last_request_at = 0.0

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)

    def get_html(self, url: str) -> str:
        """GET a page and return its HTML, retrying transient failures.

        Raises requests.RequestException if all retries are exhausted.
        """
        if url.startswith("/"):
            url = BASE_URL + url

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._respect_rate_limit()
            self._last_request_at = time.monotonic()
            try:
                response = self._session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                status = getattr(getattr(e, "response", None), "status_code", None)
                # 4xx errors (except 429 rate limiting) won't improve on retry
                if status is not None and 400 <= status < 500 and status != 429:
                    raise
                last_error = e
                backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s, 8s
                logger.warning(
                    "Request failed (attempt %d/%d) for %s: %s. Retrying in %ds...",
                    attempt, self.max_retries, url, e, backoff,
                )
                time.sleep(backoff)

        raise requests.RequestException(f"All {self.max_retries} retries failed for {url}") from last_error
