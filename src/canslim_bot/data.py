import pandas as pd
import yfinance as yf
from typing import Any

def fetch_daily(ticker: str) -> pd.DataFrame:
    """
    Fetch 6 months of daily OHLCV data for a given ticker using yfinance.

    Args:
        ticker (str): Stock ticker symbol.

    Returns:
        pd.DataFrame: DataFrame with daily OHLCV data.
    """
    df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False)
    return df

def to_weekly(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Resample daily OHLCV data to weekly (Friday) OHLCV.

    Args:
        df_daily (pd.DataFrame): Daily OHLCV DataFrame.

    Returns:
        pd.DataFrame: Weekly OHLCV DataFrame (W-FRI).
    """
    ohlc_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }
    df_weekly = df_daily.resample('W-FRI').agg(ohlc_dict).dropna()
    return df_weekly

def get_moving_average(series: pd.Series, window: int) -> pd.Series:
    """
    Calculate the moving average for a given series and window.

    Args:
        series (pd.Series): Input data series.
        window (int): Window size for moving average.

    Returns:
        pd.Series: Moving average series.
    """
    return series.rolling(window=window, min_periods=1).mean()

def rs_rank(series: pd.Series, window: int) -> float:
    """
    Calculate the percentile rank of the last value in a rolling window.

    Args:
        series (pd.Series): Input data series.
        window (int): Window size for ranking.

    Returns:
        float: Percentile rank (0-100).
    """
    if len(series) < window:
        raise ValueError("Series length is less than the window size.")
    window_series = series[-window:]
    rank = (window_series.rank(pct=True).iloc[-1]) * 100
    return rank

def market_uptrend() -> bool:
    """
    Determine if the S&P 500 (^GSPC) is in an uptrend (close > 50-day moving average).

    Returns:
        bool: True if uptrend, False otherwise.
    """
    df = fetch_daily("^GSPC")
    close = df["Close"]
    ma50 = get_moving_average(close, 50)
    return bool(close.iloc[-1] > ma50.iloc[-1]) 