from collections.abc import Sequence
from textwrap import dedent
from typing import Mapping

from pytest_httpx import HTTPXMock

from edgar.api import EdgarAPIClient, get_http_client


async def test_edgar_api_client_fetch_tickers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        # Excerpt from actual endpoint
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
        is_reusable=True,
    )

    async with get_http_client() as http_client:
        edgar = EdgarAPIClient(http_client)
        raw_tickers = await edgar._fetch_tickers()
        tickers = await edgar.fetch_tickers()

    assert isinstance(raw_tickers, Mapping)
    assert len(raw_tickers) == 11

    assert isinstance(tickers, Sequence)
    assert len(tickers) == 11

    test_tickers = [
        (0, "NVDA"),
        (1, "GOOGL"),
        (6, "META"),
        (10, "JPM"),
    ]

    for idx, ticker in test_tickers:
        assert tickers[idx].ticker == ticker


async def test_edgar_api_client_fetch_recent_filings(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        # Excerpt from actual endpoint
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
        is_reusable=True,
    )

    cik = "0001045810"
    filter_form = "10-K"

    async with get_http_client() as http_client:
        edgar = EdgarAPIClient(http_client)
        raw_filings = await edgar._fetch_recent_filings(cik)
        filings = await edgar.fetch_recent_filings(cik, filter_form)

    assert isinstance(raw_filings, Mapping)
    assert "cik" in raw_filings
    assert "filings" in raw_filings
    assert "recent" in raw_filings["filings"]

    for lst in [
        "form",
        "accessionNumber",
        "filingDate",
        "acceptanceDateTime",
        "primaryDocument",
    ]:
        assert len(raw_filings["filings"]["recent"][lst]) == 5

    assert isinstance(filings, Sequence)
    assert len(filings) == 2

    for filing in filings:
        assert filing.cik == cik
        assert filing.form == filter_form
