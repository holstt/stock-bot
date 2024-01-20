from io import BytesIO
from locale import currency
import logging
from datetime import datetime
from typing import NamedTuple
import discord
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pandas import DataFrame, Series
from typeguard import check_type
import pandas as pd

import yfinance as yf

from src.models import PriceEntry, StockPricePeriod

logger = logging.getLogger(__name__)


class ChartResult(NamedTuple):
    buffer: BytesIO | None = None
    embed: discord.Embed | None = None
    error_msg: str = ""


# ticker.history parameters:
# period : str
#     Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
#     Either Use period parameter or use start and end
# interval : str
#     Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
#     Intraday data cannot extend last 60 days
# start: str
#     Download start date string (YYYY-MM-DD) or _datetime.
#     Default is 1900-01-01
# end: str
#     Download end date string (YYYY-MM-DD) or _datetime.
#     Default is now


# TODO: Separate responsibilities
def get_chart_message(ticker_str: str):
    logger.info(f"Creating chart message for ticker: {ticker_str}")
    ticker = yf.Ticker(ticker_str)

    logger.info("Fetching data for ticker: " + ticker_str)
    data: DataFrame = ticker.history(period="1y")
    if data.empty:
        return ChartResult(
            error_msg=f"Could not fetch data for {ticker_str}, ensure ticker is valid"
        )
    logger.info(f"Ticker fetched: {ticker_str}")

    basic_info = ticker.fast_info
    title, description = _create_message(ticker_str, basic_info, data)  # type: ignore

    embed = discord.Embed(title=title, description=description)

    currency = basic_info["currency"]
    buffer = _create_plot(ticker_str, data, currency)

    return ChartResult(buffer=buffer, embed=embed)


# Create message with some stats about the ticker
def _create_message(ticker_str: str, basic_info: dict, data: DataFrame):
    market_cap = basic_info["marketCap"]
    market_cap_str = f"{market_cap:,}"
    if market_cap >= 1_000_000_000:
        market_cap_str = f"{market_cap / 1_000_000_000:,.0f}B"
    elif market_cap >= 1_000_000:
        market_cap_str = f"{market_cap / 1_000_000:,.0f}M"

    currency = basic_info["currency"]
    quote_type = basic_info["quote_type"]
    closes = data["Close"]
    # Get total return for the year in percent
    period_return = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
    #  Get return for the day in percent
    day_return = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100

    # TODO:
    # Get the std. deviation
    # std = closes.std()
    # Get the relative coefficient of variation (CV) X: Should it be based on the moving std?
    # cv = std / closes.mean()

    # Get max drawdown
    # cummax = closes.cummax()
    # drawdown = closes - cummax
    # max_drawdown = drawdown.min()

    # daily_returns = closes.pct_change()

    # Get skewness
    # Skewness (measures the asymmetry of the return distribution):
    # Stock A: 0.14 (a positive skew indicates more frequent small losses and a few large gains)
    # Stock B: -0.11 (a negative skew indicates more frequent small gains and a few large losses)
    # skewness = daily_returns.skew()

    # Get kurtosis
    # measures the 'tailedness' of the distribution
    # kurtosis = daily_returns.kurtosis()

    # Value at Risk (VaR) at 5%
    # measures the maximum expected loss over a given time period at a certain confidence level)
    # implies a 5% chance of losing more than 3.25% of value in a day
    # var_95 = daily_returns.quantile(0.05)

    # Conditional Value at Risk (CVaR) at 5% (measures the expected loss exceeding the VaR). (average loss in the worst 5% of cases)
    # cvar_95 = daily_returns[closes <= var_95].mean()

    title = f"{ticker_str.upper()} ({quote_type})"
    description = ""
    # Return, 1d
    description += f"\n{_get_emoji(day_return)}**Return, 1d**: {day_return:.2f} %"
    description += (
        f"\n{_get_emoji(period_return)}**Return, period**: {period_return:.2f} %"
    )
    description += f"\n**Market Cap**: {market_cap_str} {currency}"
    # description += f"\n**CV**: {cv:.2f}"
    # description += f"\n**nMax Drawdown**: {max_drawdown:.2f}"
    # description += f"\n**Skewness**: {skewness:.2f}"
    # description += f"\n**Kurtosis**: {kurtosis:.2f}"
    # description += f"\n**VaR 95%**: {var_95 * 100:.2f}%"
    # description += f"\n**CVaR 95%**: {cvar_95 * 100:.2f}%"

    return title, description


