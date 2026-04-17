from dataclasses import dataclass


@dataclass
class CompanyTicker:
    index: int
    ticker: str
    title: str
    cik: str
