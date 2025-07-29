import pandas as pd, yfinance as yf, pathlib, sys
from datetime import date

# ensure rulebook import works no matter where script is run
sys.path.append(str(pathlib.Path(__file__).parent))
from rulebook import RULES

# RULES:
#   HIGH_BETA    ➜ SMA-30, RSI≤35
#   ESTABLISHED  ➜ SMA-50, RSI≤40
#   THEMATIC     ➜ SMA-100, RSI≤45

# ── THREE-TIER RULE SETS ──────────────────────────────────────────────────────
# THEME: SMA-100, RSI≤45
THEMATIC_RULES = {
    "URNM":  {"sma": 100, "rsi": 45},
    "NUKZ":  {"sma": 100, "rsi": 45},
    "XYL":   {"sma": 100, "rsi": 45},
    "ALFA.ST":{"sma": 100, "rsi": 45},
    "LEU":   {"sma": 100, "rsi": 45},
    "SMR":   {"sma": 100, "rsi": 45},
}

# HIGH-BETA: SMA-30, RSI≤35
HIGH_BETA_RULES = {
    "ATLX":   {"sma": 30, "rsi": 35},
    "BEAM":   {"sma": 30, "rsi": 35},
    "BMI":    {"sma": 30, "rsi": 35},
    "EOSE":   {"sma": 30, "rsi": 35},
    "FLNC":   {"sma": 30, "rsi": 35},
    "FLS":    {"sma": 30, "rsi": 35},
    "GWH":    {"sma": 30, "rsi": 35},
    "SANA":   {"sma": 30, "rsi": 35},
    "TMC":    {"sma": 30, "rsi": 35},
    "VRT":    {"sma": 30, "rsi": 35},
    "WIX":    {"sma": 30, "rsi": 35},
    "6324.T": {"sma": 30, "rsi": 35},
}

# ESTABLISHED: SMA-50, RSI≤40
ESTABLISHED_RULES = {
    "D":      {"sma": 50, "rsi": 40},
    "NEE":    {"sma": 50, "rsi": 40},
    "CEG":    {"sma": 50, "rsi": 40},
    "INTC":   {"sma": 50, "rsi": 40},
    "BNP":    {"sma": 50, "rsi": 40},
    "ENGI":   {"sma": 50, "rsi": 40},
    "IBE":    {"sma": 50, "rsi": 40},
    "KOMB":   {"sma": 50, "rsi": 40},
    "EOAN":   {"sma": 50, "rsi": 40},
    "BAS":    {"sma": 50, "rsi": 40},
    "FGR":    {"sma": 50, "rsi": 40},
    "AI":     {"sma": 50, "rsi": 40},
    "ALV":    {"sma": 50, "rsi": 40},
    "MUV2":   {"sma": 50, "rsi": 40},
    "1211.HK": {"sma": 50, "rsi": 40},
}

# Map display tickers to Yahoo symbols
ALIAS = {
    "U_T": "SRUUF",     # Sprott Physical Uranium Trust (USD OTC)
    # use "U.TO" instead if you prefer CAD TSX pricing
    "STOR": "STOR.SW",   # SIX Swiss Exchange symbol for the ETF
    "BNP":  "BNP.PA",    # BNP Paribas – Euronext Paris
    "ENGI": "ENGI.PA",   # Engie – Euronext Paris
    "IBE":  "IBE.MC",    # Iberdrola – Bolsa Madrid
    "KOMB": "KOMB.PR",   # Komercni banka – Prague exchange
    "EOAN": "EOAN.DE",   # E.ON SE – Deutsche Börse
    "BAS":  "BAS.DE",    # BASF SE – Deutsche Börse
    "FGR":  "FGR.PA",    # Eiffage S.A. – Euronext Paris
    "AI":   "AI.PA",     # Air Liquide – Euronext Paris
    "ALV":  "ALV.DE",    # Allianz SE – Deutsche Börse
    "MUV2": "MUV2.DE",   # Munich Re – Deutsche Börse
    "ALFA.ST": "ALFA.ST", # Alfa Laval – Stockholm
}

# ETFs / trusts with no earnings → auto-pass valuation
ETF_SET = {"NUKZ", "U_T", "STOR"}

# Ticker categorization sets
HIGH_BETA = set(HIGH_BETA_RULES.keys())
THEMATIC = set(THEMATIC_RULES.keys())
ESTABLISHED = set(ESTABLISHED_RULES.keys())

