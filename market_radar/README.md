# Market Radar Slack Bot

A single-run script for market monitoring and Slack alerts with Reddit buzz tracking.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Set up Slack:**
   - **Option A (Webhook)**: Create a webhook at https://api.slack.com/apps → Incoming Webhooks
   - **Option B (Bot Token)**: Create a Slack app with bot token scopes: `chat:write`, `chat:write.public`

4. **Get API tokens:**
   - **IEX Cloud**: Get free token at https://iexcloud.io/
   - **Reddit API**: Optional for enhanced Reddit tracking

## Usage

Run the bot manually:
```bash
python radar.py
```

## Features

- **Watch List Monitoring**: Tracks configured ticker lists for alerts
- **Reddit Buzz Detection**: Monitors Reddit mentions with configurable thresholds
- **IEX Market Data**: Real-time stock data integration
- **Slack Alerts**: Webhook or bot token support
- **Alert Tracking**: SQLite database prevents duplicate alerts
- **Error Handling**: Graceful error handling with Slack notifications

## Configuration

### API Tokens & Webhooks
- `SLACK_WEBHOOK`: Your Slack webhook URL (preferred)
- `SLACK_BOT_TOKEN`: Fallback Slack bot token
- `IEX_TOKEN`: IEX Cloud API token for stock data

### Watch Lists
- `SI_TICKERS`: Comma-separated list of tickers to monitor
- `NEWS_TICKERS_EXTRA`: Additional tickers for headline scanning

### Reddit Buzz Settings
- `MENTION_MIN`: Minimum mentions to trigger alert (default: 25)
- `ACCEL_FACTOR`: Acceleration factor for trend detection (default: 3)
- `SUBREDDITS`: Comma-separated list of subreddits to monitor

## Database

The bot uses `sent.db` (auto-created) to track sent alerts and prevent spam.

## Integration

This bot integrates with:
- IEX Cloud for real-time stock data
- Reddit API for social sentiment
- Your existing momentum screening data

Modify the `run_market_scan()` method in `radar.py` to connect with additional market data sources. 