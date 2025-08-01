#!/usr/bin/env python3
"""
Enhanced Market Radar Bot
Enhanced version with SEC filings, earnings calendar, volume spikes, and sentiment analysis
"""
import os, sys, sqlite3, datetime as dt, requests, feedparser, io, csv
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client
import yfinance as yf
import re
from collections import defaultdict

#──────────────── CONFIG
RSS_STATIC = {
    "Federal Register – nuclear":
      "https://www.federalregister.gov/api/v1/articles.rss?conditions%5Bterm%5D=nuclear",
    "FDA Calendar":
      "https://www.fda.gov/about-fda/center-drug-evaluation-and-research-drug-approvals/calendar/rss.xml",
    "OpenInsider – Top Buys":
      "https://openinsider.com/top-insider-purchases-of-the-day?rss=1",
}

# SEC filing types to monitor
SEC_FILING_TYPES = ['8-K', '10-K', '10-Q', '4', '13F-HR', 'SC 13G', 'SC 13D']

# API endpoints
APEW_URL = "https://apewisdom.io/api/v1.0/filter/wallstreetbets"
YOLO_API = "https://yolostocks.live/api/top"

DB_FILE = Path(__file__).with_name("sent.db")

#──────────────── ENV / DB
load_dotenv(override=True)
SLACK = os.getenv("SLACK_WEBHOOK")
NOTION_TOK, NOTION_DB = os.getenv("NOTION_TOKEN"), os.getenv("NOTION_DB")
SI_SET = set(os.getenv("SI_TICKERS","").upper().split(",")) if os.getenv("SI_TICKERS") else set()
MANUAL_EXTRA = set(os.getenv("NEWS_TICKERS_EXTRA","").upper().split(",")) if os.getenv("NEWS_TICKERS_EXTRA") else set()
MIN_MENTIONS = int(os.getenv("MENTION_MIN",25))
ACCEL_FACTOR = int(os.getenv("ACCEL_FACTOR",3))
SUBREDDITS = os.getenv("SUBREDDITS","wallstreetbets").split(",")

# New configuration options
VOLUME_SPIKE_THRESHOLD = float(os.getenv("VOLUME_SPIKE_THRESHOLD", "2.0"))
PRICE_MOMENTUM_THRESHOLD = float(os.getenv("PRICE_MOMENTUM_THRESHOLD", "0.05"))
EARNINGS_DAYS_AHEAD = int(os.getenv("EARNINGS_DAYS_AHEAD", "7"))
SEC_FILING_DAYS_BACK = int(os.getenv("SEC_FILING_DAYS_BACK", "1"))

if not SLACK:
    sys.exit("⚠️  SLACK_WEBHOOK missing in .env")

con = sqlite3.connect(DB_FILE)
cur = con.cursor()

# Enhanced database schema
cur.execute("CREATE TABLE IF NOT EXISTS sent_rss (guid TEXT PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS yolo_hist (ticker TEXT, date TEXT, cnt INT, PRIMARY KEY(ticker,date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_news (ticker TEXT, title TEXT, date TEXT, PRIMARY KEY(ticker,title,date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_sec_filings (ticker TEXT, filing_type TEXT, date TEXT, PRIMARY KEY(ticker,filing_type,date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_earnings (ticker TEXT, earnings_date TEXT, PRIMARY KEY(ticker,earnings_date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_volume_spikes (ticker TEXT, date TEXT, PRIMARY KEY(ticker,date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_momentum (ticker TEXT, date TEXT, direction TEXT, PRIMARY KEY(ticker,date,direction))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_short_interest (ticker TEXT, short_pct TEXT, dtc TEXT, date TEXT, PRIMARY KEY(ticker,date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_reddit_mentions (ticker TEXT, mentions TEXT, delta TEXT, date TEXT, PRIMARY KEY(ticker,date))")
cur.execute("CREATE TABLE IF NOT EXISTS sent_top_reddit (ticker TEXT, rank TEXT, mentions TEXT, date TEXT, PRIMARY KEY(ticker,date))")
con.commit()

