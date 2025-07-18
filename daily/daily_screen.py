from datetime import date
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from rulebook import RULES

DOC_PATH = "docs/daily_screen"  # base path without extension

def valuation_pass(pe: float | None, ev_ebitda: float | None) -> bool:
    return (
        pe is not None and 0 < pe <= 15
    ) or (
        ev_ebitda is not None and ev_ebitda <= 8
    )

def get_company_name(tkr: str) -> str:
    try:
        info = yf.Ticker(tkr).info
        return info.get("shortName") or info.get("longName") or tkr
    except Exception:
        return tkr

records: list[list] = []

for ticker, rule in RULES.items():
    name = get_company_name(ticker)
    df = yf.download(ticker, period="500d", progress=False)
    if df.empty:
        records.append([ticker, name, None, None, None, "NoPrice", "SKIP"])
        continue

    prices = df['Close'].dropna()
    close_val = prices.iloc[-1] if not prices.empty else None
    close = round(float(close_val), 2) if close_val is not None and not pd.isna(close_val) else None
    fast = yf.Ticker(ticker).fast_info or {}
    pe = fast.get("forwardPE") or fast.get("trailingPE")
    ev_ebitda = fast.get("enterpriseToEbitda")

    if pe is None and ev_ebitda is None:
        slow = yf.Ticker(ticker).info
        pe = slow.get("forwardPE") or slow.get("trailingPE")
        ev_ebitda = slow.get("enterpriseToEbitda")

    val_ok = valuation_pass(pe, ev_ebitda)
    val_flag = "Pass" if val_ok else "Fail"

    if not val_ok:
        records.append([ticker, name, close, None, None, val_flag, "SKIP"])
        continue

    # ---------- 3. TECHNICALS ----------
    sma_len, rsi_cut = rule["sma"], rule["rsi"]
    prices = df['Close'].dropna()
    close_val = prices.iloc[-1] if not prices.empty else None
    close = round(float(close_val), 2) if close_val is not None and not pd.isna(close_val) else None
    sma_val = prices.rolling(sma_len).mean().iloc[-1]
    rsi_series = ta.rsi(prices, length=14)
    rsi_val = rsi_series.iloc[-1] if rsi_series is not None else None

    if pd.isna(sma_val) or sma_val is None or pd.isna(rsi_val) or rsi_val is None or close is None or pd.isna(close):
        signal = "SKIP"
        close_out = None
        sma_out = None
        rsi_out = None
    else:
        close_out = round(close, 2)
        sma_out = round(float(sma_val), 2)
        rsi_out = round(float(rsi_val), 1)
        if close < sma_val:
            signal = "EXIT"
        elif rsi_val <= rsi_cut:
            signal = "BUY"
        else:
            signal = "HOLD"

    records.append([
        ticker,
        name,
        close_out,
        sma_out,
        rsi_out,
        val_flag,
        signal
    ])

cols = ["Ticker", "Name", "Close", "SMA", "RSI", "Valuation", "Signal"]
table = pd.DataFrame(records, columns=cols).sort_values("Ticker")

table.to_csv(f"{DOC_PATH}.csv", index=False)

print("✅ daily screen updated", date.today())