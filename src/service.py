import logging
from datetime import datetime

import yfinance as yf

from src.models import PriceEntry, StockPricePeriod

logger = logging.getLogger(__name__)


# Get weekly summary for a stock using yfinance
def get_5d_summary(ticker_str: str) -> StockPricePeriod:
    logger.debug(f"Getting data for {ticker_str}...")
    ticker = yf.Ticker(ticker_str)
    # NB: Trading week is 5 days. Only trading days are included in yfinance data
    data = ticker.history(period="5d")

    if data.empty:
        raise Exception(f"Could not get data for {ticker_str}. Ensure ticker is valid")

    logger.debug(f"Got data for {ticker_str}. Length: {len(data)}")

    price_entries = [
        PriceEntry(
            date=datetime.fromisoformat(str(index)),
            open=row["Open"],
            close=row["Close"],
            high=row["High"],
            low=row["Low"],
        )
        for index, row in data.iterrows()
    ]
    return StockPricePeriod(ticker_str, price_entries)


# TODO: Get multiple stocks at once
# TODO: Consider NaN values in response due to diff timezones?
# def get_multiple():
#     symbols = [index.symbol for index in indices]
#     data = yf.download(symbols, period="5d")
