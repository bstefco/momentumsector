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

    close = round(df.Close.iloc[-1], 2)
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

    sma_len = rule["sma"]
    rsi_cut = rule["rsi"]
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
        ticker, name, close, round(sma, 2), round(rsi, 1), val_flag, signal
    ])

cols = ["Ticker", "Name", "Close", "SMA", "RSI", "Valuation", "Signal"]
table = pd.DataFrame(records, columns=cols).sort_values("Ticker")

table.to_html(
    f"{DOC_PATH}.html",
    index=False,
    justify="center",
    border=0,
    classes="datatable",
)
table.to_csv(f"{DOC_PATH}.csv", index=False)

print("✅ daily screen updated", date.today())