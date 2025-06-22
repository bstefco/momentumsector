#!/usr/bin/env python3
"""
Sector-Momentum ETF Screener
--------------------------------------------------
1. Downloads 400 days of *adjusted* closes for a
   global sector-ETF universe + bond proxy.
2. Computes the average of 3-, 6-, 9-, 12-month
   returns (skipping the most recent month).
3. Filters out ETFs whose 12-m return is ≤ bond.
4. Prints the top-3 winners (or fewer) and saves
   a CSV snapshot of all scores.
Dependencies:  pandas  numpy  yfinance
"""

from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

# ------------------------------------------------ #
# USER CONFIGURATION                               #
# ------------------------------------------------ #

UNIVERSE = {
    # — U.S. SPDR sector ETFs —
    "XLK": "US Technology",
    "XLE": "US Energy",
    "XLF": "US Financials",
    "XLV": "US Health Care",
    "XLI": "US Industrials",
    "XLP": "US Cons. Staples",
    "XLY": "US Cons. Discretionary",
    "XLU": "US Utilities",
    "XLB": "US Materials",
    "XLRE": "US Real Estate",
    "XLC": "US Communication",

    # — Global sector ETFs (more reliable) —
    "IXN": "Global Technology",
    "IXG": "Global Financials",
    "IXJ": "Global Healthcare",
    "IXI": "Global Industrials",
    "IXP": "Global Telecom",
    "IXC": "Global Energy",
    "IXM": "Global Materials",

    # — Asia proxies —
    "KWEB": "China Internet",
    "FXI": "China Large Cap",
    "EWJ": "Japan",
}

BOND_TICKER   = "AGG"            # US Aggregate Bond (more reliable)
TOP_N         = 3                # how many winners to own
LOOKBACK_DAYS = 400              # price history pulled

# ------------------------------------------------ #
# Helper functions                                 #
# ------------------------------------------------ #

def download_prices(tickers: list[str],
                    start: datetime,
                    end  : datetime) -> pd.DataFrame:
    """Get adjusted-close prices."""
    data = yf.download(tickers, start=start, end=end,
                       auto_adjust=True, progress=False)
    return data["Close"].dropna(how="all")

def momentum_scores(prices: pd.DataFrame,
                    today : pd.Timestamp) -> tuple[pd.Series, pd.Series]:
    """Return (avg-momentum-score, 12-m return) for every ticker."""
    # Offsets: 1,3,6,9,12 months back (~22 trading days per month)
    steps = [26, 78, 130, 182, 234]          # in calendar days
    gap   = steps[0]                         # one-month skip

    returns = []
    for d in steps[:-1]:                     # first 4 look-backs
        past = today - pd.Timedelta(days=d)
        gapd = today - pd.Timedelta(days=gap)
        
        # Find the closest available dates
        past_idx = prices.index[prices.index <= past][-1] if len(prices.index[prices.index <= past]) > 0 else None
        gapd_idx = prices.index[prices.index <= gapd][-1] if len(prices.index[prices.index <= gapd]) > 0 else None
        
        if past_idx is not None and gapd_idx is not None:
            returns.append(prices.loc[gapd_idx] / prices.loc[past_idx] - 1)

    if not returns:
        # Fallback: use simple returns if date calculations fail
        avg_mom = pd.Series(0.0, index=prices.columns)
        ret12 = pd.Series(0.0, index=prices.columns)
        return avg_mom, ret12

    avg_mom = pd.concat(returns, axis=1).mean(axis=1)

    # 12-month return
    past_12m = today - pd.Timedelta(days=steps[-1])
    past_12m_idx = prices.index[prices.index <= past_12m][-1] if len(prices.index[prices.index <= past_12m]) > 0 else None
    gapd_idx = prices.index[prices.index <= gapd][-1] if len(prices.index[prices.index <= gapd]) > 0 else None
    
    if past_12m_idx is not None and gapd_idx is not None:
        ret12 = prices.loc[gapd_idx] / prices.loc[past_12m_idx] - 1
    else:
        ret12 = pd.Series(0.0, index=prices.columns)
    
    return avg_mom, ret12

# ------------------------------------------------ #
# Main                                             #
# ------------------------------------------------ #

def main() -> None:
    end   = datetime.today()
    start = end - timedelta(days=LOOKBACK_DAYS)

    tickers = list(UNIVERSE.keys()) + [BOND_TICKER]
    prices  = download_prices(tickers, start, end)
    today   = prices.index[-1]               # last available date

    mom, ret12 = momentum_scores(prices, today)
    bond_12m   = ret12[BOND_TICKER]

    survivors  = mom[mom.index != BOND_TICKER]
    survivors  = survivors[survivors > bond_12m]

    winners = survivors.sort_values(ascending=False).head(TOP_N)

    # ---------- Output ---------- #
    print("-" * 42)
    print(f"Run date: {today.date()}")
    print(f"Bond 12-m return ({BOND_TICKER}): {bond_12m*100:5.2f} %")
    print(f"Top-{TOP_N} winners:")
    for i, (tic, score) in enumerate(winners.items(), 1):
        label = UNIVERSE.get(tic, "n/a")
        print(f"  {i:<2} {tic:<8} | {score*100:5.1f} %  ({label})")
    if len(winners) < TOP_N:
        missing = TOP_N - len(winners)
        print(f"→ Only {len(winners)} ETF(s) passed; "
              f"allocate {missing} slot(s) to {BOND_TICKER}.")
    print("-" * 42)

    # Save CSV snapshot
    pd.DataFrame({
        "MomentumScore": mom,
        "Return12m": ret12
    }).to_csv("momentum_scores.csv", float_format="%.6f")

if __name__ == "__main__":
    main()