print(f"[DEBUG] Using DB file: {DB_FILE}", file=sys.stderr)

def slack(msg:str, emoji=":newspaper:"):
    """Enhanced Slack messaging with better formatting"""
    try:
        webhook_url = SLACK.strip()
        if not webhook_url.startswith('http'):
            print(f"Invalid webhook URL: {webhook_url}", file=sys.stderr)
            return
        
        # Enhanced message formatting
        formatted_msg = f"{emoji} {msg}"
        requests.post(webhook_url, json={"text": formatted_msg}, timeout=8)
    except Exception as e:
        print("Slack error:", e, file=sys.stderr)

def seen(guid:str)->bool:
    cur.execute("SELECT 1 FROM sent_rss WHERE guid=?", (guid,))
    return cur.fetchone() is not None

def mark(guid):
    print(f"[DEBUG] Marking RSS: {guid}", file=sys.stderr)
    cur.execute("INSERT OR IGNORE INTO sent_rss VALUES (?)",(guid,))
    con.commit()

def seen_news(ticker:str, title:str)->bool:
    today = dt.date.today().isoformat()
    normalized_title = " ".join(title.lower().split())[:80]
    cur.execute("SELECT 1 FROM sent_news WHERE ticker=? AND title=? AND date=?", 
                (ticker, normalized_title, today))
    return cur.fetchone() is not None

def mark_news(ticker:str, title:str):
    today = dt.date.today().isoformat()
    normalized_title = " ".join(title.lower().split())[:80]
    print(f"[DEBUG] Marking news: {ticker} | {normalized_title} | {today}", file=sys.stderr)
    cur.execute("INSERT OR IGNORE INTO sent_news VALUES (?,?,?)", 
                (ticker, normalized_title, today))
    con.commit()

# New tracking functions
def seen_sec_filing(ticker:str, filing_type:str, date:str)->bool:
    cur.execute("SELECT 1 FROM sent_sec_filings WHERE ticker=? AND filing_type=? AND date=?", 
                (ticker, filing_type, date))
    return cur.fetchone() is not None

def mark_sec_filing(ticker:str, filing_type:str, date:str):
    cur.execute("INSERT OR IGNORE INTO sent_sec_filings VALUES (?,?,?)", 
                (ticker, filing_type, date))
    con.commit()

def seen_earnings(ticker:str, earnings_date:str)->bool:
    cur.execute("SELECT 1 FROM sent_earnings WHERE ticker=? AND earnings_date=?", 
                (ticker, earnings_date))
    return cur.fetchone() is not None

def mark_earnings(ticker:str, earnings_date:str):
    cur.execute("INSERT OR IGNORE INTO sent_earnings VALUES (?,?)", 
                (ticker, earnings_date))
    con.commit()

def seen_volume_spike(ticker:str, date:str)->bool:
    cur.execute("SELECT 1 FROM sent_volume_spikes WHERE ticker=? AND date=?", 
                (ticker, date))
    return cur.fetchone() is not None

def mark_volume_spike(ticker:str, date:str):
    cur.execute("INSERT OR IGNORE INTO sent_volume_spikes VALUES (?,?)", 
                (ticker, date))
    con.commit()

def seen_momentum(ticker:str, date:str, direction:str)->bool:
    cur.execute("SELECT 1 FROM sent_momentum WHERE ticker=? AND date=? AND direction=?", 
                (ticker, date, direction))
    return cur.fetchone() is not None

def mark_momentum(ticker:str, date:str, direction:str):
    cur.execute("INSERT OR IGNORE INTO sent_momentum VALUES (?,?,?)", 
                (ticker, date, direction))
    con.commit()

# New tracking functions for short interest and Reddit mentions
def seen_short_interest(ticker:str, short_pct:str, dtc:str, date:str)->bool:
    cur.execute("SELECT 1 FROM sent_short_interest WHERE ticker=? AND short_pct=? AND dtc=? AND date=?", 
                (ticker, short_pct, dtc, date))
    return cur.fetchone() is not None

