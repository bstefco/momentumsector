import os
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from rulebook import RULES

os.makedirs(os.path.join("..", "docs"), exist_ok=True)

# Output paths
HTML_PATH = os.path.join("..", "docs", "daily_screen.html")
CSV_PATH = os.path.join("..", "docs", "daily_screen.csv")

# Helper for valuation pass
VALUATION_PE = 15
VALUATION_EV_EBITDA = 8

results = []

for ticker, params in RULES.items():
    try:
        yf_ticker = yf.Ticker(ticker)
        # Get fast_info for valuation
        fast_info = yf_ticker.fast_info
        pe = fast_info.get("forwardPE")
        ev_ebitda = fast_info.get("evToEbitda")
        val_pass = False
        if pe is not None and pe <= VALUATION_PE:
            val_pass = True
        if ev_ebitda is not None and ev_ebitda <= VALUATION_EV_EBITDA:
            val_pass = True
        # Get last 100 trading days OHLCV
        df = yf_ticker.history(period="130d").tail(100)
        if df.empty:
            results.append({"Ticker": ticker, "Valuation": "No Data", "Signal": "NO DATA"})
            continue
        close = df["Close"]
        if val_pass:
            sma_len = params["sma"]
            rsi_cut = params["rsi"]
            df["SMA"] = close.rolling(sma_len).mean()
            df["RSI"] = ta.rsi(close, length=14)
            last = df.iloc[-1]
            if last["Close"] < last["SMA"]:
                signal = "EXIT"
            elif last["Close"] > last["SMA"] and last["RSI"] <= rsi_cut:
                signal = "BUY"
            else:
                signal = "HOLD"
            results.append({
                "Ticker": ticker,
                "Valuation": "PASS",
                "Close": round(last["Close"], 2),
                "SMA": round(last["SMA"], 2),
                "RSI": round(last["RSI"], 2),
                "Signal": signal
            })
        else:
            results.append({"Ticker": ticker, "Valuation": "FAIL", "Signal": "NO TRADE"})
    except Exception as e:
        results.append({"Ticker": ticker, "Valuation": "ERROR", "Signal": str(e)})

# Create DataFrame
results_df = pd.DataFrame(results)

print("Results DataFrame:")
print(results_df)

print("Writing CSV to", CSV_PATH)
results_df.to_csv(CSV_PATH, index=False)
