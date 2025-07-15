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
    "EXH1.DE": "EU Oil & Gas",                # <-- changed from EXV0.DE or EXV2.DE
    "EXV9.DE": "EU Real Estate",
    "EXV2.DE": "EU Communication Services",   # <-- ensure correct sector

    # ---------- Asia proxies ----------
    "XCTE.L": "China Technology",
    "KWEB":   "China Internet",
    "JPJP.L": "MSCI Japan Broad",
    
    # ---------- Bond asset for risk-off indicator ----------
    "SUAG.L": "EU Aggregate Bond"   # iShares EUR Agg Bond UCITS
}

BOND_TICKER: str = "SUAG.L"

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

def momentum_scores(prices: pd.DataFrame,
                    today : pd.Timestamp) -> tuple[pd.Series, pd.Series]:
    """
    Return (avg-momentum-score, 12-m return) for every ticker.
    Uses *trading-day* shifts so weekend / holiday gaps do not inflate ratios.
    """
    # Trading-day offsets ≈ 1, 3, 6, 9, 12 months
    bd_offsets = [22, 66, 132, 198, 264]   # 22 ≈ 1 month
    
    # Use pandas shift which respects the index (trading days)
    # The index should already be business days from yfinance data
    ref = prices.shift(bd_offsets[0])      # t-1 month (skip most-recent month)

    # Calculate momentum for each ticker individually
    tickers = prices.columns
    momentum_scores = {}
    return12m_scores = {}
    
    for ticker in tickers:
        # Calculate momentum parts for each lookback period
        parts = []
        for bd in bd_offsets[1:]:              # 3,6,9,12 m
            past = prices[ticker].shift(bd)
            part = ref[ticker] / past - 1
            parts.append(part)
        
        # Average across lookback periods
        avg_momentum = pd.concat(parts, axis=1).mean(axis=1)
        ret12 = ref[ticker] / prices[ticker].shift(bd_offsets[-1]) - 1
        
        # Get latest values
        momentum_scores[ticker] = avg_momentum.iloc[-1]
        return12m_scores[ticker] = ret12.iloc[-1]
    
    return pd.Series(momentum_scores), pd.Series(return12m_scores)

def momentum_screen() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform the momentum screen.
    Returns a tuple of (ranked_results, bond_data).
    """
    tickers = list(UNIVERSE.keys())
    prices = get_price_data(tickers)
    
    if prices.empty or len(prices) < 260:
        print("Not enough price data to perform screen.")
        return pd.DataFrame(columns=['Ticker', 'MomentumScore', 'Return12m']), pd.DataFrame()

    today = pd.Timestamp.now()
    avg_mom, ret12 = momentum_scores(prices, today)
    
    # Create DataFrame from the Series objects
    all_results = pd.DataFrame({'MomentumScore': avg_mom, 'Return12m': ret12}).reset_index()
    all_results.rename(columns={'index': 'Ticker'}, inplace=True)
    
    bond_data = all_results[all_results['Ticker'] == BOND_TICKER].copy()
    
    if bond_data.empty:
        print(f"Could not find data for bond ticker {BOND_TICKER}.")
        bond_return_12m = 0.0
    else:
        bond_return_12m = bond_data['Return12m'].iloc[0]

    results = all_results[all_results['Return12m'] > bond_return_12m]
    results = results[results['Ticker'] != BOND_TICKER]

    return results.sort_values(by='MomentumScore', ascending=False), bond_data

def main() -> None:
    """Main function to run the screen and save results."""
    today = datetime.today()
    print(f"Running momentum screen for {today.date()}...")
    
    ranked_results, bond_data = momentum_screen()
    
    if ranked_results.empty:
        print("No assets passed the screen. No results to save.")
        pd.DataFrame(columns=['Ticker', 'MomentumScore', 'Return12m']).to_csv('momentum_scores.csv', index=False)
        # Still save bond data if it exists
        if not bond_data.empty:
            bond_data.to_json("momentum_scores.json", orient="records", indent=2)
        return

    print("\n🏆 Top 3 Momentum Winners:")
    for i, row in ranked_results.head(3).iterrows():
        ticker: str = row['Ticker']
        score: float = row['MomentumScore']
        print(f"{i+1}. {UNIVERSE.get(ticker, ticker)} ({ticker}): {score:.4f}")

    # Get all tickers data (not just winners)
    tickers = list(UNIVERSE.keys())
    prices = get_price_data(tickers)
    
    if not prices.empty and len(prices) >= 260:
        avg_mom, ret12 = momentum_scores(prices, pd.Timestamp.now())
        
        # Extract latest values for all tickers
        momentum = avg_mom.iloc[-1]
        return12m = ret12.iloc[-1]
        
        all_results = pd.DataFrame({'MomentumScore': avg_mom, 'Return12m': ret12}).reset_index()
        all_results.rename(columns={'index': 'Ticker'}, inplace=True)
        
        # Save to CSV - ALL tickers (not just winners)
        all_results.to_csv('momentum_scores.csv', index=False)
        print("\n💾 All results saved to momentum_scores.csv")

        # also export JSON for the dashboard - include bond data
        results_for_json = pd.concat([all_results, bond_data], ignore_index=True)
        results_for_json.to_json("momentum_scores.json", orient="records", indent=2)
    else:
        # Fallback to just winners if we can't get all data
        ranked_results.to_csv('momentum_scores.csv', index=False)
        print("\n💾 Winners saved to momentum_scores.csv")
        results_for_json = pd.concat([ranked_results, bond_data], ignore_index=True)
        results_for_json.to_json("momentum_scores.json", orient="records", indent=2)

if __name__ == "__main__":
    main()