def mark_short_interest(ticker:str, short_pct:str, dtc:str, date:str):
    cur.execute("INSERT OR IGNORE INTO sent_short_interest VALUES (?,?,?,?)", 
                (ticker, short_pct, dtc, date))
    con.commit()

def seen_reddit_mentions(ticker:str, mentions:str, delta:str, date:str)->bool:
    cur.execute("SELECT 1 FROM sent_reddit_mentions WHERE ticker=? AND mentions=? AND delta=? AND date=?", 
                (ticker, mentions, delta, date))
    return cur.fetchone() is not None

def mark_reddit_mentions(ticker:str, mentions:str, delta:str, date:str):
    cur.execute("INSERT OR IGNORE INTO sent_reddit_mentions VALUES (?,?,?,?)", 
                (ticker, mentions, delta, date))
    con.commit()

def seen_top_reddit(ticker:str, rank:str, mentions:str, date:str)->bool:
    cur.execute("SELECT 1 FROM sent_top_reddit WHERE ticker=? AND rank=? AND mentions=? AND date=?", 
                (ticker, rank, mentions, date))
    return cur.fetchone() is not None

def mark_top_reddit(ticker:str, rank:str, mentions:str, date:str):
    cur.execute("INSERT OR IGNORE INTO sent_top_reddit VALUES (?,?,?,?)", 
                (ticker, rank, mentions, date))
    con.commit()

