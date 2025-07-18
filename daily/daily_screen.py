import pandas as pd, yfinance as yf, pathlib, sys
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
    # -------------------------------------------------
    #  Price history (adjusted)  +  company name
    # -------------------------------------------------
    hist = yf.download(ticker, period="1000d", auto_adjust=True, progress=False)["Close"].dropna()  # <-- Series
    if hist.empty:
        records.append([ticker, "—", "—", "—", "NoPrice", "SKIP"])
        continue

    close = float(hist.iloc[-1].item())  # scalar
    name  = yf.Ticker(ticker).info.get("shortName", "—")

    # -------------------------------------------------
    #  Valuation filter  (PE ≤ 25  OR  EV/EBITDA ≤ 12)
    # -------------------------------------------------
    fast = yf.Ticker(ticker).fast_info or {}
    slow = yf.Ticker(ticker).info
    if not (valuation_pass(fast) or valuation_pass(slow)):
        records.append([ticker, name, close, "—", "—", "Fail", "SKIP"])
        continue
    val_flag = "Pass"

    # -------------------------------------------------
    #  Technicals: SMA  +  RSI
    # -------------------------------------------------
    sma_len, rsi_cut = rule["sma"], rule["rsi"]

    sma_val = float(hist.tail(sma_len).mean().item()) if len(hist) >= sma_len else None

    # Manual RSI calculation with Wilder's smoothing (EMA, alpha=1/14)
    if len(hist) >= 14:
        delta = hist.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_series = rsi_series.ffill()  # Forward-fill any NaNs
        rsi_val = float(rsi_series.dropna().iloc[-1].item()) if not rsi_series.dropna().empty else None
    else:
        rsi_val = None

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
        round(sma_val, 2) if sma_val is not None else "—",
        round(rsi_val, 1) if rsi_val is not None else "—",
        val_flag,
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