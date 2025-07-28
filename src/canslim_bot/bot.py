import os
import time
from dotenv import load_dotenv
import schedule
import pandas as pd

from . import config
from . import data
from . import patterns
from . import state

# --- SlackAlerter ---
import requests
class SlackAlerter:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    def send(self, message: str):
        if self.webhook_url:
            requests.post(self.webhook_url, json={"text": message})

alerter = SlackAlerter(config.SLACK_WEBHOOK_URL)

# --- Main scan logic ---
def scan_once():
    """
    Run a single scan for buy/sell signals and send Slack notifications. Never triggers orders.
    """
    positions = state.load_state()
    new_positions = positions.copy()
    messages = []

    # SELL logic: check for stop or target exits
    for ticker, pos in positions.items():
        last_price = data.fetch_daily(ticker)["Close"].iloc[-1]
        entry = pos["entry"]
        stop = entry * (1 - config.STOP_PCT)
        target = entry * (1 + config.TARGET_PCT)
        if last_price <= stop:
            messages.append(f"SELL STOP: {ticker} hit stop ({last_price:.2f} ≤ {stop:.2f})")
            new_positions.pop(ticker)
        elif last_price >= target:
            messages.append(f"SELL TARGET: {ticker} hit target ({last_price:.2f} ≥ {target:.2f})")
            new_positions.pop(ticker)

    # BUY logic: scan watchlist for new entries
    for ticker in config.WATCH:
        if ticker in new_positions:
            continue  # already held
        if not data.market_uptrend():
            continue  # only buy in uptrend
        df_daily = data.fetch_daily(ticker)
        df_weekly = data.to_weekly(df_daily)
        pivot = patterns.compute_pivot(df_weekly)
        if pivot is None:
            continue
        last_close = df_daily["Close"].iloc[-1]
        buy_window = pivot * (1 + config.BUY_WINDOW)
        if pivot < last_close <= buy_window:
            # Simulate buy (do not trigger order)
            new_positions[ticker] = {"entry": last_close, "pivot": pivot}
            messages.append(f"BUY: {ticker} breakout at {last_close:.2f} (pivot {pivot:.2f})")

    # Save updated positions
    state.save_state(new_positions)

    # Send notifications
    for msg in messages:
        alerter.send(msg)

# --- Startup notification ---
def send_startup():
    alerter.send(":robot_face: CANSLIM Slack Bot started.")

# --- Main loop ---
if __name__ == "__main__":
    load_dotenv()
    send_startup()
    scan_once()  # initial scan
    schedule.every(config.SCAN_FREQ_MIN).minutes.do(scan_once)
    while True:
        schedule.run_pending()
        time.sleep(5) 