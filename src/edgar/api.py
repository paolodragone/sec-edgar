import asyncio
from datetime import datetime
from operator import attrgetter
from pprint import pp
from typing import Any
from urllib.parse import urljoin

from httpx import AsyncClient as AsyncHTTPClient
from pyrate_limiter import limiter_factory
from pyrate_limiter.extras.httpx_limiter import AsyncRateLimiterTransport

from edgar.types import CompanyFiling, CompanyTicker

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

    async def fetch_recent_filings(
        self,
        cik: str,
        filter_form: str,
    ) -> list[CompanyFiling]:
        data = await self._fetch_recent_filings(cik)
        return self._parse_recent_filings(data, filter_form)

    async def _fetch_recent_filings(self, cik: str) -> Any:
        url = urljoin(self.SEC_DATA_BASE_URL, f"submissions/CIK{cik}.json")
        resp = await self.http_client.get(url)
        return resp.json()

    def _parse_recent_filings(self, data: Any, filter_form: str) -> list[CompanyFiling]:
        try:
            cik = data["cik"]
            recent_filings = data["filings"]["recent"]

            recent_filings_iter = zip(
                recent_filings["form"],
                recent_filings["filingDate"],
                recent_filings["acceptanceDateTime"],
                recent_filings["accessionNumber"],
                recent_filings["primaryDocument"],
            )

            filings: list[CompanyFiling] = []

            for row in recent_filings_iter:
                form = row[0]

                if form != filter_form:
                    continue

                filing = CompanyFiling(
                    cik=cik,
                    form=form,
                    filing_date=datetime.fromisoformat(row[1]),
                    acceptance_datetime=datetime.fromisoformat(row[2][:-1]),
                    accession_number=row[3],
                    primary_document=row[4],
                )

                filings.append(filing)

            # the endpoint should return filings in reverse filing order
            # but just in case we sort based on filing date and acceptance datetime
            # (to break ties if two filings have the same filing date)
            filings.sort(key=lambda item: (item.filing_date, item.acceptance_datetime))

            return filings
        except KeyError as exc:
            raise EdgarAPIError(
                f"Failed to parse company recent filings: {data}"
            ) from exc

    def get_primary_document_url(self, filing: CompanyFiling) -> str:
        return urljoin(
            self.SEC_BASE_URL,
            "/Archives/edgar/data"
            f"/{filing.cik.lstrip('0')}"
            f"/{filing.accession_number.replace("-", "")}"
            f"/{filing.primary_document}",
        )  # fmt: skip


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
