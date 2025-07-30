# rulebook.py – Ticker‑specific technical rules
# Only the tickers the user explicitly wants.

RULES = {
    # 🎯 THEMATIC Momentum (SMA-50, RSI≤48) – Long-term thematic holdings
    "URNM":  {"sma": 50, "rsi": 48},   # Sprott Uranium Miners ETF
    "NUKZ":  {"sma": 50, "rsi": 48},   # Range Nuclear Renaissance ETF
    "XYL":   {"sma": 50, "rsi": 48},   # Xylem
    "ALFA.ST":{"sma": 50, "rsi": 48},   # Alfa Laval
    "LEU":   {"sma": 50, "rsi": 48},   # Centrus
    "SMR":   {"sma": 50, "rsi": 48},   # NuScale Power

    # 🔥 HIGH-BETA / Tactical (SMA-20, RSI≤40) – Short-term tactical trades
    "ATLX":   {"sma": 20, "rsi": 40},   # Atlas Lithium
    "BEAM":   {"sma": 20, "rsi": 40},   # Beam Therapeutics
    "BMI":    {"sma": 20, "rsi": 40},   # Badger Meter
    "EOSE":   {"sma": 20, "rsi": 40},   # Eos Energy Enterprises
    "FLNC":   {"sma": 20, "rsi": 40},   # Fluence Energy
    "FLS":    {"sma": 20, "rsi": 40},   # Flowserve Corporation
    "GWH":    {"sma": 20, "rsi": 40},   # ESS Tech
    "KD":     {"sma": 20, "rsi": 40},   # Kyndryl Holdings
    "ONON":   {"sma": 20, "rsi": 40},   # On Holding
    "SANA":   {"sma": 20, "rsi": 40},   # Sana Biotechnology
    "TMC":    {"sma": 20, "rsi": 40},   # TMC the metals company
    "TSLA":   {"sma": 20, "rsi": 40},   # Tesla
    "VEEV":   {"sma": 20, "rsi": 40},   # Veeva Systems
    "VRT":    {"sma": 20, "rsi": 40},   # Vertiv Holdings
    "WIX":    {"sma": 20, "rsi": 40},   # Wix.com
    "6324.T": {"sma": 20, "rsi": 40},   # Harmonic Drive Systems

    # 🏢 DIVIDEND / Established (SMA-50, RSI≤45) – Core & income holdings
    "1211.HK": {"sma": 50, "rsi": 45},  # BYD COMPANY
    "AI":     {"sma": 50, "rsi": 45},   # Air Liquide
    "ALV":    {"sma": 50, "rsi": 45},   # Allianz SE
    "ASML":   {"sma": 50, "rsi": 45},   # ASML Holding
    "BNP":    {"sma": 50, "rsi": 45},   # BNP Paribas
    "CEG":    {"sma": 50, "rsi": 45},   # Constellation Energy
    "D":      {"sma": 50, "rsi": 45},   # Dominion Energy
    "ENGI":   {"sma": 50, "rsi": 45},   # Engie
    "FGR":    {"sma": 50, "rsi": 45},   # Eiffage S.A.
    "IBE":    {"sma": 50, "rsi": 45},   # Iberdrola
    "INTC":   {"sma": 50, "rsi": 45},   # Intel Corporation
    "KOMB":   {"sma": 50, "rsi": 45},   # Komercni banka
    "NEE":    {"sma": 50, "rsi": 45},   # NextEra Energy
    "NTDOY":  {"sma": 50, "rsi": 45},   # Nintendo
    "PGR":    {"sma": 50, "rsi": 45},   # Progressive Corporation
    "RACE":   {"sma": 50, "rsi": 45},   # Ferrari
    "SBUX":   {"sma": 50, "rsi": 45},   # Starbucks
    "TJX":    {"sma": 50, "rsi": 45},   # TJX Companies
} 