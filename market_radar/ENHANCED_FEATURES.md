# Enhanced Market Radar Bot Features

## 🚀 New Features Implemented

The market radar bot has been significantly enhanced with the following new features:

### 1. 📁 SEC Filing Monitoring
**What it does:** Monitors SEC filings for important documents like 8-K, 10-K, 10-Q, and Form 4 filings.

**Configuration:**
- `SEC_FILING_DAYS_BACK`: How many days back to check (default: 1)
- `SEC_FILING_TYPES`: Types of filings to monitor

**Alert Format:**
```
📁 *SEC Filing Alert*
• *$TSLA* - 8-K
• [Filing Title Link]
• Date: 2024-01-15
```

### 2. 📅 Earnings Calendar Integration
**What it does:** Proactively alerts about upcoming earnings dates.

**Configuration:**
- `EARNINGS_DAYS_AHEAD`: How many days ahead to alert (default: 7)

**Alert Format:**
```
📅 *Earnings Alert*
• *$TSLA* - 2024-01-20
• Days until: 5
• EPS Estimate: 0.85
```

### 3. 📈 Volume Spike Detection
**What it does:** Detects unusual volume activity that might indicate significant market interest.

**Configuration:**
- `VOLUME_SPIKE_THRESHOLD`: Multiplier for average volume (default: 2.0x)

**Alert Format:**
```
📈 *Volume Spike Alert*
• *$TSLA* - 3.2x average volume
• Current: 45,678,901
• Average: 14,234,567
```

### 4. 💹 Price Momentum Alerts
**What it does:** Alerts on significant price movements (>5% by default).

**Configuration:**
- `PRICE_MOMENTUM_THRESHOLD`: Percentage change threshold (default: 0.05 = 5%)

**Alert Format:**
```
🚀 *Price Momentum Alert*
• *$TSLA* - +12.5%
• $245.67 (prev: $218.50)
• Direction: UP
```

### 5. 🔥 Reddit Mentions via Ape Wisdom
**What it does:** Monitors Reddit mentions from r/wallstreetbets using Ape Wisdom API.

**Features:**
- Real-time Reddit mention tracking
- 24-hour mention counts and changes
- Smart filtering (only alerts on significant mentions)
- Emoji indicators based on mention volume
- **Duplicate prevention** - Only sends alerts when data changes
- **Efficient API usage** - Single API call for all tickers
- **Integrated alerts** - Reddit data combined with short interest alerts

**Note:** Reddit mentions are now integrated into the enhanced short interest alerts rather than sent as separate alerts to prevent duplicates.

### 6. 🏆 Top 15 Reddit Mentions Tracking
**What it does:** Monitors the top 15 most mentioned tickers on r/wallstreetbets and alerts on position changes.

**Features:**
- Tracks top 15 Reddit mentions by volume
- Only alerts when positions change (new entries, rank changes, mention count changes)
- Rank-based emoji indicators (🥇🥈🥉 for top 3, 🔥 for top 5, 📈 for top 10, 📊 for others)
- **Duplicate prevention** - Only sends alerts when data changes
- **Efficient API usage** - Single Ape Wisdom call for all data

**Alert Format:**
```
🏆 *Top 15 Reddit Mentions Update*
🥇 *#1* *$SPY* - 495 mentions (+156)
🥈 *#2* *$NVDA* - 482 mentions (+291)
🥉 *#3* *$META* - 448 mentions (+371)
🔥 *#4* *$MSFT* - 433 mentions (+392)
🔥 *#5* *$AMD* - 231 mentions (-74)
```

### 7. 🚨 Enhanced Short Interest with Reddit Data
**What it does:** Combines short interest data with Reddit mentions for comprehensive alerts.

**Features:**
- Short interest percentage and Days to Cover (DTC)
- Integrated Reddit mention data
- Ranking information (if in top-100)
- Heat indicators based on mention volume
- **Duplicate prevention** - Only alerts when data changes
- **Efficient API usage** - Single Ape Wisdom call for all tickers

**Alert Format:**
```
🚀 *$TSLA* — Short 25.4% | DTC 3.2×
 • WSB 24 h: *1,234* (+56) | Rank: #15
```

### 5. 🧠 Enhanced Sentiment Analysis
**What it does:** Analyzes news headlines for sentiment and only alerts on significant sentiment.

**Features:**
- Keyword-based sentiment scoring
- Only sends alerts for headlines with strong sentiment (score ≥ 2)
- Color-coded sentiment indicators

**Alert Format:**
```
📰 *$TSLA* — [News Headline Link] _(Source)_ 🟢 POSITIVE
```

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file or GitHub Secrets:

## 🚫 Duplicate Prevention System

The enhanced bot includes comprehensive duplicate prevention to avoid spam:

### **How It Works:**
- **Daily Tracking**: Each alert type is tracked per day
- **Data Normalization**: Values are normalized for consistent comparison
- **Change Detection**: Only sends alerts when data actually changes
- **Database Storage**: Uses SQLite to track sent alerts

### **Protected Alert Types:**
- ✅ **News Headlines** - Prevents duplicate news alerts
- ✅ **Short Interest** - Only alerts when SI/DTC values change
- ✅ **Reddit Mentions** - Only alerts when mention counts change
- ✅ **SEC Filings** - Prevents duplicate filing alerts
- ✅ **Earnings** - Prevents duplicate earnings alerts
- ✅ **Volume Spikes** - Prevents duplicate volume alerts
- ✅ **Price Momentum** - Prevents duplicate momentum alerts

### **Example:**
- **First run**: Sends short interest alert for $TSLA (25.4% SI)
- **Second run**: No alert (same data)
- **Third run**: New alert only if SI changes to 26.1%

