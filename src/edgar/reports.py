import asyncio
from pathlib import Path

from structlog.contextvars import bind_contextvars, unbind_contextvars

from edgar.api import EdgarAPIClient, get_edgar_api_client
from edgar.logging import get_logger
from edgar.printer import WebPDFPrinter
from edgar.types import CompanyFiling

logger = get_logger(__name__)

DEFAULT_FORM = "10-K"


class ReportDownloader:
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

    async def download_latest_reports(
        self,
        tickers: list[str],
        output_dir: Path,
        filter_form: str = DEFAULT_FORM,
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        async def _download_latest_report(ticker: str) -> None:
            try:
                output_file = self.get_output_file_path(ticker, filter_form, output_dir)

                await self.download_latest_report(
                    ticker=ticker,
                    output_file=output_file,
                    filter_form=filter_form,
                )
            except ReportDownloaderError:
                # Log errors but do not fail so other tasks can still run
                logger.error(
                    "An error occurred while downloading the latest report",
                    ticker=ticker,
                    exc_info=True,
                )

        async with asyncio.TaskGroup() as tg:
            for ticker in tickers:
                tg.create_task(_download_latest_report(ticker))

    def get_output_file_path(
        self,
        ticker: str,
        filter_form: str,
        output_dir: Path,
    ) -> Path:
        form = filter_form.replace("-", "").lower()
        return output_dir / f"{ticker.lower()}_{form}.pdf"

    async def download_latest_report(
        self,
        ticker: str,
        output_file: Path,
        filter_form: str = DEFAULT_FORM,
    ) -> None:
        bind_contextvars(ticker=ticker)

        logger.info(
            "Download latest report",
            form=filter_form,
            output_file=str(output_file),
        )

        if not (cik := self.ticker_cik_map.get(ticker)):
            raise UnknownTickerError(f"Unknown ticker: '{ticker}'")

        logger.debug("Fetching recent filings", cik=cik)

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

        unbind_contextvars("ticker")

    async def download_report(self, filing: CompanyFiling, output_file: Path) -> None:
        report_url = self.client.get_primary_document_url(filing)

        logger.debug(
            "Downloading report",
            report_url=report_url,
            output_file=str(output_file),
        )

        await self.printer.print(report_url, output_file=output_file)


class ReportDownloaderError(Exception): ...


class UnknownTickerError(ReportDownloaderError): ...


class NoFilingsFoundError(ReportDownloaderError): ...


async def download_reports(tickers: list[str], output_dir: Path) -> None:
    printer = WebPDFPrinter()

    async with get_edgar_api_client() as client:
        downloader = ReportDownloader(client, printer)
        await downloader.load_ticker_cik_map()
        await downloader.download_latest_reports(tickers, output_dir)


if __name__ == "__main__":
    asyncio.run(download_reports(["NVDA", "GOOGL"], Path(".tmp")))
