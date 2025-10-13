import pandas as pd, yfinance as yf, pathlib, sys, argparse
from datetime import date

# Ensure chained assignment warnings are enabled
pd.options.mode.chained_assignment = 'warn'

# Parse command line arguments
parser = argparse.ArgumentParser(description='Daily momentum screen with enhanced features')
parser.add_argument('--save-csv', action='store_true', help='Save DataFrame to CSV file')
args = parser.parse_args()

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

    "FLS":    {"sma": 30, "rsi": 35},
    "GWH":    {"sma": 30, "rsi": 35},
    "H4N.F":  {"sma": 30, "rsi": 35},   # Solar Foods Oyj – Frankfurt exchange
    "KD":     {"sma": 30, "rsi": 35},
    "ONON":   {"sma": 30, "rsi": 35},
    "SANA":   {"sma": 30, "rsi": 35},
    "TMC":    {"sma": 30, "rsi": 35},   # TMC the metals company Inc. – US exchange
    "TMDX":   {"sma": 30, "rsi": 35},   # TransMedics Group Inc. – US exchange
    "VEEV":   {"sma": 30, "rsi": 35},
    "VRT":    {"sma": 30, "rsi": 35},
    "WIX":    {"sma": 30, "rsi": 35},
    "NBIS":   {"sma": 30, "rsi": 35},   # Nebius – added 30 Jul 2025
    "IDR.MC": {"sma": 30, "rsi": 35},   # Indra Sistemas – Madrid exchange
    "IREN":   {"sma": 30, "rsi": 35},   # IREN Ltd – NASDAQ
    "9660":   {"sma": 30, "rsi": 35},   # Horizon Robotics – HKEX code 9660
    "ZETA":   {"sma": 30, "rsi": 35},   # Zeta Global Holdings – NYSE
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
    "GTT":    {"sma": 50, "rsi": 40},
    "FGR":    {"sma": 50, "rsi": 40},
    "700":    {"sma": 50, "rsi": 40},   # Tencent Holdings – SEHK 0700.HK
    "9880":   {"sma": 50, "rsi": 40},   # UBTECH Robotics – SEHK 9880.HK
    "BIDU":   {"sma": 50, "rsi": 40},   # Baidu Inc. – ADR
    "NKE":    {"sma": 50, "rsi": 40},   # Nike Inc. – NYSE
    "BABA":   {"sma": 50, "rsi": 40},   # Alibaba Group – NYSE
    "BARN":   {"sma": 50, "rsi": 40},   # Barry Callebaut – SIX Swiss
    "IBE":    {"sma": 50, "rsi": 40},
    "INTC":   {"sma": 50, "rsi": 40},
    "KOMB":   {"sma": 50, "rsi": 40},
    "NEE":    {"sma": 50, "rsi": 40},
    "NTDOY":  {"sma": 50, "rsi": 40},
    "PGR":    {"sma": 50, "rsi": 40},
    "RACE.MI":   {"sma": 50, "rsi": 40},
    "SBUX":   {"sma": 50, "rsi": 40},
    "TJX":    {"sma": 50, "rsi": 40},
    
    # Added from Team Hidden Gems and Team Rule Breakers
    "DASH":   {"sma": 50, "rsi": 40},
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
    "H4N.F": "H4N.F",    # Solar Foods Oyj – Frankfurt exchange
    "IBE":  "IBE.MC",    # Iberdrola – Bolsa Madrid
    "IDR.MC": "IDR.MC",  # Indra Sistemas – Bolsa Madrid
    "700":  "0700.HK",   # Tencent Holdings – Hong Kong
    "9880": "9880.HK",   # UBTECH Robotics – Hong Kong
    "BARN": "BARN.SW",   # Barry Callebaut AG – SIX Swiss
    "KOMB": "KOMB.PR",   # Komercni banka – Prague exchange
    "FGR":  "FGR.PA",    # Eiffage S.A. – Euronext Paris
    "AI":   "AI.PA",     # Air Liquide – Euronext Paris
    "GTT":  "GTT.PA",    # Gaztransport & Technigaz – Euronext Paris
    "9660": "9660.HK",   # Horizon Robotics – Hong Kong (Yahoo symbol)
    "ALFA.ST": "ALFA.ST", # Alfa Laval – Stockholm

    "ASML": "ASML",      # ASML Holding
    "NTDOY": "NTDOY",    # Nintendo
    "PGR":  "PGR",       # Progressive Corporation
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

    # -------------------------------------------------
    #  Enhanced Technical Analysis - New Columns
    # -------------------------------------------------
    # 1. 20-day moving average and related fields
    sma20_val = float(hist.tail(20).mean().item()) if len(hist) >= 20 else None
    px_vs_sma20 = (close / sma20_val) if sma20_val else None
    px_vs_sma20_flag = px_vs_sma20 >= 1.15 if px_vs_sma20 else False
    
    # 2. Short-term drawdown tracking for high-beta names
    if len(hist) >= 2:
        pct_1d = float(((hist.iloc[-1] - hist.iloc[-2]) / hist.iloc[-2]).item()) if len(hist) >= 2 else None
        pct_2d = float(((hist.iloc[-1] - hist.iloc[-3]) / hist.iloc[-3]).item()) if len(hist) >= 3 else None
    else:
        pct_1d = None
        pct_2d = None
    
    # Volume analysis for drawdown flags
    vol_2d = float(volume.tail(2).mean().item()) if len(volume) >= 2 else None
    avg_vol = float(volume.tail(20).mean().item()) if len(volume) >= 20 else None
    
    # Determine which bucket this ticker belongs to
    if ticker in THEMATIC:
        bucket = "THEMATIC"
    elif ticker in HIGH_BETA:
        bucket = "HIGH_BETA"
    else:
        bucket = "DIVIDEND"
    
    # 3. Flag calculations
    drop10_flag = (pct_1d <= -0.10) and (bucket == "HIGH_BETA") if pct_1d is not None else False
    drop15vol_flag = (pct_2d <= -0.15) and (vol_2d >= 2 * avg_vol) and (bucket == "HIGH-BETA") if all(x is not None for x in [pct_2d, vol_2d, avg_vol]) else False
    rsi70_flag = rsi_val >= 70 if rsi_val else False
    
    # 4. Master TRIM_FLAG
    trim_flag = px_vs_sma20_flag or rsi70_flag or drop10_flag or drop15vol_flag
    
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
        # TRIM rules: 15% above SMA-20 OR RSI >= 70 OR other trim flags
        if trim_flag:
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
        signal,
        round(sma20_val, 2) if sma20_val is not None else "—",
        round(px_vs_sma20, 3) if px_vs_sma20 is not None else "—",
        round(pct_1d * 100, 1) if pct_1d is not None else "—",
        round(pct_2d * 100, 1) if pct_2d is not None else "—",
        "✓" if rsi70_flag else "—",
        "✓" if trim_flag else "—"
    ])