def valuation_pass(ticker: str, info: dict) -> bool:
    pe = info.get("forwardPE") or info.get("trailingPE")
    ev = info.get("enterpriseToEbitda")

    # Utility / nuclear incumbents get a higher cap
    if ticker in ESTABLISHED:
        return (
            (pe and 0 < pe <= 36) or
            (ev and ev <= 17)
        )

    # High-beta names keep the stricter cap
    return (
        (pe and 0 < pe <= 25) or
        (ev and ev <= 12)
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
# Combine all rule dictionaries
ALL_RULES = {**THEMATIC_RULES, **HIGH_BETA_RULES, **ESTABLISHED_RULES}
for ticker, rule in ALL_RULES.items():
    # -------------------------------------------------
    #  Price history (adjusted)  +  company name
    # -------------------------------------------------
    yahoo_symbol = ALIAS.get(ticker, ticker)
    hist = yf.download(yahoo_symbol, period="1000d", auto_adjust=True, progress=False)["Close"].dropna()  # <-- Series
    if hist.empty:
        records.append([ticker, "—", "—", "—", "NoPrice", "SKIP"])
        continue

    close = float(hist.iloc[-1].item())  # scalar
    name  = yf.Ticker(yahoo_symbol).info.get("shortName", "—")

    # -------------------------------------------------
    #  Valuation filter  (PE ≤ 25  OR  EV/EBITDA ≤ 12)
    # -------------------------------------------------
    fast = yf.Ticker(yahoo_symbol).fast_info or {}
    slow = yf.Ticker(yahoo_symbol).info
    # Debug: print valuation metrics for CEG and LEU
    if ticker in {"CEG", "LEU"}:
        print(f"DEBUG {ticker} fast_info: PE={fast.get('forwardPE') or fast.get('trailingPE')}, EV/EBITDA={fast.get('enterpriseToEbitda')}")
        print(f"DEBUG {ticker} info: PE={slow.get('forwardPE') or slow.get('trailingPE')}, EV/EBITDA={slow.get('enterpriseToEbitda')}")
    if ticker in ETF_SET:
        val_flag = "Pass"
    else:
        if not (valuation_pass(ticker, fast) or valuation_pass(ticker, slow)):
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

# ── 4. styled HTML + CSV output ───────────────────────────────────────
out_dir = pathlib.Path(__file__).parents[1] / "docs"
out_dir.mkdir(parents=True, exist_ok=True)

def colour_signal(val: str) -> str:
    return {
        "BUY":  "background-color:#d4f4be;color:#000;",
        "HOLD": "background-color:#f0f0f0;color:#000;",
        "EXIT": "background-color:#ffcccc;color:#000;",
        "SKIP": "background-color:#fff3bf;color:#000;",
    }.get(val, "")

def fmt_num(x, ndigits=2):
    if isinstance(x, (float, int)):
        return f"{x:.{ndigits}f}"
    return x  # leave em-dash or strings as-is

extra_css = """
<style>
body {
  background: #f8fafc;
  margin: 0;
  padding: 0;
}
#daily {
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  border-collapse: separate;
  border-spacing: 0;
  width: 95vw;
  max-width: 1100px;
  margin: 40px auto 32px auto;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.08);
  overflow: hidden;
}
#daily th {
  background: #f8fafc;
  color: #222;
  font-weight: 700;
  font-size: 1.12em;
  border-bottom: 2px solid #e5e7eb;
  padding: 14px 14px;
  letter-spacing: 0.02em;
}
#daily td {
  border-bottom: 1px solid #e5e7eb;
  padding: 13px 14px;
  font-size: 1em;
}
#daily tr:nth-child(even) td {
  background: #f6f8fa;
}
#daily tr:hover td {
  background: #e0f2fe;
  transition: background 0.2s;
}
caption {
  caption-side: top;
  font-size: 1.45em;
  font-weight: bold;
  color: #222;
  margin-bottom: 18px;
  padding: 12px 0 8px 0;
  letter-spacing: 0.5px;
}
</style>
"""

# Build HTML table manually
columns = table.columns.tolist()
rows = table.values.tolist()
caption = f"Daily Valuation + MA/RSI Screen • {date.today()}"

html = [f"<!DOCTYPE html><html><head>{extra_css}</head><body>"]
html.append(f'<table id="daily">')
html.append(f'<caption>{caption}</caption>')
html.append('<thead><tr>' + ''.join(f'<th>{col}</th>' for col in columns) + '</tr></thead>')
html.append('<tbody>')
for row in rows:
    html.append('<tr>')
    for i, cell in enumerate(row):
        style = ''
        if columns[i] == "Signal":
            style = colour_signal(cell)
        html.append(f'<td style="{style}">{cell}</td>')
    html.append('</tr>')
html.append('</tbody></table></body></html>')

with open(out_dir / "daily_screen.html", "w", encoding="utf-8") as f:
    f.write('\n'.join(html))

# ── 5. Add Exit-Action tables ─────────────────────────────────────────────────
cheat_chunks = [
    ("High-Beta / Tactical – EXIT rule: sell entire (or ≥ 50 %) next day",
     list(HIGH_BETA_RULES.keys())),
    ("Thematic Momentum – EXIT rule: hold/trim; sell only if thesis breaks",
     list(THEMATIC_RULES.keys())),
    ("Dividend / Established – EXIT rule: usually ignore; may average-down",
     list(ESTABLISHED_RULES.keys())),
]

with open(out_dir / "daily_screen.html", "a", encoding="utf-8") as f:
    for title, ticks in cheat_chunks:
        df = pd.DataFrame(
            {"Ticker": ticks,
             "What to do on EXIT": [title.split("–")[1].strip()]*len(ticks)}
        )
        f.write(f"<h3 style='margin-top:2em;'>{title}</h3>")
        f.write(df.to_html(index=False, escape=False))

# ── 6. Add enhanced disclaimer with Thesis-Break checklist ─────────────────────
disclaimer_html = """
    <h4>Disclaimer</h4>
    <p>This screener is for educational purposes only and is <strong>not</strong> investment advice.</p>

    <h4 style='margin-top:1em;'>Thesis-Break Test for Thematic Holdings</h4>
    <p>Act on EXIT <em>only</em> if <strong>two or more</strong> of these red flags appear:</p>
    <ol>
      <li><strong>Narrative flip</strong>&nbsp;&mdash; project or major customer lost.</li>
      <li><strong>Regulatory hit</strong>&nbsp;&mdash; new rule or licence denial undermines the business.</li>
      <li><strong>Moat breached</strong>&nbsp;&mdash; competitor leap-frogs tech or captures key share.</li>
      <li><strong>Balance-sheet blow-up</strong>&nbsp;&mdash; leverage spike, credit-rating plunge, or dilutive rescue financing.</li>
    </ol>
    """

with open(out_dir / "daily_screen.html", "a", encoding="utf-8") as f:
    f.write(disclaimer_html)

table.to_csv(out_dir / "daily_screen.csv", index=False)
print("✅ daily screen updated", date.today())