import os
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from rulebook import RULES

os.makedirs("docs", exist_ok=True)

HTML_PATH = os.path.join("docs", "daily_screen.html")
CSV_PATH = os.path.join("docs", "daily_screen.csv")

cols = ["Ticker","Close","SMA","RSI","Valuation","Signal"]
records = []

for ticker, rule in RULES.items():
    # ---------- 1. PRICE DATA ----------
    df = yf.download(ticker, period="500d", progress=False)
    if df.empty:
        records.append([ticker, None, None, None, "NoPrice", "SKIP"])
        continue
    close = round(df.Close.iloc[-1], 2)

    # ---------- 2. VALUATION ----------
    info = yf.Ticker(ticker).fast_info or {}
    pe = info.get("forwardPE") or info.get("trailingPE")
    ev_ebitda = info.get("enterpriseToEbitda") or info.get("evToEbitda")

    # fallback – slower but richer
    if pe is None and ev_ebitda is None:
        slow = yf.Ticker(ticker).info
        pe        = slow.get("forwardPE") or slow.get("trailingPE")
        ev_ebitda = slow.get("enterpriseToEbitda") or slow.get("evToEbitda")

    val_ok = (
        (pe and 0 < pe <= 15) or
        (ev_ebitda and ev_ebitda <= 8)
    )
    val_flag = "Pass" if val_ok else "Fail"

    if not val_ok:
        records.append([ticker, close, None, None, val_flag, "SKIP"])
        continue

    # ---------- 3. TECHNICALS ----------
    sma_len, rsi_cut = rule["sma"], rule["rsi"]
    sma = df.Close.rolling(sma_len).mean().iloc[-1]
    rsi = ta.rsi(df.Close, length=14).iloc[-1]

    if pd.isna(sma) or pd.isna(rsi):
        signal = "SKIP"
    elif close < sma:
        signal = "EXIT"
    elif rsi <= rsi_cut:
        signal = "BUY"
    else:
        signal = "HOLD"

    records.append([
        ticker, close,
        round(sma, 2), round(rsi, 1),
        val_flag, signal
    ])

results_df = pd.DataFrame(records, columns=cols)

print("Results DataFrame:")
print(results_df)

print("Writing CSV to", CSV_PATH)
results_df.to_csv(CSV_PATH, index=False)

print("Writing HTML to", HTML_PATH)
results_df.to_html(HTML_PATH, index=False)