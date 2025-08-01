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
# 🎯 THEMATIC Momentum (SMA-100, RSI≤45) – Long-term thematic holdings
THEMATIC_RULES = {
    "URNM.L":  {"sma": 100, "rsi": 45},
    "NUKZ":  {"sma": 100, "rsi": 45},
    "XYL":   {"sma": 100, "rsi": 45},
    "ALFA.ST":{"sma": 100, "rsi": 45},
    "LEU":   {"sma": 100, "rsi": 45},
    "SMR":   {"sma": 100, "rsi": 45},
}

# 🔥 HIGH-BETA / Tactical (SMA-30, RSI≤35) – Short-term tactical trades
HIGH_BETA_RULES = {
    "ATLX":   {"sma": 30, "rsi": 35},
    "BEAM":   {"sma": 30, "rsi": 35},
    "BMI":    {"sma": 30, "rsi": 35},
    "EOSE":   {"sma": 30, "rsi": 35},
    "FLNC":   {"sma": 30, "rsi": 35},
    "FLS":    {"sma": 30, "rsi": 35},
    "GWH":    {"sma": 30, "rsi": 35},
    "ONON":   {"sma": 30, "rsi": 35},
    "SANA":   {"sma": 30, "rsi": 35},
    "VEEV":   {"sma": 30, "rsi": 35},
    "VRT":    {"sma": 30, "rsi": 35},
    "WIX":    {"sma": 30, "rsi": 35},
    "NBIS":   {"sma": 30, "rsi": 35},   # Nebius – added 30 Jul 2025
    "6324.T": {"sma": 30, "rsi": 35},
}

# 🏢 DIVIDEND / Established (SMA-50, RSI≤40) – Core & income holdings
ESTABLISHED_RULES = {
    "BYDDY": {"sma": 50, "rsi": 40},
    "AI":     {"sma": 50, "rsi": 40},

    "ASML":   {"sma": 50, "rsi": 40},
    "BNP":    {"sma": 50, "rsi": 40},
    "CEG":    {"sma": 50, "rsi": 40},
    "D":      {"sma": 50, "rsi": 40},
    "ENGI":   {"sma": 50, "rsi": 40},
    "FGR":    {"sma": 50, "rsi": 40},
    "IBE":    {"sma": 50, "rsi": 40},
    "INTC":   {"sma": 50, "rsi": 40},
    "KOMB":   {"sma": 50, "rsi": 40},
    "NEE":    {"sma": 50, "rsi": 40},
    "NTDOY":  {"sma": 50, "rsi": 40},
    "PGR":    {"sma": 50, "rsi": 40},
    "RACE BVME":   {"sma": 50, "rsi": 40},
    "SBUX":   {"sma": 50, "rsi": 40},
    "TJX":    {"sma": 50, "rsi": 40},
    
    # Added from Team Hidden Gems and Team Rule Breakers
    "DASH":   {"sma": 50, "rsi": 40},
    "KD":     {"sma": 50, "rsi": 40},
    "TSLA":   {"sma": 50, "rsi": 40},
    "AMZN":   {"sma": 50, "rsi": 40},
    "MSFT":   {"sma": 50, "rsi": 40},
    "NVDA":   {"sma": 50, "rsi": 40},
    "VRTX":   {"sma": 50, "rsi": 40},
    "DIS":    {"sma": 50, "rsi": 40},
}

# Map display tickers to Yahoo symbols
ALIAS = {
    "BNP":  "BNP.PA",    # BNP Paribas – Euronext Paris
    "ENGI": "ENGI.PA",   # Engie – Euronext Paris
    "IBE":  "IBE.MC",    # Iberdrola – Bolsa Madrid
    "KOMB": "KOMB.PR",   # Komercni banka – Prague exchange
    "FGR":  "FGR.PA",    # Eiffage S.A. – Euronext Paris
    "AI":   "AI.PA",     # Air Liquide – Euronext Paris
    "ALFA.ST": "ALFA.ST", # Alfa Laval – Stockholm

    "ASML": "ASML",      # ASML Holding
    "NTDOY": "NTDOY",    # Nintendo
    "PGR":  "PGR",       # Progressive Corporation
    "RACE BVME": "RACE",      # Ferrari
    "SBUX": "SBUX",      # Starbucks
    "TJX":  "TJX",       # TJX Companies
}