#──── Ape Wisdom Reddit Mentions
def fetch_ape_snapshot() -> tuple[dict, dict]:
    """Fetch all Reddit mentions data from Ape Wisdom API in one call"""
    try:
        response = requests.get(APEW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        elif isinstance(data, dict) and 'data' in data:
            items = data['data']
        elif isinstance(data, list):
            items = data
        else:
            print(f"Unexpected Ape Wisdom response format: {type(data)}")
            return {}, {}
        
        # Create lookup dictionaries
        ape_by_tk = {}  # ticker -> (mentions_24h, delta)
        ape_by_rk = {}  # ticker -> rank
        
        for i, item in enumerate(items):
            if isinstance(item, dict):
                ticker = item.get('ticker', '').upper()
                if ticker:
                    mentions_24h = item.get('mentions', 0) or 0
                    mentions_24h_ago = item.get('mentions_24h_ago', 0) or 0
                    delta_mentions = mentions_24h - mentions_24h_ago
                    ape_by_tk[ticker] = (mentions_24h, delta_mentions)
                    ape_by_rk[ticker] = i + 1  # 1-based ranking
        
        return ape_by_tk, ape_by_rk
    except Exception as e:
        print(f"Error fetching Ape Wisdom snapshot: {e}")
        return {}, {}

def apewisdom_mentions(symbol: str) -> tuple[int, int]:
    """
    Return (mentions_24h, Δmentions_vs_24h_ago) for `symbol`.
    If the ticker isn't in the top-100 list, return (0, 0).

    Ape Wisdom docs: https://apewisdom.io/api/  (fields: ticker,
    mentions, mentions_24h_ago)
    """
    try:
        response = requests.get(APEW_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, dict) and 'results' in data:
            # Ape Wisdom API format with results array
            items = data['results']
        elif isinstance(data, dict) and 'data' in data:
            # Response wrapped in data object
            items = data['data']
        elif isinstance(data, list):
            # Direct array response
            items = data
        else:
            print(f"Unexpected Ape Wisdom response format: {type(data)}")
            return 0, 0
        
        # Find the ticker in the results
        for item in items:
            if isinstance(item, dict) and item.get('ticker', '').upper() == symbol.upper():
                mentions_24h = item.get('mentions', 0) or 0
                mentions_24h_ago = item.get('mentions_24h_ago', 0) or 0
                delta_mentions = mentions_24h - mentions_24h_ago
                return mentions_24h, delta_mentions
        
        # Ticker not found in top-100
        return 0, 0
        
    except Exception as e:
        print(f"Error fetching Ape Wisdom data for {symbol}: {e}")
        return 0, 0

def monitor_reddit_mentions(tickers):
    """Monitor Reddit mentions for tickers using Ape Wisdom"""
    print("🔥 Checking Reddit mentions via Ape Wisdom...", file=sys.stderr)
    today = dt.date.today().isoformat()
    
    # Fetch Ape Wisdom data once for all tickers
    ape_by_tk, ape_by_rk = fetch_ape_snapshot()  # 1 API hit per batch
    
    for ticker in tickers:
        try:
            mentions_24h, delta_mentions = ape_by_tk.get(ticker.upper(), (0, 0))
            
            if mentions_24h > 0:
                # Only alert if there are significant mentions or changes
                if mentions_24h >= 25 or abs(delta_mentions) >= 10:
                    # Create normalized values for comparison
                    mentions_str = str(mentions_24h)
                    delta_str = str(delta_mentions)
                    
                    # Check if we've already sent this exact data today
                    if not seen_reddit_mentions(ticker, mentions_str, delta_str, today):
                        # Determine emoji based on mention volume
                        if mentions_24h > 100:
                            emoji = "🔥"
                        elif mentions_24h > 50:
                            emoji = "📱"
                        else:
                            emoji = "💬"
                        
                        slack(f"*Reddit Mentions Alert*\n• *${ticker}* - {mentions_24h} mentions ({delta_mentions:+.0f})\n• 24h change: {delta_mentions:+.0f}", 
                              emoji)
                        mark_reddit_mentions(ticker, mentions_str, delta_str, today)
                    
        except Exception as e:
            print(f"Error monitoring Reddit mentions for {ticker}: {e}")

def monitor_top_reddit_mentions():
    """Monitor top 15 Reddit mentions and alert on position changes"""
    print("🏆 Monitoring top 15 Reddit mentions...", file=sys.stderr)
    today = dt.date.today().isoformat()
    
    try:
        # Fetch Ape Wisdom data
        ape_by_tk, ape_by_rk = fetch_ape_snapshot()
        
        # Get top 15 by mentions
        top_tickers = []
        for ticker, (mentions, delta) in ape_by_tk.items():
            if mentions > 0:  # Only include tickers with mentions
                top_tickers.append((ticker, mentions, delta))
        
        # Sort by mentions (descending) and take top 15
        top_tickers.sort(key=lambda x: x[1], reverse=True)
        top_15 = top_tickers[:15]
        
        if top_15:
            blocks = []
            for i, (ticker, mentions, delta) in enumerate(top_15, 1):
                rank = str(i)
                mentions_str = str(mentions)
                
                # Check if we've already sent this exact data today
                if not seen_top_reddit(ticker, rank, mentions_str, today):
                    # Determine emoji based on rank
                    if i <= 3:
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                    elif i <= 5:
                        emoji = "🔥"
                    elif i <= 10:
                        emoji = "📈"
                    else:
                        emoji = "📊"
                    
                    line = f"{emoji} *#{i}* *${ticker}* - {mentions:,} mentions ({delta:+,})"
                    blocks.append(line)
                    mark_top_reddit(ticker, rank, mentions_str, today)
            
            # Send combined alert if we have changes
            if blocks:
                slack("*🏆 Top 15 Reddit Mentions Update*\n" + "\n".join(blocks), emoji=":fire:")
            else:
                print("No changes in top 15 Reddit mentions", file=sys.stderr)
        else:
            print("No Reddit mention data available", file=sys.stderr)
            
    except Exception as e:
        print(f"Error monitoring top Reddit mentions: {e}")

#──── SEC Filing Monitor
def monitor_sec_filings(tickers):
    """Monitor SEC filings for specified tickers"""
    today = dt.date.today()
    cutoff_date = today - dt.timedelta(days=SEC_FILING_DAYS_BACK)
    
    for ticker in tickers:
        try:
            # Get company info to find CIK
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try to get CIK from various sources
            cik = None
            if 'cik' in info and info['cik']:
                cik = str(info['cik']).zfill(10)  # SEC requires 10-digit CIK
            else:
                # Try to find CIK from company name
                company_name = info.get('longName', ticker)
                # This is a simplified approach - in production you'd want a proper CIK lookup
                continue
            
            # SEC RSS feed for company filings
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=exclude&output=atom&count=40"
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                try:
                    # Parse filing date
                    filing_date = dt.datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S%z").date()
                    if filing_date >= cutoff_date:
                        # Extract filing type from title or category
                        filing_type = None
                        if hasattr(entry, 'category') and entry.category:
                            filing_type = entry.category.get('term', '')
                        else:
                            # Try to extract from title
                            title_lower = entry.title.lower()
                            for ft in SEC_FILING_TYPES:
                                if ft.lower() in title_lower:
                                    filing_type = ft
                                    break
                        
                        if filing_type in SEC_FILING_TYPES:
                            filing_date_str = filing_date.isoformat()
                            if not seen_sec_filing(ticker, filing_type, filing_date_str):
                                slack(f"*SEC Filing Alert*\n• *${ticker}* - {filing_type}\n• <{entry.link}|{entry.title[:100]}>\n• Date: {filing_date_str}", 
                                      ":file_folder:")
                                mark_sec_filing(ticker, filing_type, filing_date_str)
                except Exception as e:
                    print(f"Error parsing SEC filing for {ticker}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error monitoring SEC filings for {ticker}: {e}")

#──── Earnings Calendar Monitor
def monitor_earnings_calendar(tickers):
    """Monitor upcoming earnings dates"""
    today = dt.date.today()
    cutoff_date = today + dt.timedelta(days=EARNINGS_DAYS_AHEAD)
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            
            if calendar is not None and isinstance(calendar, dict) and len(calendar) > 0:
                for earnings_date_str, earnings_data in calendar.items():
                    try:
                        earnings_date = dt.datetime.strptime(earnings_date_str, "%Y-%m-%d").date()
                        
                        if today <= earnings_date <= cutoff_date:
                            if not seen_earnings(ticker, earnings_date_str):
                                days_until = (earnings_date - today).days
                                estimate = earnings_data.get('EPS Estimate', 'N/A')
                                
                                slack(f"*Earnings Alert*\n• *${ticker}* - {earnings_date_str}\n• Days until: {days_until}\n• EPS Estimate: {estimate}", 
                                      ":calendar:")
                                mark_earnings(ticker, earnings_date_str)
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"Error checking earnings for {ticker}: {e}")

