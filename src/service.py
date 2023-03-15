import requests
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

ENDPOINT = 'https://www.alphavantage.co/query'


# Client for alpha vantage class
class AlphaVantageClient:
    pass


class StockSummary:
    def __init__(self, symbol: str, latest_close: float, percent_change_5d: float):
        self.symbol = symbol
        self.latest_close = latest_close 
        self.percent_change_5d = percent_change_5d

    # def __str__(self):
    #     return f"{self.symbol}: {self.percent_change_5d:.2f}%"

# TODO: Consider NaN values
# def get_multi():
#     symbols = [index.symbol for index in indices]
#     data = yf.download(symbols, period="5d")
#     percent_changes = (data['Close'].iloc[-2] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
#     print(percent_changes)
#     exit()
#     for index, percent_change in zip(indices, percent_changes):
#         index.percent_change_5d = percent_change
    
#     for index in indices:
#         index.percent_change_5d = percent_changes[index.symbol]

# XXX: Async version?
# Get weekly summary for a stock using yfinance
def get_weekly_summary(symbol: str):
    ticker = yf.Ticker(symbol)
    # Request trading week = 5 days
    data = ticker.history(period="5d") 


    price_change: float = (data['Close'][-1] - data['Close'][0])
    percent_change: float = price_change / data['Close'][0] * 100 

    return StockSummary(symbol, data['Close'][0], percent_change)