# ETFs / trusts with no earnings → auto-pass valuation
ETF_SET = {"NUKZ"}

# Ticker categorization sets
HIGH_BETA = set(HIGH_BETA_RULES.keys())
THEMATIC = set(THEMATIC_RULES.keys())
ESTABLISHED = set(ESTABLISHED_RULES.keys())

def valuation_pass(ticker: str, info: dict) -> bool:
    pe = info.get("forwardPE") or info.get("trailingPE")
    ev = info.get("enterpriseToEbitda")

    # --- valuation pass ---
    #  • If both PE and EV/EBITDA are NaN (ETFs, non-US), skip the test.
    #  • Else must pass ≤15× PE  OR  ≤8× EV/EBITDA.
    VAL_OK = (
        (pd.isna(pe) and pd.isna(ev))
        or (pe and pe <= 15)
        or (ev and ev <= 8)
    )
    return VAL_OK

def get_company_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or ticker
    except Exception:
        return ticker

def safe_round(val, ndigits):
    return round(float(val), ndigits) if val is not None else "—"

def gbx_gbp_eur(price: float, currency: str) -> float:
    """
    Convert GBX or GBP price to EUR. 
    - GBX  (pence): divide by 100, then multiply by FX.
    - GBP  (pounds): multiply by FX directly.
    - Other currencies (EUR, USD, SEK …): return unchanged.
    """
    if currency not in ("GBX", "GBp", "GBP"):
        return price                        # already native
    gbp_eur = yf.Ticker("GBPEUR=X").fast_info["last_price"]
    if currency in ("GBX", "GBp"):
        price = price / 100                # to pounds first
    return price * gbp_eur

def normalize_row(row):
    """
    Convert URNM.L (and any other GBX/GBP lines) to euros *before*
    SMA and RSI are calculated.
    """
    ticker = row["Ticker"]
    currency = yf.Ticker(ticker).info.get("currency", "EUR")
    row["Close"] = gbx_gbp_eur(row["Close"], currency)
    row["SMA"]   = gbx_gbp_eur(row["SMA"],   currency)
    return row

records = []
# Combine all rule dictionaries
ALL_RULES = {**THEMATIC_RULES, **HIGH_BETA_RULES, **ESTABLISHED_RULES}
for ticker, rule in ALL_RULES.items():
    # -------------------------------------------------
    #  Price history (adjusted)  +  company name
    # -------------------------------------------------
    yahoo_symbol = ALIAS.get(ticker, ticker)
    data = yf.download(yahoo_symbol, period="1000d", auto_adjust=True, progress=False)
    if data.empty:
        records.append([ticker, "—", "—", "—", "NoPrice", "SKIP"])
        continue
    
    hist = data["Close"].dropna()  # <-- Series
    volume = data["Volume"].dropna()  # <-- Volume Series
    
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

    # Determine which bucket this ticker belongs to
    if ticker in THEMATIC:
        bucket = "THEMATIC"
    elif ticker in HIGH_BETA:
        bucket = "HIGH_BETA"
    else:
        bucket = "DIVIDEND"
    
    # Signal assignment based on new logic
    if sma_val is None or rsi_val is None:
        signal = "SKIP"
    elif bucket == "THEMATIC":
        if (close <= sma_val) or (rsi_val <= rsi_cut):
            signal = "BUY"
        else:
            signal = "HOLD"
    elif bucket == "HIGH_BETA":
        # HIGH_BETA specific logic with TRIM conditions
        # Calculate extension percentage above SMA-20
        sma20_val = float(hist.tail(20).mean().item()) if len(hist) >= 20 else None
        
        # TRIM conditions for high-beta stocks
        extension_pct = ((close - sma20_val) / sma20_val * 100) if sma20_val else 0
        overbought_rsi = rsi_val >= 70 if rsi_val else False
        
        # TRIM rules: 15% above SMA-20 OR RSI >= 70
        if (extension_pct >= 15) or overbought_rsi:
            signal = "TRIM"
        elif (close <= sma_val) or (rsi_val <= rsi_cut):
            signal = "BUY"
        elif close < sma_val:
            signal = "EXIT"
        else:
            signal = "HOLD"
    else:  # DIVIDEND / Established
        if (close <= sma_val) or (rsi_val <= rsi_cut):
            signal = "BUY"
        elif close < sma_val:
            signal = "EXIT"
        else:
            signal = "HOLD"

    # -------------------------------------------------
    #  Panic-flush filter (overrides BUY and TRIM)
    # -------------------------------------------------
    if (signal == "BUY" or signal == "TRIM") and len(hist) >= 4 and len(volume) >= 20:
        # Calculate 3-day price drop percentage
        drop_3d_pct = ((hist.iloc[-1] - hist.iloc[-4]) / hist.iloc[-4] * 100).item()
        
        # Calculate 20-day average volume
        avg20vol = float(volume.tail(20).mean().item())
        current_vol = float(volume.iloc[-1].item()) if len(volume) > 0 else 0
        
        # Panic-flush condition: -15% drop + 2x volume
        panic = (drop_3d_pct <= -15) and (current_vol >= 2 * avg20vol)
        if panic:
            signal = "EXIT"

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