#──── Volume Spike Detector
def detect_volume_spikes(tickers):
    """Detect unusual volume spikes"""
    today = dt.date.today().isoformat()
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if len(hist) >= 2:
                current_volume = hist.iloc[-1]['Volume']
                avg_volume = hist.iloc[:-1]['Volume'].mean()
                
                if current_volume > (avg_volume * VOLUME_SPIKE_THRESHOLD):
                    if not seen_volume_spike(ticker, today):
                        ratio = current_volume / avg_volume
                        slack(f"*Volume Spike Alert*\n• *${ticker}* - {ratio:.1f}x average volume\n• Current: {current_volume:,.0f}\n• Average: {avg_volume:,.0f}", 
                              ":chart_with_upwards_trend:")
                        mark_volume_spike(ticker, today)
                        
        except Exception as e:
            print(f"Error detecting volume spike for {ticker}: {e}")

#──── Price Momentum Alert
def detect_price_momentum(tickers):
    """Alert on significant price movements"""
    today = dt.date.today().isoformat()
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            
            if len(hist) >= 2:
                current_price = hist.iloc[-1]['Close']
                prev_price = hist.iloc[-2]['Close']
                change_pct = (current_price - prev_price) / prev_price
                
                if abs(change_pct) > PRICE_MOMENTUM_THRESHOLD:
                    direction = "up" if change_pct > 0 else "down"
                    if not seen_momentum(ticker, today, direction):
                        emoji = ":rocket:" if direction == "up" else ":chart_with_downwards_trend:"
                        slack(f"*Price Momentum Alert*\n• *${ticker}* - {change_pct*100:+.1f}%\n• ${current_price:.2f} (prev: ${prev_price:.2f})\n• Direction: {direction.upper()}", 
                              emoji)
                        mark_momentum(ticker, today, direction)
                        
        except Exception as e:
            print(f"Error detecting momentum for {ticker}: {e}")

