#!/usr/bin/env python3
"""
market_radar – Slack alert bot
•  RSS feeds  (Reg, FDA, Insider, Yahoo headline per-ticker)
•  Reddit-buzz scanner via YoloStocks.live
•  Short-interest pings via IEX Cloud
Designed to run as a cron / GitHub Action once per hour US-trading hours.
"""

import os, sys, sqlite3, datetime as dt, requests, feedparser, json, textwrap, time
from pathlib import Path
from dotenv import load_dotenv

# ───────────────────────────────────────────────────────────────────────────────
# 0 ▸  CONFIG
# ───────────────────────────────────────────────────────────────────────────────
RSS_STATIC = {
    "Federal Register – nuclear":
        "https://www.federalregister.gov/api/v1/articles.rss?conditions%5Bterm%5D=nuclear",
    "FDA Calendar":
        "https://www.fda.gov/about-fda/center-drug-evaluation-and-research-drug-approvals/calendar/rss.xml",
    "OpenInsider – Top Buys":
        "https://openinsider.com/top-insider-purchases-of-the-day?rss=1",
}

YOLO_API = "https://yolostocks.live/api/top"
DB_FILE  = Path(__file__).with_name("sent.db")

# ───────────────────────────────────────────────────────────────────────────────
# 1 ▸  ENV / DB  INIT
# ───────────────────────────────────────────────────────────────────────────────
load_dotenv()
SLACK = os.getenv("SLACK_WEBHOOK")
IEX   = os.getenv("IEX_TOKEN")

# user-tunable lists
SI_TICKERS = os.getenv("SI_TICKERS","").split(",") if os.getenv("SI_TICKERS") else []
NEWS_TICKERS_EXTRA = os.getenv("NEWS_TICKERS_EXTRA","").split(",") if os.getenv("NEWS_TICKERS_EXTRA") else []

# buzz thresholds
MIN_MENTIONS   = int(os.getenv("MENTION_MIN", 25))
ACCEL_FACTOR   = int(os.getenv("ACCEL_FACTOR", 3))
SUBREDDITS     = os.getenv("SUBREDDITS","wallstreetbets").split(",")

if not SLACK:
    sys.exit("⚠️  SLACK_WEBHOOK missing in .env")

# SQLite
con = sqlite3.connect(DB_FILE)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS sent_rss (guid TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS yolo_hist (ticker TEXT, date TEXT, cnt INT, "
            "PRIMARY KEY(ticker,date))")
con.commit()

def seen(guid:str)->bool:
    cur.execute("SELECT 1 FROM sent_rss WHERE guid=?", (guid,))
    return cur.fetchone() is not None

def mark_seen(guid:str):
    cur.execute("INSERT OR IGNORE INTO sent_rss VALUES (?)", (guid,))
    con.commit()

def slack(text:str, emoji=":newspaper:"):
    try:
        requests.post(SLACK, json={"text": f"{emoji} {text}"}, timeout=8)
    except Exception as exc:
        print("Slack error:", exc, file=sys.stderr)

# ───────────────────────────────────────────────────────────────────────────────
# 2 ▸  STATIC RSS (Reg / FDA / Insider)
# ───────────────────────────────────────────────────────────────────────────────
def is_today(ts):
    today = dt.date.today()
    return dt.date(ts.tm_year, ts.tm_mon, ts.tm_mday) == today

def scan_static_rss():
    for label, url in RSS_STATIC.items():
        feed = feedparser.parse(url)
        for e in feed.entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            if not ts or not is_today(ts) or seen(e.id):
                continue
            slack(f"*{label}*\n• {e.title[:240]}\n<{e.link}>")
            mark_seen(e.id)

# ───────────────────────────────────────────────────────────────────────────────
# 3 ▸  REDDIT BUZZ via YOLOSTOCKS
# ───────────────────────────────────────────────────────────────────────────────
def yolo_top(subreddit:str):
    params = {"subreddit": subreddit, "window": "daily", "limit": 200}
    try:
        return requests.get(YOLO_API, params=params, timeout=10).json()
    except Exception as exc:
        print("Yolo API error:", exc, file=sys.stderr)
        return []

def buzz_tickers():
    today = dt.date.today().isoformat()
    buzz = set()
    for sub in SUBREDDITS:
        for row in yolo_top(sub):
            tk, hits = row["ticker"], row["mentions"]
            if hits < MIN_MENTIONS:
                continue
            # 3-day average from SQLite
            cur.execute("SELECT AVG(cnt) FROM yolo_hist "
                        "WHERE ticker=? AND date>? ",
                        (tk, (dt.date.today()-dt.timedelta(days=3)).isoformat()))
            avg3 = cur.fetchone()[0] or 0
            if hits >= ACCEL_FACTOR * avg3:
                buzz.add(tk)
            # store today's count
            cur.execute("INSERT OR REPLACE INTO yolo_hist VALUES (?,?,?)",
                        (tk, today, hits))
    con.commit()
    return list(buzz)

# ───────────────────────────────────────────────────────────────────────────────
# 4 ▸  HEADLINE SCRAPE (Yahoo)
# ───────────────────────────────────────────────────────────────────────────────
def yahoo_rss(tkr):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={tkr}&region=US&lang=en-US"
    return feedparser.parse(url)

def scan_headlines(tickers):
    today = dt.date.today()
    for t in tickers:
        feed = yahoo_rss(t)
        for e in feed.entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            if not ts or dt.date(ts.tm_year, ts.tm_mon, ts.tm_mday) != today:
                continue
            if seen(e.id):
                continue
            src = e.get("source",{}).get("title","News")
            slack(f"*${t}* — {e.title}  _({src})_")
            mark_seen(e.id)

# ───────────────────────────────────────────────────────────────────────────────
# 5 ▸  SHORT-INTEREST quick ping (optional)
# ───────────────────────────────────────────────────────────────────────────────
def short_interest_alert():
    if not IEX or not SI_TICKERS:
        return
    for sym in SI_TICKERS:
        url = f"https://cloud.iexapis.com/stable/stock/{sym}/short-interest"
        try:
            data = requests.get(url, params={"token": IEX}, timeout=8).json()
        except Exception:
            continue
        si_pct = data.get("shortInterest",0)/max(data.get("float",1),1)*100
        ratio  = data.get("daysToCover",0)
        if si_pct>=20 or ratio>=10:
            slack(f"*${sym}* – Short {si_pct:.1f}% | DTC {ratio:.1f}×", emoji=":rotating_light:")

# ───────────────────────────────────────────────────────────────────────────────
# 6 ▸  MAIN
# ───────────────────────────────────────────────────────────────────────────────
def main():
    scan_static_rss()                               # Reg / FDA / Insider
    dynamic_tickers = buzz_tickers() + NEWS_TICKERS_EXTRA
    scan_headlines(dynamic_tickers)                 # Yahoo headlines (Reddit buzz + manual list)
    short_interest_alert()                          # Optional SI ping

if __name__ == "__main__":
    main() 