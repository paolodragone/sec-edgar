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
