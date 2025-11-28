# rulebook.py – Ticker‑specific technical rules
# Only the tickers the user explicitly wants.

RULES = {
    # 🎯 THEMATIC Momentum (SMA-100, RSI≤45) – Long-term thematic holdings
    "URNM":  {"sma": 100, "rsi": 45},   # Sprott Uranium Miners ETF
    "NUKZ":  {"sma": 100, "rsi": 45},   # Range Nuclear Renaissance ETF
    "XYL":   {"sma": 100, "rsi": 45},   # Xylem
    "ALFA.ST":{"sma": 100, "rsi": 45},   # Alfa Laval
    "LEU":   {"sma": 100, "rsi": 45},   # Centrus
    "SMR":   {"sma": 100, "rsi": 45},   # NuScale Power
    "TSLA":  {"sma": 100, "rsi": 45},   # Tesla

    # 🔥 HIGH-BETA / Tactical (SMA-30, RSI≤35) – Short-term tactical trades
    "ATLX":   {"sma": 30, "rsi": 35},   # Atlas Lithium
    "BEAM":   {"sma": 30, "rsi": 35},   # Beam Therapeutics
    "BMI":    {"sma": 30, "rsi": 35},   # Badger Meter
    "EOSE":   {"sma": 30, "rsi": 35},   # Eos Energy Enterprises

    "FLS":    {"sma": 30, "rsi": 35},   # Flowserve Corporation
    "GWH":    {"sma": 30, "rsi": 35},   # ESS Tech
    "KD":     {"sma": 30, "rsi": 35},   # Kyndryl Holdings
    "ONON":   {"sma": 30, "rsi": 35},   # On Holding
    "SANA":   {"sma": 30, "rsi": 35},   # Sana Biotechnology
    "TSLA":   {"sma": 30, "rsi": 35},   # Tesla
    "VEEV":   {"sma": 30, "rsi": 35},   # Veeva Systems
    "VRT":    {"sma": 30, "rsi": 35},   # Vertiv Holdings
    "WIX":    {"sma": 30, "rsi": 35},   # Wix.com
    "NBIS":   {"sma": 30, "rsi": 35},   # Nebius – added 30 Jul 2025

    # 🏢 DIVIDEND / Established (SMA-50, RSI≤40) – Core & income holdings
    "BYDDY": {"sma": 50, "rsi": 40},  # BYD COMPANY
    "AI":     {"sma": 50, "rsi": 40},   # Air Liquide

    "ASML":   {"sma": 50, "rsi": 40},   # ASML Holding
    "BNP":    {"sma": 50, "rsi": 40},   # BNP Paribas
    "CEG":    {"sma": 50, "rsi": 40},   # Constellation Energy
    "D":      {"sma": 50, "rsi": 40},   # Dominion Energy
    "ENGI":   {"sma": 50, "rsi": 40},   # Engie
    "FGR":    {"sma": 50, "rsi": 40},   # Eiffage S.A.
    "IBE":    {"sma": 50, "rsi": 40},   # Iberdrola
    "INTC":   {"sma": 50, "rsi": 40},   # Intel Corporation
    "KOMB":   {"sma": 50, "rsi": 40},   # Komercni banka
    "NEE":    {"sma": 50, "rsi": 40},   # NextEra Energy
    "NTDOY":  {"sma": 50, "rsi": 40},   # Nintendo
    "PGR":    {"sma": 50, "rsi": 40},   # Progressive Corporation
    "RACE":   {"sma": 50, "rsi": 40},   # Ferrari
    "SBUX":   {"sma": 50, "rsi": 40},   # Starbucks
    "TJX":    {"sma": 50, "rsi": 40},   # TJX Companies
    "BRYN":   {"sma": 50, "rsi": 40},
    "AAPL":   {"sma": 50, "rsi": 40},
} 