```bash
# Enhanced Features Configuration
VOLUME_SPIKE_THRESHOLD=2.0          # Volume spike multiplier
PRICE_MOMENTUM_THRESHOLD=0.05       # Price change threshold (5%)
EARNINGS_DAYS_AHEAD=7               # Days ahead for earnings alerts
SEC_FILING_DAYS_BACK=1              # Days back for SEC filings

# Existing Configuration
SLACK_WEBHOOK=your_webhook_url
SI_TICKERS=SANA,TMC,EOSE,GWH,ATLX,NBIS,VRT,BEAM,FLNC,BYDDY
NEWS_TICKERS_EXTRA=TSLA,NVDA,AAPL
MENTION_MIN=25
ACCEL_FACTOR=3
SUBREDDITS=wallstreetbets,stocks,options
```

### GitHub Secrets

For GitHub Actions, add these secrets:

| Secret Name | Description | Default Value |
|-------------|-------------|---------------|
| `VOLUME_SPIKE_THRESHOLD` | Volume spike multiplier | `2.0` |
| `PRICE_MOMENTUM_THRESHOLD` | Price change threshold | `0.05` |
| `EARNINGS_DAYS_AHEAD` | Days ahead for earnings | `7` |
| `SEC_FILING_DAYS_BACK` | Days back for SEC filings | `1` |

## 📊 Database Schema

The enhanced bot uses additional database tables:

```sql
-- SEC filings tracking
CREATE TABLE sent_sec_filings (
    ticker TEXT, 
    filing_type TEXT, 
    date TEXT, 
    PRIMARY KEY(ticker,filing_type,date)
);

-- Earnings alerts tracking
CREATE TABLE sent_earnings (
    ticker TEXT, 
    earnings_date TEXT, 
    PRIMARY KEY(ticker,earnings_date)
);

-- Volume spike tracking
CREATE TABLE sent_volume_spikes (
    ticker TEXT, 
    date TEXT, 
    PRIMARY KEY(ticker,date)
);

-- Price momentum tracking
CREATE TABLE sent_momentum (
    ticker TEXT, 
    date TEXT, 
    direction TEXT, 
    PRIMARY KEY(ticker,date,direction)
);
```

## 🎯 Usage

### Local Testing
```bash
cd market_radar
python3 radar_enhanced.py
```

### GitHub Actions
The enhanced bot runs automatically via GitHub Actions:
- **Schedule**: Hourly during US trading hours (10-20 UTC, Mon-Fri)
- **Manual**: Can be triggered manually via workflow_dispatch

## 🔍 Monitoring & Debugging

### Log Output
The enhanced bot provides detailed logging:
```
🚀 Starting Enhanced Market Radar Bot...
📊 Monitoring 3 tickers for enhanced features...
📁 Checking SEC filings...
📅 Checking earnings calendar...
📈 Detecting volume spikes...
💹 Detecting price momentum...
✅ Enhanced Market Radar Bot completed!
```

### Database Inspection
```bash
# Check what alerts have been sent
sqlite3 sent.db "SELECT * FROM sent_sec_filings;"
sqlite3 sent.db "SELECT * FROM sent_earnings;"
sqlite3 sent.db "SELECT * FROM sent_volume_spikes;"
sqlite3 sent.db "SELECT * FROM sent_momentum;"
```

## 🚨 Alert Types & Emojis

| Feature | Emoji | Description |
|---------|-------|-------------|
| SEC Filings | 📁 | Important regulatory filings |
| Earnings | 📅 | Upcoming earnings dates |
| Volume Spikes | 📈 | Unusual trading volume |
| Price Momentum Up | 🚀 | Significant price increases |
| Price Momentum Down | 📉 | Significant price decreases |
| News (Positive) | 📰 + 🟢 | Positive sentiment news |
| News (Negative) | 📰 + 🔴 | Negative sentiment news |
| Short Interest | 🚨 | High short interest alerts |

## ⚡ Performance Considerations

- **Rate Limiting**: All features include rate limiting to prevent API abuse
- **Error Handling**: Graceful error handling for all external APIs
- **Duplicate Prevention**: Comprehensive duplicate detection across all alert types
- **Database Efficiency**: Optimized database queries and indexing

## 🔮 Future Enhancements

Potential future features to consider:
- [ ] Options flow monitoring
- [ ] Institutional ownership changes
- [ ] Technical indicator alerts (RSI, MACD, etc.)
- [ ] Web dashboard for configuration
- [ ] Alert effectiveness analytics
- [ ] Custom alert thresholds per ticker
- [ ] Integration with trading platforms

## 🛠️ Troubleshooting

### Common Issues

1. **No SEC Filing Alerts**: Some companies may not have easily accessible CIK numbers
2. **No Earnings Alerts**: Earnings data may not be available for all tickers
3. **API Rate Limits**: Yahoo Finance and SEC APIs have rate limits
4. **Database Issues**: Check database permissions and disk space

### Debug Mode
```bash
# Test individual features
python3 -c "import radar_enhanced; radar_enhanced.monitor_sec_filings(['TSLA'])"
python3 -c "import radar_enhanced; radar_enhanced.detect_volume_spikes(['TSLA'])"
```

## 📈 Expected Results

With the enhanced features, you should see:
- **More comprehensive market monitoring**
- **Earlier alerts for important events**
- **Better sentiment-filtered news**
- **Technical analysis alerts**
- **Reduced noise through intelligent filtering**

The enhanced bot provides a much more comprehensive view of market activity and should help identify trading opportunities earlier and more effectively. 