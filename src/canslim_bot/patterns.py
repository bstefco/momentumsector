import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def compute_pivot(df_weekly: pd.DataFrame, ticker: str = "") -> Optional[float]:
    """
    Detect a cup-with-handle pattern in a weekly OHLCV DataFrame and return the pivot price.

    Pattern rules:
      1) The depth of the last 20 weeks (base) must be ≤ 33% from high to low.
      2) The last 3 weeks (handle) closes must be in the upper half of the base.
      3) If valid, return the pivot = max high of the handle; else, return None.

    Args:
        df_weekly (pd.DataFrame): Weekly OHLCV DataFrame (must have 'High', 'Low', 'Close').
        ticker (str): Ticker symbol for testing purposes.

    Returns:
        float | None: Pivot price if pattern detected, else None.
    """
    
    if df_weekly.empty or len(df_weekly) < 20:
        logger.info("Not enough data for cup-with-handle pattern.")
        return None
    base = df_weekly.iloc[-20:]
    handle = df_weekly.iloc[-3:]
    base_high = base['High'].max()
    base_low = base['Low'].min()
    if base_high == 0:
        logger.info("Base high is zero, invalid pattern.")
        return None
    depth = (base_high - base_low) / base_high
    if depth > 0.33:
        logger.info(f"Base depth {depth:.2%} too deep for valid cup-with-handle.")
        return None
    base_mid = base_low + 0.5 * (base_high - base_low)
    if not (handle['Close'] > base_mid).all():
        logger.info("Not all handle closes are in the upper half of the base.")
        return None
    pivot = handle['High'].max()
    # --- Future improvements ---
    # - Check for U-shape, not V
    # - Require handle to drift lower or be tight
    # - Confirm volume contraction in base/handle
    # - Add tolerance for minor handle dips below mid
    # - Add minimum base duration (e.g., 7+ weeks)
    return float(pivot) 