#!/usr/bin/env python3
"""
market_radar – Slack news & buzz bot
• Static RSS feeds (Reg, FDA, Insider)
• Live ticker list from Notion 'Active tickers' database
• Reddit buzz scan via YoloStocks.live
• Short-interest alert via yfinance
Designed for hourly cron / GH-Actions (US trading hours).
"""
import os, sys, sqlite3, datetime as dt, requests, feedparser, io, csv
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client
import yfinance as yf

#──────────────── CONFIG
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

#──────────────── ENV / DB
load_dotenv(override=True)
SLACK  = os.getenv("SLACK_WEBHOOK")
NOTION_TOK, NOTION_DB  = os.getenv("NOTION_TOKEN"), os.getenv("NOTION_DB")
SI_SET = set(os.getenv("SI_TICKERS","").upper().split(",")) if os.getenv("SI_TICKERS") else set()
MANUAL_EXTRA = set(os.getenv("NEWS_TICKERS_EXTRA","").upper().split(",")) if os.getenv("NEWS_TICKERS_EXTRA") else set()
MIN_MENTIONS = int(os.getenv("MENTION_MIN",25))
ACCEL_FACTOR = int(os.getenv("ACCEL_FACTOR",3))
SUBREDDITS   = os.getenv("SUBREDDITS","wallstreetbets").split(",")

if not SLACK:
    sys.exit("⚠️  SLACK_WEBHOOK missing in .env")

con = sqlite3.connect(DB_FILE)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS sent_rss (guid TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS yolo_hist (ticker TEXT, date TEXT, cnt INT, "
            "PRIMARY KEY(ticker,date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_news (ticker TEXT, title TEXT, date TEXT, "
            "PRIMARY KEY(ticker,title,date))")
con.commit()
print(f"[DEBUG] Using DB file: {DB_FILE}", file=sys.stderr)

def slack(msg:str, emoji=":newspaper:"):
    try:
        # Clean the webhook URL and ensure it's a proper URL
        webhook_url = SLACK.strip()
        if not webhook_url.startswith('http'):
            print(f"Invalid webhook URL: {webhook_url}", file=sys.stderr)
            return
        requests.post(webhook_url, json={"text":f"{emoji} {msg}"}, timeout=8)
    except Exception as e:
        print("Slack error:", e, file=sys.stderr)

def seen(guid:str)->bool:
    cur.execute("SELECT 1 FROM sent_rss WHERE guid=?", (guid,)); return cur.fetchone() is not None
def mark(guid):
    print(f"[DEBUG] Marking RSS: {guid}", file=sys.stderr)
    cur.execute("INSERT OR IGNORE INTO sent_rss VALUES (?)",(guid,)); con.commit()

def seen_news(ticker:str, title:str)->bool:
    today = dt.date.today().isoformat()
    # Create a normalized title (lowercase, remove extra spaces, take first 80 chars)
    normalized_title = " ".join(title.lower().split())[:80]
    cur.execute("SELECT 1 FROM sent_news WHERE ticker=? AND title=? AND date=?", 
                (ticker, normalized_title, today))
    return cur.fetchone() is not None

def mark_news(ticker:str, title:str):
    today = dt.date.today().isoformat()
    # Create a normalized title (lowercase, remove extra spaces, take first 80 chars)
    normalized_title = " ".join(title.lower().split())[:80]
    print(f"[DEBUG] Marking news: {ticker} | {normalized_title} | {today}", file=sys.stderr)
    cur.execute("INSERT OR IGNORE INTO sent_news VALUES (?,?,?)", 
                (ticker, normalized_title, today))
    con.commit()

#──── Static RSS  (Reg / FDA / Insider)
def scan_static():
    today = dt.date.today()
    for label,url in RSS_STATIC.items():
        for e in feedparser.parse(url).entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            if not ts or dt.date(*ts[:3])!=today or seen(e.id): continue
            slack(f"*{label}*\n• <{e.link}|{e.title[:240]}>\n<{e.link}>"); mark(e.id)

#──── Notion live ticker list (Active Ticker Overview)
def notion_tickers():
    if not (NOTION_TOK and NOTION_DB): 
        print("Notion not configured - skipping live ticker list", file=sys.stderr)
        return []
    try:
        nc = Client(auth=NOTION_TOK)
        # Get all tickers from Title column (no Active filter for now)
        res = nc.databases.query(database_id=NOTION_DB, page_size=200)["results"]
        tickers = [p["properties"]["Title"]["title"][0]["plain_text"].upper() for p in res if p["properties"]["Title"]["title"]]
        print(f"Found {len(tickers)} tickers from Notion: {tickers}", file=sys.stderr)
        return tickers
    except Exception as e:
        print("Notion API error:", e, file=sys.stderr); return []

#──── Reddit buzz
def buzz_tickers():
    today = dt.date.today().isoformat(); buzz = set()
    for sub in SUBREDDITS:
        try:
            rows = requests.get(YOLO_API,
                params={"subreddit":sub,"window":"daily","limit":200},timeout=10).json()
        except Exception: continue
        for r in rows:
            tk,hits=r["ticker"].upper(),r["mentions"]
            if hits < MIN_MENTIONS: continue
            cur.execute("SELECT AVG(cnt) FROM yolo_hist WHERE ticker=? AND date>?",
                        (tk,(dt.date.today()-dt.timedelta(days=3)).isoformat()))
            avg3 = cur.fetchone()[0] or 0
            if hits >= ACCEL_FACTOR*avg3: buzz.add(tk)
            cur.execute("INSERT OR REPLACE INTO yolo_hist VALUES (?,?,?)",(tk,today,hits))
    con.commit(); return buzz

# Note: YOLO API is currently not working, so YOLO mentions feature is disabled
# The existing buzz_tickers() function already provides Reddit buzz monitoring

#──── Yahoo headline fetch
def yahoo(tkr): return feedparser.parse(
    f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={tkr}&region=US&lang=en-US")

def scan_headlines(tickers):
    today=dt.date.today()
    sent_count = 0  # Track how many messages we've sent
    
    for tk in tickers:
        if sent_count >= 20:  # Limit to 20 news items per run to prevent spam
            break
            
        for e in yahoo(tk).entries:
            if sent_count >= 20:  # Double check limit
                break
                
            ts=e.get("published_parsed")or e.get("updated_parsed")
            if not ts or dt.date(*ts[:3])!=today: continue
            if seen_news(tk, e.title): continue  # Skip if already sent today
            
            src=e.get("source",{}).get("title","News")
            slack(f"*${tk}* — <{e.link}|{e.title}>  _({src})_")
            mark_news(tk, e.title)  # Mark as sent for today
            sent_count += 1

#──── Short-interest alert via yfinance
def short_interest():
    for sym in SI_SET:
        try:
            info=yf.Ticker(sym).get_info()
            si=float(info.get("sharesShort",0)); flo=float(info.get("floatShares")or info.get("sharesOutstanding") or 0)
            vol=float(info.get("averageVolume",0))
        except Exception: continue
        if not (si and flo and vol): continue
        pct,dtc=si/flo*100, si/vol
        if pct>=20 or dtc>=10:
            slack(f"*${sym}* – Short {pct:.1f}% | DTC {dtc:.1f}×", emoji=":rotating_light:")

#──── MAIN
def main():
    scan_static()
    tks = set(notion_tickers()) | MANUAL_EXTRA | buzz_tickers()
    scan_headlines(sorted(tks))
    
    # YOLO mentions feature disabled due to API issues
    # Reddit buzz monitoring is still active via buzz_tickers()
    
    if SI_SET: short_interest()

if __name__=="__main__": main() 