#──── Enhanced Sentiment Analysis
def analyze_sentiment(text):
    """Basic sentiment analysis using keyword matching"""
    positive_words = ['up', 'gain', 'rise', 'positive', 'beat', 'exceed', 'growth', 'profit', 'surge', 'rally', 'bullish']
    negative_words = ['down', 'loss', 'fall', 'negative', 'miss', 'decline', 'drop', 'crash', 'plunge', 'bearish', 'sell']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return 'positive', positive_count - negative_count
    elif negative_count > positive_count:
        return 'negative', negative_count - positive_count
    else:
        return 'neutral', 0

def scan_headlines_enhanced(tickers):
    """Enhanced headline scanning with sentiment analysis"""
    today = dt.date.today()
    sent_count = 0
    print(f"🔍 Scanning headlines for {len(tickers)} tickers on {today}...", file=sys.stderr)
    
    for tk in tickers:
        if sent_count >= 20:
            break
            
        try:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={tk}&region=US&lang=en-US"
            print(f"📡 Checking {tk}: {url}", file=sys.stderr)
            feed = feedparser.parse(url)
            print(f"   Found {len(feed.entries)} entries", file=sys.stderr)
            
            for e in feed.entries:
                if sent_count >= 20:
                    break
                    
                ts = e.get("published_parsed") or e.get("updated_parsed")
                if not ts or dt.date(*ts[:3]) != today:
                    print(f"   Skipping {tk}: date mismatch", file=sys.stderr)
                    continue
                    
                if seen_news(tk, e.title):
                    print(f"   Skipping {tk}: already seen", file=sys.stderr)
                    continue
                
                # Analyze sentiment
                sentiment, score = analyze_sentiment(e.title)
                
                # Send alerts for all news (removed strict sentiment filter)
                src = e.get("source", {}).get("title", "News")
                sentiment_emoji = ":green_circle:" if sentiment == "positive" else ":red_circle:" if sentiment == "negative" else ":white_circle:"
                
                print(f"   Sending {tk}: {e.title[:50]}...", file=sys.stderr)
                slack(f"*${tk}* — <{e.link}|{e.title}>  _({src})_ {sentiment_emoji} {sentiment.upper()}", 
                      ":newspaper:")
                mark_news(tk, e.title)
                sent_count += 1
                    
        except Exception as e:
            print(f"Error scanning headlines for {tk}: {e}")

#──── Original functions (keeping for compatibility)
def scan_static():
    today = dt.date.today()
    print(f"🔍 Scanning static RSS feeds for {today}...", file=sys.stderr)
    for label,url in RSS_STATIC.items():
        print(f"📡 Checking {label}: {url}", file=sys.stderr)
        feed = feedparser.parse(url)
        print(f"   Found {len(feed.entries)} entries", file=sys.stderr)
        for e in feed.entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            if not ts or dt.date(*ts[:3])!=today or seen(e.id): 
                print(f"   Skipping: date={ts}, seen={seen(e.id)}", file=sys.stderr)
                continue
            print(f"   Sending: {e.title[:50]}...", file=sys.stderr)
            slack(f"*{label}*\n• <{e.link}|{e.title[:240]}>\n<{e.link}>"); mark(e.id)

