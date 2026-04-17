import asyncio
import functools
from pathlib import Path
from typing import Any, override

from pyrate_limiter import Limiter
from weasyprint import HTML, URLFetcher

from edgar.api import DEFAULT_USER_AGENT, get_rate_limiter


class WebPDFPrinter:
    def __init__(self, url_fetcher: URLFetcher | None = None) -> None:
        self.url_fetcher = url_fetcher or get_url_fetcher()

    async def print(self, url: str, output_file: Path) -> None:
        loop = asyncio.get_running_loop()
        fn = functools.partial(self._print, url, output_file)
        await loop.run_in_executor(None, fn)  # run sync function asynchronously

    def _print(self, url: str, output_file: Path) -> None:
        HTML(url, url_fetcher=self.url_fetcher).write_pdf(output_file)


class RateLimitedURLFetcher(URLFetcher):
    """A rate-limited WeasyPrint URLFetcher"""

    def __init__(
        self,
        *args: Any,
        limiter: Limiter | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.limiter = limiter or get_rate_limiter()

    @override
    def fetch(self, url, headers=None):
        return super().fetch(url, headers)


def get_url_fetcher(user_agent: str = DEFAULT_USER_AGENT) -> URLFetcher:
    return RateLimitedURLFetcher(http_headers={"User-Agent": user_agent})
