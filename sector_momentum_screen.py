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
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Tuple

# ------------------------------------------------ #
# USER CONFIGURATION                               #
# ------------------------------------------------ #

UNIVERSE: Dict[str, str] = {
    # ---------- U.S. SPDR sector ETFs ----------
    "XLK":  "US Technology",
    "XLE":  "US Energy",
    "XLF":  "US Financials",
    "XLV":  "US Health Care",
    "XLI":  "US Industrials",
    "XLP":  "US Consumer Staples",
    "XLY":  "US Consumer Discretionary",
    "XLU":  "US Utilities",
    "XLB":  "US Materials",
    "XLRE": "US Real Estate",
    "XLC":  "US Communication Services",

    # ---------- Europe STOXX-600 sector UCITS (Xetra unless noted) ----------
    "EXV3.DE": "EU Technology",
    "EXV1.DE": "EU Banks",
    "EXV4.DE": "EU Health Care",
    "EXV7.DE": "EU Industrials",
    "EXV6.DE": "EU Consumer Staples",
    "CDIS.L":  "EU Consumer Discretionary",   # SPDR MSCI Europe Cons-Disc (London)
    "EXV5.DE": "EU Utilities",
    "EXV8.DE": "EU Materials",
    "EXV2.DE": "EU Energy",
    "EXV9.DE": "EU Real Estate",
    "EXV0.DE": "EU Communication Services",  # note the zero

    # ---------- Asia proxies ----------
    "XCTE.L": "China Technology",
    "KWEB":   "China Internet",
    "JPJP.L": "MSCI Japan Broad",
    
    # ---------- Bond asset for risk-off indicator ----------
    "AGG": "US Aggregate Bond"
}

BOND_TICKER: str = "AGG" 

# ------------------------------------------------ #
# Helper functions                                 #
# ------------------------------------------------ #

def get_price_data(tickers: List[str], period: str = '2y') -> pd.DataFrame:
    """Download historical price data for a list of tickers."""
    try:
        data = yf.download(tickers, period=period, auto_adjust=True)['Close']
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
        return data.ffill()
    except Exception as e:
        print(f"Error downloading price data: {e}")
        return pd.DataFrame()

def calculate_momentum(prices: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """Calculate momentum and 12-month returns."""
    returns_1m = prices.pct_change(periods=21)
    returns_3m = prices.pct_change(periods=63)
    returns_6m = prices.pct_change(periods=126)
    returns_12m = prices.pct_change(periods=252)
    
    momentum = (returns_1m + returns_3m + returns_6m + returns_12m).iloc[-1]
    return12m = returns_12m.iloc[-1]
    
    return momentum.dropna(), return12m.dropna()

def momentum_screen() -> pd.DataFrame:
    """Perform the momentum screen and return ranked results."""
    tickers = list(UNIVERSE.keys())
    prices = get_price_data(tickers)
    
    if prices.empty or len(prices) < 260:
        print("Not enough price data to perform screen.")
        return pd.DataFrame(columns=['Ticker', 'MomentumScore', 'Return12m'])

    momentum, return12m = calculate_momentum(prices)
    
    results = pd.DataFrame({'MomentumScore': momentum, 'Return12m': return12m}).reset_index()
    results.rename(columns={'index': 'Ticker'}, inplace=True)
    
    bond_return_12m_series = results[results['Ticker'] == BOND_TICKER]['Return12m']
    if bond_return_12m_series.empty:
        print(f"Could not find 12m return for bond ticker {BOND_TICKER}.")
        bond_return_12m = 0.0
    else:
        bond_return_12m = bond_return_12m_series.iloc[0]

    results = results[results['Return12m'] > bond_return_12m]
    results = results[results['Ticker'] != BOND_TICKER]

    return results.sort_values(by='MomentumScore', ascending=False)

def main() -> None:
    """Main function to run the screen and save results."""
    today = datetime.today()
    print(f"Running momentum screen for {today.date()}...")
    
    ranked_results = momentum_screen()
    
    if ranked_results.empty:
        print("No assets passed the screen. No results to save.")
        pd.DataFrame(columns=['Ticker', 'MomentumScore', 'Return12m']).to_csv('momentum_scores.csv', index=False)
        return

    print("\n🏆 Top 3 Momentum Winners:")
    for i, row in ranked_results.head(3).iterrows():
        ticker: str = row['Ticker']
        score: float = row['MomentumScore']
        print(f"{i+1}. {UNIVERSE.get(ticker, ticker)} ({ticker}): {score:.4f}")

    ranked_results.to_csv('momentum_scores.csv', index=False)
    print("\n💾 Full results saved to momentum_scores.csv")

if __name__ == "__main__":
    main()