def notion_tickers():
    if not (NOTION_TOK and NOTION_DB): 
        print("Notion not configured - skipping live ticker list", file=sys.stderr)
        return []
    try:
        nc = Client(auth=NOTION_TOK)
        res = nc.databases.query(database_id=NOTION_DB, page_size=200)["results"]
        tickers = [p["properties"]["Title"]["title"][0]["plain_text"].upper() for p in res if p["properties"]["Title"]["title"]]
        print(f"Found {len(tickers)} tickers from Notion: {tickers}", file=sys.stderr)
        return tickers
    except Exception as e:
        print("Notion API error:", e, file=sys.stderr); return []

def buzz_tickers():
    today = dt.date.today().isoformat(); buzz = set()
    for sub in SUBREDDITS:
        try:
            rows = requests.get("https://yolostocks.live/api/top",
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

def short_interest():
    today = dt.date.today().isoformat()
    
    # Fetch Ape Wisdom data once for all tickers
    ape_by_tk, ape_by_rk = fetch_ape_snapshot()  # 1 API hit per batch
    
    # Collect short interest data
    siren_rows = []
    for sym in SI_SET:
        try:
            info=yf.Ticker(sym).get_info()
            si=float(info.get("sharesShort",0)); flo=float(info.get("floatShares")or info.get("sharesOutstanding") or 0)
            vol=float(info.get("averageVolume",0))
        except Exception: continue
        if not (si and flo and vol): continue
        pct,dtc=si/flo*100, si/vol
        
        if pct>=20 or dtc>=10:
            siren_rows.append((sym, pct, dtc))
    
    # Send combined alerts with Reddit data
    if siren_rows:
        blocks = []
        for tkr, short_pct, dtc in siren_rows:
            m24, delta = ape_by_tk.get(tkr, (0, 0))
            rank = ape_by_rk.get(tkr)  # None if not in top-100
            heat = "🚀" if m24 > 500 else "🟡" if m24 > 100 else "🟢"
            
            # Create normalized values for comparison
            short_pct_str = f"{short_pct:.1f}"
            dtc_str = f"{dtc:.1f}"
            
            # Check if we've already sent this exact data today
            if not seen_short_interest(tkr, short_pct_str, dtc_str, today):
                line = (
                    f"{heat} *${tkr}* — Short {short_pct:.1f}% | DTC {dtc:.1f}×"
                    f"\n • WSB 24 h: *{m24:,}* ({delta:+,})"
                    + (f" | Rank: #{rank}" if rank else "")
                )
                blocks.append(line)
                mark_short_interest(tkr, short_pct_str, dtc_str, today)
        
        # Send combined alert if we have data
        if blocks:
            slack("\n".join(blocks), emoji=":rotating_light:")

#──── Enhanced Main Function
def main():
    print("🚀 Starting Enhanced Market Radar Bot...", file=sys.stderr)
    
    # Get all tickers to monitor
    all_tickers = set(notion_tickers()) | MANUAL_EXTRA | buzz_tickers()
    
    # Original features
    scan_static()
    scan_headlines_enhanced(sorted(all_tickers))
    if SI_SET: short_interest()
    
    # New enhanced features
    print(f"📊 Monitoring {len(all_tickers)} tickers for enhanced features...", file=sys.stderr)
    
    # SEC filings monitoring
    print("📁 Checking SEC filings...", file=sys.stderr)
    monitor_sec_filings(sorted(all_tickers))
    
    # Earnings calendar
    print("📅 Checking earnings calendar...", file=sys.stderr)
    monitor_earnings_calendar(sorted(all_tickers))
    
    # Volume spikes
    print("📈 Detecting volume spikes...", file=sys.stderr)
    detect_volume_spikes(sorted(all_tickers))
    
    # Price momentum
    print("💹 Detecting price momentum...", file=sys.stderr)
    detect_price_momentum(sorted(all_tickers))
    
    # Top 15 Reddit mentions
    print("🏆 Monitoring top 15 Reddit mentions...", file=sys.stderr)
    monitor_top_reddit_mentions()
    
    print("✅ Enhanced Market Radar Bot completed!", file=sys.stderr)

if __name__=="__main__": main() 