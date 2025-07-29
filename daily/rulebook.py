# rulebook.py – Ticker‑specific technical rules
# Only the tickers the user explicitly wants.

RULES = {
    # ── Smaller / high-beta (SMA-30, RSI≤35)
    "URNM": {"sma": 30, "rsi": 35},
    "LEU":  {"sma": 30, "rsi": 35},
    "SMR":  {"sma": 30, "rsi": 35},
    "OKLO": {"sma": 30, "rsi": 35},
    "SANA": {"sma": 30, "rsi": 35},
    "NTLA": {"sma": 30, "rsi": 35},
    "TMC":  {"sma": 30, "rsi": 35},
    "WIX":  {"sma": 30, "rsi": 35},
    "EOSE": {"sma": 30, "rsi": 35},
    "GWH":  {"sma": 30, "rsi": 35},
    "STOR": {"sma": 30, "rsi": 35},    # iShares Energy Storage & Hydro ETF (SIX)
    "NUKZ": {"sma": 30, "rsi": 35},
    "U_T": {"sma": 30, "rsi": 35},   # TSX symbol for the uranium trust
    "ATLX": {"sma": 30, "rsi": 35},   # Atlas Lithium
    "BEAM": {"sma": 30, "rsi": 35},   # Beam Therapeutics
    "6324.T": {"sma": 30, "rsi": 35}, # Harmonic Drive Systems (Tokyo)

    # ── Established players (SMA-50, RSI≤40)
    "D":    {"sma": 50, "rsi": 40},
    "NEE":  {"sma": 50, "rsi": 40},
    "CEG":  {"sma": 50, "rsi": 40},
    "1211.HK": {"sma": 50, "rsi": 40},
    "INTC": {"sma": 50, "rsi": 40},
    "BNP":  {"sma": 50, "rsi": 40},   # BNP Paribas
    "ENGI": {"sma": 50, "rsi": 40},   # Engie
    "IBE":  {"sma": 50, "rsi": 40},   # Iberdrola
    "KOMB": {"sma": 50, "rsi": 40},   # Komercni banka
} 