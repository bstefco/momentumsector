import time
import logging
import schedule
import argparse
from dotenv import load_dotenv
import pandas as pd

from . import config, data, patterns, state
from .alerts import SlackAlerter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def scan_once(alerter: SlackAlerter) -> None:
    """
    Run a single scan for buy/sell signals and send Slack notifications. Never triggers orders.
    """
    positions = state.load_state()
    new_positions = positions.copy()

    # SELL logic: check for stop or target exits
    for ticker, pos in positions.items():
        df = data.fetch_daily(ticker)
        if df.empty or "Close" not in df:
            logger.warning(f"No data for {ticker} in SELL logic.")
            continue
        last_price = df["Close"].iloc[-1]
        entry = pos["entry"]
        stop = entry * (1 - config.STOP_PCT)
        target = entry * (1 + config.TARGET_PCT)
        gain_pct = 100 * (last_price / entry - 1)
        if last_price <= stop:
            alerter.send_sell({
                "tkr": ticker,
                "reason": "stop",
                "exit_price": last_price,
                "entry": entry,
                "gain_pct": gain_pct
            })
            new_positions.pop(ticker)
        elif last_price >= target:
            alerter.send_sell({
                "tkr": ticker,
                "reason": "target",
                "exit_price": last_price,
                "entry": entry,
                "gain_pct": gain_pct
            })
            new_positions.pop(ticker)

    # BUY logic: scan watchlist for new entries
    for ticker in config.WATCH:
        if ticker in new_positions:
            continue  # already held
        if not data.market_uptrend():
            continue  # only buy in uptrend
        df_daily = data.fetch_daily(ticker)
        if df_daily.empty or "Close" not in df_daily or "Volume" not in df_daily:
            logger.info(f"No data for {ticker} in BUY logic.")
            continue
        df_weekly = data.to_weekly(df_daily)
        pivot = patterns.compute_pivot(df_weekly)
        if pivot is None:
            continue
        last_close = df_daily["Close"].iloc[-1]
        buy_window = pivot * (1 + config.BUY_WINDOW)
        if not (pivot < last_close <= buy_window):
            continue
        # Volume and RS checks
        vol_ratio = df_daily["Volume"].iloc[-1] / df_daily["Volume"].rolling(50, min_periods=1).mean().iloc[-1]
        rs1 = data.rs_rank(df_daily["Close"], 5)
        rs6 = data.rs_rank(df_daily["Close"], 126)
        if vol_ratio < config.VOL_RATIO:
            continue
        if rs1 < config.RS_THRESHOLD or rs6 < config.RS_THRESHOLD:
            continue
        size_pct = config.position_size_pct()
        stop = pivot * (1 - config.STOP_PCT)
        target = pivot * (1 + config.TARGET_PCT)
        alerter.send_buy({
            "tkr": ticker,
            "entry": last_close,
            "pivot": pivot,
            "stop": stop,
            "target": target,
            "vol_ratio": vol_ratio,
            "rs1": rs1,
            "rs6": rs6,
            "size_pct": size_pct
        })
        new_positions[ticker] = {"entry": last_close, "pivot": pivot}

    state.save_state(new_positions)


def main():
    parser = argparse.ArgumentParser(description='CANSLIM Slack Bot')
    parser.add_argument('--once', action='store_true', help='Run once and exit (for GitHub Actions)')
    args = parser.parse_args()
    
    load_dotenv()
    alerter = SlackAlerter(config.SLACK_WEBHOOK_URL)
    alerter.send_startup()
    
    if args.once:
        # Run once and exit (for GitHub Actions)
        scan_once(alerter)
        logger.info("Bot completed single run.")
    else:
        # Run continuously (for local development)
        scan_once(alerter)
        schedule.every(config.SCAN_FREQ_MIN).minutes.do(lambda: scan_once(alerter))
        while True:
            schedule.run_pending()
            time.sleep(5)

if __name__ == "__main__":
    main() 