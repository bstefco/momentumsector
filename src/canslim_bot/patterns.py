import pandas as pd
from typing import Optional

def compute_pivot(df_weekly: pd.DataFrame) -> Optional[float]:
    """
    Detect a cup-with-handle pattern in a weekly OHLCV DataFrame and return the pivot price.

    Pattern rules:
      1) The depth of the last 20 weeks (base) must be ≤ 33% from high to low.
      2) The last 3 weeks (handle) closes must be in the upper half of the base.
      3) If valid, return the pivot = max high of the handle; else, return None.

    Args:
        df_weekly (pd.DataFrame): Weekly OHLCV DataFrame (must have 'High', 'Low', 'Close').

    Returns:
        float | None: Pivot price if pattern detected, else None.
    """
    # --- Step 1: Check if there are at least 20 weeks ---
    if len(df_weekly) < 20:
        # Not enough data for pattern detection
        return None

    # --- Step 2: Define base and handle ---
    base = df_weekly.iloc[-20:]
    handle = df_weekly.iloc[-3:]

    # --- Step 3: Calculate base depth ---
    base_high = base['High'].max()
    base_low = base['Low'].min()
    if base_high == 0:
        # Prevent division by zero
        return None
    depth = (base_high - base_low) / base_high
    if depth > 0.33:
        # Base is too deep for a valid cup-with-handle
        return None

    # --- Step 4: Check handle closes in upper half of base ---
    base_mid = base_low + 0.5 * (base_high - base_low)
    if not (handle['Close'] > base_mid).all():
        # Not all handle closes are in the upper half
        return None

    # --- Step 5: Pivot is the max high of the handle ---
    pivot = handle['High'].max()
    return float(pivot)

    # --- Notes for future improvement ---
    # - Add checks for proper cup shape (U, not V)
    # - Require handle to drift lower or be tight
    # - Confirm volume contraction in base and handle
    # - Add tolerance for minor handle dips below mid
    # - Add minimum base duration (e.g., 7+ weeks) 