# Apply currency conversion for GBX/GBP tickers
table = table.apply(normalize_row, axis=1)

# ── 4. styled HTML + CSV output ───────────────────────────────────────
out_dir = pathlib.Path(__file__).parents[1] / "docs"
out_dir.mkdir(parents=True, exist_ok=True)

def colour_signal(val: str) -> str:
    return {
        "BUY":  "background-color:#d4f4be;color:#000;",
        "HOLD": "background-color:#f0f0f0;color:#000;",
        "EXIT": "background-color:#ffcccc;color:#000;",
        "TRIM": "background-color:#ffeb3b;color:#000;",
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

# Build three separate HTML tables by tier
columns = ["Ticker", "Name", "Close", "SMA", "RSI", "Valuation", "Signal"]

def build_table_html(tier_name, ticker_list, caption):
    """Build a styled HTML table for a specific tier"""
    tier_records = [row for row in records if row[0] in ticker_list]
    if not tier_records:
        return ""
    
    tier_df = pd.DataFrame(tier_records, columns=columns).sort_values("Ticker")
    rows = tier_df.values.tolist()
    
    html_parts = [f'<table id="daily">']
    html_parts.append(f'<caption>{caption}</caption>')
    html_parts.append('<thead><tr>' + ''.join(f'<th>{col}</th>' for col in columns) + '</tr></thead>')
    html_parts.append('<tbody>')
    
    for row in rows:
        html_parts.append('<tr>')
        for i, cell in enumerate(row):
            style = ''
            if columns[i] == "Signal":
                style = colour_signal(cell)
            html_parts.append(f'<td style="{style}">{cell}</td>')
        html_parts.append('</tr>')
    
    html_parts.append('</tbody></table>')
    return '\n'.join(html_parts)

# Build the three tier tables
thematic_table = build_table_html("Thematic", list(THEMATIC_RULES.keys()), 
                                 f"Thematic Momentum (SMA-100, RSI≤45) • {date.today()}")
high_beta_table = build_table_html("High-Beta", list(HIGH_BETA_RULES.keys()), 
                                   f"High-Beta / Tactical (SMA-30, RSI≤35) • {date.today()}")
established_table = build_table_html("Established", list(ESTABLISHED_RULES.keys()), 
                                     f"Dividend / Established (SMA-50, RSI≤40) • {date.today()}")

# Add disclaimer
disclaimer_html = """
    <div style="margin: 40px auto; max-width: 1100px; padding: 20px; background: #fff; border-radius: 14px; box-shadow: 0 2px 16px rgba(0,0,0,0.08);">
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
    </div>
    """

# Combine all tables and disclaimer
html = [f"<!DOCTYPE html><html><head>{extra_css}</head><body>"]
html.append(thematic_table)
html.append(high_beta_table)
html.append(established_table)
html.append(disclaimer_html)
html.append('</body></html>')

with open(out_dir / "daily_screen.html", "w", encoding="utf-8") as f:
    f.write('\n'.join(html))

table.to_csv(out_dir / "daily_screen.csv", index=False)
print("✅ daily screen updated", date.today())