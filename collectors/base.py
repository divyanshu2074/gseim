"""Base polite collector for GSEIM with rate-limiting and robots.txt compliance."""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import urllib.robotparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from gseim.config.settings import USER_AGENT, REQUEST_TIMEOUT, RATE_LIMIT_DELAY

logger = logging.getLogger("gseim.collectors")

class BaseCollector(ABC):
    """Abstract Base Collector ensuring polite crawling and unified interface."""

    # Class-level rate limiter: maps netloc to last_request_time
    _last_request_times: Dict[str, float] = {}
    _robots_parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def __init__(self, user_agent: str = USER_AGENT, timeout: int = REQUEST_TIMEOUT):
        self.user_agent = user_agent
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a resilient requests session with automatic retries."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.7",
            "Connection": "keep-alive"
        })

        retries = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def is_allowed_by_robots(self, url: str) -> bool:
        """Check robots.txt permission for the requested URL."""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = f"{base_url}/robots.txt"

            if base_url not in self._robots_parsers:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                try:
                    res = self.session.get(robots_url, timeout=5)
                    if res.status_code == 200:
                        rp.parse(res.text.splitlines())
                    else:
                        # If robots.txt doesn't exist (404), assume allowed
                        rp.allow_all = True
                except Exception:
                    rp.allow_all = True
                self._robots_parsers[base_url] = rp

            return self._robots_parsers[base_url].can_fetch(self.user_agent, url)
        except Exception as e:
            logger.debug(f"Robots check error for {url}: {e}")
            return True

    def polite_delay(self, url: str, delay: float = RATE_LIMIT_DELAY):
        """Enforce per-domain rate limiting."""
        domain = urlparse(url).netloc
        now = time.time()
        last_time = self._last_request_times.get(domain, 0.0)
        elapsed = now - last_time

        if elapsed < delay:
            sleep_time = delay - elapsed
            time.sleep(sleep_time)

        self._last_request_times[domain] = time.time()

    def fetch(self, url: str, check_robots: bool = True) -> Optional[requests.Response]:
        """Fetch URL respectfully obeying rate limits and robots.txt."""
        if check_robots and not self.is_allowed_by_robots(url):
            logger.warning(f"Crawling disallowed by robots.txt: {url}")
            return None

        self.polite_delay(url)
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            return None

    @abstractmethod
    def collect(self, source: Dict[str, Any]) -> list[Dict[str, Any]]:
        """Collect records from the given source definition."""
        pass
