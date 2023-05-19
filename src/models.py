from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PriceEntry:
    date: datetime
    open: float
    close: float
    high: float
    low: float


class StockPricePeriod:
    def __init__(self, ticker: str, price_entries: list[PriceEntry]):
        self.ticker = ticker
        self.price_entries = price_entries

    @property
    def period_close(self) -> float:
        return self.price_entries[-1].close

    @property
    def period_open(self) -> float:
        return self.price_entries[0].open

    @property
    def period_percent_change(self) -> float:
        price_change: float = self.period_close - self.period_open
        return price_change / self.period_open * 100
