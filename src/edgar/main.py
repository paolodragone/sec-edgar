import argparse
import asyncio
from argparse import Namespace
from pathlib import Path
from textwrap import dedent

from edgar.logging import get_logger
from edgar.reports import download_reports

logger = get_logger(__name__)

DEFAULT_OUTPUT_DIR = "reports"
DEFAULT_TICKERS = [
    "GOOGL",  # Alphabet
    "AAPL",  # Apple
    "META",  # Meta
    "AMZN",  # Amazon
    "NFLX",  # Netflix
    "GS",  # Goldman Sachs
]


async def main() -> None:
    args = parse_args()

    logger.info(
        "SEC EDGAR Report downloader",
        **vars(args),
    )

    await download_reports(args.tickers, Path(args.output_dir))


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=dedent("""
        Download latest 10-K reports in PDF format for the given company tickers.

        Usage
        -----
        The default behaviour is to download the latest 10-K report for all default tickers:
            python -m edgar.main
        
        A list of tickers can be provided via command line:
            python -m edgar.main --tickers AAPL GOOGL NVDA

        Otherwise it can also be used with an input file like: (one ticker per line)
            cat tickers.txt | xargs python edgar.main --tickers
        """),
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory where PDF files will be downloaded; default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=DEFAULT_TICKERS,
        help=f"Company tickers to download the latest reports for; default: {DEFAULT_TICKERS}",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main())
