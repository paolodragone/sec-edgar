import asyncio
from pathlib import Path

from edgar.api import EdgarAPIClient, get_edgar_api_client
from edgar.html2pdf import WebPDFPrinter
from edgar.types import CompanyFiling


class ReportDownloader:
    DEFAULT_FORM = "10-K"

    def __init__(
        self,
        client: EdgarAPIClient,
        printer: WebPDFPrinter,
    ) -> None:
        self.client = client
        self.printer = printer

        self.ticker_cik_map: dict[str, str] = {}

    async def load_ticker_cik_map(self) -> None:
        tickers = await self.client.fetch_tickers()

        self.ticker_cik_map = {
            ticker.ticker: ticker.cik
            for ticker in tickers
        }  # fmt: skip

    async def download_latest_report(
        self,
        ticker: str,
        output_file: Path,
        filter_form: str = DEFAULT_FORM,
    ) -> None:
        if not (cik := self.ticker_cik_map.get(ticker)):
            raise UnknownTickerError(f"Unknown ticker: '{ticker}'")

        recent_filings = await self.client.fetch_recent_filings(
            cik,
            filter_form=filter_form,
        )

        if not recent_filings:
            raise NoFilingsFoundError(
                f"No filings found for ticker: '{ticker}' (cik: '{cik}') "
            )

        # recent_filings sorted by reverse filing date
        latest_filing = recent_filings[0]

        await self.download_report(latest_filing, output_file)

    async def download_report(self, filing: CompanyFiling, output_file: Path) -> None:
        report_url = self.client.get_primary_document_url(filing)
        await self.printer.print(report_url, output_file=output_file)


class ReportDownloaderError(Exception): ...


class UnknownTickerError(ReportDownloaderError): ...


class NoFilingsFoundError(ReportDownloaderError): ...


async def download_report(ticker: str, output_file: Path) -> None:
    printer = WebPDFPrinter()

    async with get_edgar_api_client() as client:
        downloader = ReportDownloader(client, printer)
        await downloader.load_ticker_cik_map()
        await downloader.download_latest_report(ticker, output_file)


if __name__ == "__main__":
    asyncio.run(download_report("NVDA", Path("nvda.pdf")))
