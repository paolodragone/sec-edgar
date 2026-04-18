import re
from pathlib import Path
from textwrap import dedent

from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from edgar.api import get_edgar_api_client
from edgar.printer import WebPDFPrinter
from edgar.reports import ReportDownloader


async def test_reports_downloader(mocker: MockerFixture, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(r"^.+files\/company_tickers\.json$"),
        text=dedent("""
            {
                "0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
                "1": {"cik_str": 1652044, "ticker": "GOOGL", "title": "Alphabet Inc."},
                "2": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
                "3": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
                "4": {"cik_str": 1018724, "ticker": "AMZN", "title": "AMAZON COM INC"},
                "5": {"cik_str": 1730168, "ticker": "AVGO", "title": "Broadcom Inc."},
                "6": {"cik_str": 1326801, "ticker": "META", "title": "Meta Platforms, Inc."},
                "7": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla, Inc."},
                "8": {"cik_str": 1067983, "ticker": "BRK-B", "title": "BERKSHIRE HATHAWAY INC"},
                "9": {"cik_str": 104169, "ticker": "WMT", "title": "Walmart Inc."},
                "10": {"cik_str": 19617, "ticker": "JPM", "title": "JPMORGAN CHASE & CO"}
            }
        """).strip(),
    )

    httpx_mock.add_response(
        url=re.compile(r"^.+submissions\/CIK\d+\.json$"),
        text=dedent("""
            {
                "cik": "0001045810",
                "filings": {
                    "recent": {
                        "form": [
                            "4",
                            "10-K",
                            "8-K",
                            "13F-HR",
                            "10-K"
                        ],
                        "accessionNumber": [
                            "0000102909-26-000426",
                            "0001199039-26-000003",
                            "0001725292-26-000002",
                            "0001526111-26-000005",
                            "0001696841-26-000006"
                        ],
                        "filingDate": [
                            "2026-03-26",
                            "2026-03-24",
                            "2026-03-20",
                            "2026-03-20",
                            "2026-03-20"
                        ],
                        "acceptanceDateTime": [
                            "2026-03-26T11:52:04.000Z",
                            "2026-03-24T17:13:39.000Z",
                            "2026-03-20T20:14:03.000Z",
                            "2026-03-20T20:13:05.000Z",
                            "2026-03-20T20:11:05.000Z"
                        ],
                        "primaryDocument": [
                            "xslF345X06/wk-form4_1774051558.xml",
                            "xsl144X01/primary_doc.xml",
                            "xslF345X05/wk-form4_1767996327.xml",
                            "xsl144X01/primary_doc.xml",
                            "filename1.pdf"
                        ]
                    }
                }
            }
        """).strip(),
    )

    printer = WebPDFPrinter()
    printer.print = mocker.AsyncMock()
    output_file = Path("output.pdf")
    exp_url = "https://www.sec.gov/Archives/edgar/data/1045810/000119903926000003/xsl144X01/primary_doc.xml"

    async with get_edgar_api_client() as client:
        downloader = ReportDownloader(client, printer)
        await downloader.load_ticker_cik_map()
        await downloader.download_latest_report("NVDA", output_file)

    printer.print.assert_awaited_once_with(exp_url, output_file=output_file)
