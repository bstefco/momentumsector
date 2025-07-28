import pandas as pd
import yfinance as yf
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def fetch_daily(ticker: str) -> pd.DataFrame:
    """
    Fetch 6 months of daily OHLCV data for a given ticker using yfinance.

    Args:
        ticker (str): Stock ticker symbol.

    Returns:
        pd.DataFrame: DataFrame with daily OHLCV data.
    """
    try:
        df = yf.Ticker(ticker).history(period="7mo", interval="1d", auto_adjust=True)  # Increased to 7mo to ensure 126+ days
        if df.empty:
            logger.warning(f"No data returned for ticker {ticker}.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch data for {ticker}: {e}")
        return pd.DataFrame()

def to_weekly(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Resample daily OHLCV data to weekly (Friday) OHLCV.

    Args:
        df_daily (pd.DataFrame): Daily OHLCV DataFrame.

    Returns:
        pd.DataFrame: Weekly OHLCV DataFrame (W-FRI).
    """
    if df_daily.empty:
        logger.warning("Input DataFrame is empty in to_weekly().")
        return pd.DataFrame()
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
    if series.empty:
        logger.warning("Input series is empty in get_moving_average().")
        return pd.Series(dtype=float)
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
        logger.error("Series length is less than the window size in rs_rank().")
        raise ValueError("Series length is less than the window size.")
    window_series = series[-window:]
    rank = (window_series.rank(pct=True).iloc[-1]) * 100
    return rank

def _fetch_sp500() -> pd.Series:
    """
    Try to fetch S&P 500 close prices from multiple sources (^GSPC, ^SPX, SPY).
    Returns the first available adjusted close series.

    Returns:
        pd.Series: Adjusted close prices for S&P 500 or ETF.
    Raises:
        RuntimeError: If no data is available from any source.
    """
    for symbol in ("^GSPC", "^SPX", "SPY"):
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False, auto_adjust=True)
            if not df.empty:
                return df['Close']
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
    raise RuntimeError("S&P 500 price unavailable from all sources.")

def market_uptrend() -> bool:
    """
    Determine if the S&P 500 is in an uptrend (close > 50-day moving average).
    Returns False if data is unavailable.

    Returns:
        bool: True if uptrend, False otherwise.
    """
    try:
        close = _fetch_sp500()
    except Exception as e:
        logger.warning(f"Could not fetch S&P 500 data for market trend check: {e}. Assuming not in uptrend.")
        return False
    ma50 = get_moving_average(close, 50)
    if close.empty or ma50.empty:
        logger.warning("S&P 500 close or MA50 data missing. Assuming not in uptrend.")
        return False
    # Extract scalar values for comparison
    last_close = float(close.iloc[-1].iloc[0])
    last_ma50 = float(ma50.iloc[-1].iloc[0])
    return last_close > last_ma50 