cols = ["Ticker", "Name", "Close", "SMA", "RSI", "Valuation", "Signal", "SMA_20", "Px_vs_SMA20", "1d_pct", "2d_pct", "RSI70_Flag", "TRIM_FLAG"]
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
columns = ["Ticker", "Name", "Close", "SMA", "RSI", "Valuation", "Signal", "SMA_20", "Px_vs_SMA20", "1d_pct", "2d_pct", "RSI70_Flag", "TRIM_FLAG"]

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
        # Check if this row has TRIM_FLAG set
        trim_flag_index = columns.index("TRIM_FLAG")
        has_trim_flag = row[trim_flag_index] == "✓"
        
        # Add red background for entire row if TRIM_FLAG is True
        row_style = 'background-color:#ffebee;' if has_trim_flag else ''
        html_parts.append(f'<tr style="{row_style}">')
        
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

# Add tactical exit legend
legend_html = """
    <div style="margin: 40px auto; max-width: 1100px; padding: 20px; background: #fff; border-radius: 14px; box-shadow: 0 2px 16px rgba(0,0,0,0.08);">
        <hr style="margin-top:32px">
        <h3 style="margin-bottom:8px">Tactical Exit Layers — Quick Guide</h3>
        <table style="border-collapse:collapse;font-size:14px">
          <thead>
            <tr>
              <th style="padding:4px 8px;border-bottom:1px solid #ccc">#</th>
              <th style="padding:4px 8px;border-bottom:1px solid #ccc">Layer</th>
              <th style="padding:4px 8px;border-bottom:1px solid #ccc">Trigger</th>
              <th style="padding:4px 8px;border-bottom:1px solid #ccc">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>1</td><td>Structural Exit</td><td>Thesis broken</td><td>Sell 100 %</td></tr>
            <tr><td>2</td><td>Risk-Trim</td><td>Price ≥ 1.15×SMA-20 <br>or RSI ≥ 70</td><td>Sell 25-35 %</td></tr>
            <tr><td>3</td><td>Stop-Loss Guard</td><td>1-day drop ≤ –10 % (High-Beta)</td><td>Sell 50 %</td></tr>
            <tr><td>4</td><td>Panic / Trailing</td><td>2-day drop ≤ –15 % & ≥ 2× vol <br>or Close &lt; SMA-50 after Risk-Trim</td><td>Sell remainder</td></tr>
            <tr><td>5</td><td>Quarterly Rebalance</td><td>End of Mar/Jun/Sep/Dec</td><td>Recycle gains into under-budget sleeves</td></tr>
          </tbody>
        </table>
        <p style="font-size:12px;color:#666;margin-top:6px">
        Hierarchy: Structural Exit → Bucket Trim caps → Risk-Trim/Stops → Calendar Rebalance.
        </p>
    </div>
    """

# Combine all tables and legend
html = [f"<!DOCTYPE html><html><head>{extra_css}</head><body>"]
html.append(thematic_table)
html.append(high_beta_table)
html.append(established_table)
html.append(legend_html)
html.append('</body></html>')

with open(out_dir / "daily_screen.html", "w", encoding="utf-8") as f:
    f.write('\n'.join(html))

if args.save_csv:
    table.to_csv(out_dir / "daily_screen.csv", index=False)
    print("✅ daily screen updated with CSV", date.today())
else:
    print("✅ daily screen updated (no CSV saved)", date.today())