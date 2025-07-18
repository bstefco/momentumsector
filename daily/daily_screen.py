import pandas as pd, yfinance as yf, pandas_ta as ta, pathlib, sys
from datetime import date

# ensure rulebook import works no matter where script is run
sys.path.append(str(pathlib.Path(__file__).parent))
from rulebook import RULES

def valuation_pass(info: dict) -> bool:
    pe = info.get("forwardPE") or info.get("trailingPE")
    ev = info.get("enterpriseToEbitda")
    return (
        (pe and 0 < pe <= 25) or      # raised from 15 to 25
        (ev and ev <= 12)             # raised from 8 to 12
    )

def get_company_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or ticker
    except Exception:
        return ticker

def safe_round(val, ndigits):
    return round(float(val), ndigits) if val is not None else "—"

records = []
for ticker, rule in RULES.items():
    name = get_company_name(ticker)
    df = yf.download(ticker, period="1000d", progress=False)["Close"].dropna()
    print(f"{ticker}: {len(df)} closing prices")
    if df.empty:
        records.append([ticker, name, "—", "—", "—", "NoPrice", "SKIP"])
        continue

    close = float(df.iloc[-1])

    # valuation ---------------------
    fast = yf.Ticker(ticker).fast_info or {}
    val_ok = valuation_pass(fast) or valuation_pass(yf.Ticker(ticker).info)
    val_flag = "Pass" if val_ok else "Fail"
    if not val_ok:
        records.append([ticker, name, safe_round(close,2), "—", "—", val_flag, "SKIP"])
        continue

    # 3-d. Technical indicators -------------------------------------------
    sma_len, rsi_cut = rule["sma"], rule["rsi"]

    # --- SMA: mean of last `sma_len` valid closes
    sma_val = float(df.tail(sma_len).mean()) if len(df) >= sma_len else None

    # --- RSI: pandas_ta with extra ffill to kill NaNs
    rsi_series = ta.rsi(df, length=14, fillna=True).ffill()
    rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None

    if sma_val is None or rsi_val is None:
        signal = "SKIP"
    elif close < sma_val:
        signal = "EXIT"
    elif rsi_val <= rsi_cut:
        signal = "BUY"
    else:
        signal = "HOLD"

    records.append([
        ticker, name,
        round(close, 2),
        round(sma_val, 2) if sma_val else "—",
        round(rsi_val, 1)  if rsi_val else "—",
        "Pass",
        signal
    ])

cols = ["Ticker", "Name", "Close", "SMA", "RSI", "Valuation", "Signal"]
table = pd.DataFrame(records, columns=cols).sort_values("Ticker")
out = pathlib.Path(__file__).parents[1] / "docs" / "daily_screen"
out.with_suffix(".html").parent.mkdir(parents=True, exist_ok=True)
table.to_html(out.with_suffix(".html"), index=False,
              justify="center", border=0)
table.to_csv(out.with_suffix(".csv"), index=False)
print("✅ daily screen updated", date.today())