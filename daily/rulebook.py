# rulebook.py – Ticker‑specific technical rules
# Only the tickers the user explicitly wants.

RULES = {
    # ── Thematic (SMA-100, RSI≤45)
    "URNM":  {"sma": 100, "rsi": 45},   # Sprott Uranium Miners ETF
    "NUKZ":  {"sma": 100, "rsi": 45},   # Range Nuclear Renaissance ETF
    "XYL":   {"sma": 100, "rsi": 45},   # Xylem
    "ALFA.ST":{"sma": 100, "rsi": 45},   # Alfa Laval
    "LEU":   {"sma": 100, "rsi": 45},   # Centrus
    "SMR":   {"sma": 100, "rsi": 45},   # NuScale Power

    # ── High-beta / smaller (SMA-30, RSI≤35)
    "ATLX":   {"sma": 30, "rsi": 35},   # Atlas Lithium
    "BEAM":   {"sma": 30, "rsi": 35},   # Beam Therapeutics
    "BMI":    {"sma": 30, "rsi": 35},   # Badger Meter
    "EOSE":   {"sma": 30, "rsi": 35},   # Eos Energy Enterprises
    "FLNC":   {"sma": 30, "rsi": 35},   # Fluence Energy
    "FLS":    {"sma": 30, "rsi": 35},   # Flowserve Corporation
    "GWH":    {"sma": 30, "rsi": 35},   # ESS Tech
    "SANA":   {"sma": 30, "rsi": 35},   # Sana Biotechnology
    "TMC":    {"sma": 30, "rsi": 35},   # TMC the metals company
    "VRT":    {"sma": 30, "rsi": 35},   # Vertiv Holdings
    "WIX":    {"sma": 30, "rsi": 35},   # Wix.com
    "6324.T": {"sma": 30, "rsi": 35},   # Harmonic Drive Systems

    # ── Established players (SMA-50, RSI≤40)
    "D":      {"sma": 50, "rsi": 40},   # Dominion Energy
    "NEE":    {"sma": 50, "rsi": 40},   # NextEra Energy
    "CEG":    {"sma": 50, "rsi": 40},   # Constellation Energy
    "INTC":   {"sma": 50, "rsi": 40},   # Intel Corporation
    "BNP":    {"sma": 50, "rsi": 40},   # BNP Paribas
    "ENGI":   {"sma": 50, "rsi": 40},   # Engie
    "IBE":    {"sma": 50, "rsi": 40},   # Iberdrola
    "KOMB":   {"sma": 50, "rsi": 40},   # Komercni banka
    "FGR":    {"sma": 50, "rsi": 40},   # Eiffage S.A.
    "AI":     {"sma": 50, "rsi": 40},   # Air Liquide
    "1211.HK": {"sma": 50, "rsi": 40},  # BYD COMPANY
} 