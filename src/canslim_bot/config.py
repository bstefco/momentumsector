import os
from typing import List
from dotenv import load_dotenv
import logging

load_dotenv()

SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
RISK_PCT_PER_TRADE: float = float(os.getenv("RISK_PCT_PER_TRADE", 1.0))

WATCH: List[str] = [
    "LPLA", "PWR", "ATAT", "KLAC", "IBKR",
    "AGX", "ROAD", "AXON", "ANET", "WELL",
    "FUTU", "CLS", "CHEF", "AVGO", "PLTR",
    "TSM", "NVDA", "VRT"
]
VOL_RATIO: float = 1.4
BUY_WINDOW: float = 0.05
STOP_PCT: float = 0.08
TARGET_PCT: float = 0.20
RS_THRESHOLD: int = 85
SCAN_FREQ_MIN: int = 30

def position_size_pct(
    risk_pct: float = RISK_PCT_PER_TRADE,
    stop_pct: float = STOP_PCT
) -> float:
    """
    Calculate the percentage of equity to deploy per trade based on risk and stop loss.

    Args:
        risk_pct (float): Percentage of equity to risk per trade (e.g., 1.0 for 1%).
        stop_pct (float): Stop loss percentage (e.g., 0.08 for 8%).

    Returns:
        float: Percentage of equity to deploy in the trade.
    """
    if stop_pct == 0:
        logging.error("stop_pct must not be zero.")
        raise ValueError("stop_pct must not be zero.")
    return risk_pct / stop_pct 