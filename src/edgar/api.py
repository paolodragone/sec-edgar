import asyncio
from operator import attrgetter
from pprint import pp
from typing import Any
from urllib.parse import urljoin

from httpx import AsyncClient as AsyncHTTPClient
from pyrate_limiter import limiter_factory
from pyrate_limiter.extras.httpx_limiter import AsyncRateLimiterTransport

from edgar.types import CompanyTicker

# Future-proofing :)
DEFAULT_USER_AGENT = "paolo.dragone@quartr.se"

# SEC max is 10 reqs/s, here set a conservative limit to 8 reqs/s
DEFAULT_MAX_REQS_SEC = 8


class EdgarAPIClient:
    """Small API client to fetch SEC EDGAR data."""

    SEC_BASE_URL = "https://www.sec.gov/"
    SEC_DATA_BASE_URL = "https://data.sec.gov/"

    def __init__(self, http_client: AsyncHTTPClient) -> None:
        self.http_client = http_client

    async def fetch_tickers(self) -> list[CompanyTicker]:
        data = await self._fetch_tickers()
        return self._parse_tickers(data)

    async def _fetch_tickers(self) -> Any:
        url = urljoin(self.SEC_BASE_URL, "files/company_tickers.json")
        resp = await self.http_client.get(url)
        return resp.json()

    def _parse_tickers(self, data: Any) -> list[CompanyTicker]:
        tickers: list[CompanyTicker] = []

        for idx, raw_ticker in data.items():
            try:
                tickers.append(
                    CompanyTicker(
                        index=int(idx),
                        ticker=raw_ticker["ticker"],
                        title=raw_ticker["title"],
                        cik=str(raw_ticker["cik_str"]).zfill(10),
                    )
                )
            except KeyError as exc:
                raise EdgarAPIError(
                    f"Failed to parse company ticker at index '{idx}': {raw_ticker}"
                ) from exc

        # sort by index in place
        # just in case the json parser does not return an ordered dict for some reason
        tickers.sort(key=attrgetter("index"))

        return tickers


class EdgarAPIError(Exception): ...


def get_http_client(
    user_agent: str = DEFAULT_USER_AGENT,
    max_reqs_sec: int = DEFAULT_MAX_REQS_SEC,
) -> AsyncHTTPClient:
    """Create an SEC-friendly HTTP client.

    The SEC API requires requests to be sent with a user-agent containing an email address of the client system administrator.
    Additionally, the request rate limit is set to 10 requests/second, which is enforced by default.
    """

    limiter = limiter_factory.create_inmemory_limiter(rate_per_duration=max_reqs_sec)
    transport = AsyncRateLimiterTransport(limiter=limiter)
    return AsyncHTTPClient(
        headers={"User-Agent": user_agent},
        transport=transport,
    )


async def pprint_tickers() -> None:
    async with get_http_client() as http_client:
        edgar = EdgarAPIClient(http_client)
        tickers = await edgar.fetch_tickers()
        pp(tickers)


if __name__ == "__main__":
    asyncio.run(pprint_tickers())
