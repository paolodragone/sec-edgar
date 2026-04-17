from dataclasses import dataclass
from datetime import datetime


@dataclass
class CompanyTicker:
    index: int
    ticker: str
    title: str
    cik: str


@dataclass
class CompanyFiling:
    # minimal fields to satisfy requirements
    # may be expanded in the future if needed

    cik: str
    form: str
    filing_date: datetime
    acceptance_datetime: datetime
    accession_number: str
    primary_document: str