def _get_emoji(value: float) -> str:
    if value > 0:
        return "🟢"
    elif value < 0:
        return "🔴"
    else:
        return "⚪"


def _create_plot(ticker_str: str, data: DataFrame, currency: str) -> BytesIO:
    logger.info(f"Creating plot for ticker: {ticker_str}")
    close_series = data["Close"]

    ax1 = close_series.plot(figsize=(7, 5))
    ax1.title.set_text(f"{ticker_str.upper()} - 1Y Chart")
    ax1.set_ylabel(f"Price ({currency})")
    ax1.set_xlabel("")

    # Insert markers at the all time highs and lows
    add_high_low_markers(ax1, close_series)

    # Highlight the last week (starting from monday) with a semi-transparent rectangle
    last_weekday = close_series.index[-1].weekday()  # type: ignore
    last_monday = close_series.index[-1] - pd.Timedelta(days=last_weekday)  # type: ignore
    next_monday = last_monday + pd.Timedelta(days=7)
    ax1.axvspan(last_monday, next_monday, alpha=0.2, color="grey")

    ax1.legend(loc="upper left")
    ax1.grid(True)
    fig: Figure = check_type(ax1.get_figure(), Figure)
    fig.tight_layout()

    # Save as IO buffer
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)

    # Clear the figure
    fig.clf()

    logger.info(f"Plot created for ticker: {ticker_str}")
    return buffer


def add_high_low_markers(ax1: Axes, close_series: Series):
    all_time_high: float = close_series.max()
    all_time_low: float = close_series.min()

    # Get high and low dates
    high_date = close_series.idxmax()
    low_date = close_series.idxmin()

    # Expanding the y-axis limits to provide more space for annotations
    y_min, y_max = ax1.get_ylim()
    y_range = y_max - y_min

    # Dynamic padding for the y-axis limits
    y_padding = 0.10
    ax1.set_ylim(y_min - y_padding * y_range, y_max + y_padding * y_range)

    # Plotting special markers towards the edges for the actual high and low points
    marker_offset = 0.03 * y_range
    marker_size = 7

    ax1.scatter(
        high_date,
        all_time_high + marker_offset,
        marker="^",
        color="green",
        label="Highest",
    )  # Special marker for high

    ax1.scatter(
        low_date,
        all_time_low - marker_offset,
        marker="v",
        color="red",
        label="Lowest",
    )  # Special marker for low

    # Annotating the high and low markers with their respective prices at the offset positions
    ax1.annotate(
        f"{all_time_high:.2f}",
        (high_date, all_time_high + marker_offset),  # type: ignore
        textcoords="offset points",
        xytext=(0, 10),
        ha="center",
        color="green",
    )
    ax1.annotate(
        f"{all_time_low:.2f}",
        (low_date, all_time_low - marker_offset),  # type: ignore
        textcoords="offset points",
        xytext=(0, -15),
        ha="center",
        color="red",
    )


# Get weekly summary for a stock using yfinance
def get_5d_summary(ticker_str: str) -> StockPricePeriod:
    logger.debug(f"Getting data for {ticker_str}...")
    ticker = yf.Ticker(ticker_str)
    # NB: Trading week is 5 days. Only trading days are included in yfinance data
    data: DataFrame = ticker.history(period="5d")

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
