#!/usr/bin/env python3
"""
Serverless handler for stock analysis with Ape Wisdom Reddit mention data.
Runs on AWS Lambda (Python 3.12) behind HTTP API Gateway.
"""

import json
import requests
import yfinance as yf
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

# API endpoints
APEW_URL = "https://apewisdom.io/api/v1.0/filter/wallstreetbets"

# International ticker aliases
ALIAS = {"URNM": "URNM.L", "RACE": "RACE.MI"}

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
                mentions_24h = item.get('mentions', 0)
                mentions_24h_ago = item.get('mentions_24h_ago', 0)
                delta_mentions = mentions_24h - mentions_24h_ago
                return mentions_24h, delta_mentions
        
        # Ticker not found in top-100
        return 0, 0
        
    except Exception as e:
        print(f"Error fetching Ape Wisdom data for {symbol}: {e}")
        return 0, 0

def get_stock_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch comprehensive stock data including price, short interest, and Reddit mentions.
    """
    try:
        # Apply ticker alias if needed
        yahoo_symbol = ALIAS.get(symbol, symbol)
        
        # Get basic stock info
        stock = yf.Ticker(yahoo_symbol)
        info = stock.info
        
        # Get current price data
        hist = stock.history(period="2d")
        current_price = hist.iloc[-1]['Close'] if len(hist) > 0 else 0
        prev_price = hist.iloc[-2]['Close'] if len(hist) > 1 else current_price
        price_change = ((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0
        
        # Handle GBX currency conversion for LSE stocks
        price_display = current_price
        currency = info.get('currency', 'USD')
        
        if yahoo_symbol.endswith('.L') and currency == 'GBX':
            try:
                gbp_eur = yf.Ticker("GBPEUR=X").info["regularMarketPrice"] / 100
                price_eur = current_price * gbp_eur
                price_display = f"€{price_eur:,.2f} (GBX {current_price:.0f})"
            except Exception as e:
                print(f"Error converting GBX to EUR for {symbol}: {e}")
                price_display = f"GBX {current_price:.0f}"
        elif yahoo_symbol.endswith('.MI'):
            # Borsa Italiana stocks are already in EUR
            price_display = f"€{current_price:,.2f}"
        
        # Get short interest data (wrap in try/except for EU tickers)
        try:
            shares_short = info.get('sharesShort', 0)
            float_shares = info.get('floatShares', info.get('sharesOutstanding', 0))
            short_interest_pct = (shares_short / float_shares * 100) if float_shares > 0 else 0
        except Exception:
            shares_short = "N/A"
            float_shares = "N/A"
            short_interest_pct = "N/A"
        
        # Get Ape Wisdom Reddit mentions
        mentions_24h, delta_mentions = apewisdom_mentions(symbol)
        
        # Determine exchange name
        exchange = "Unknown"
        if yahoo_symbol.endswith('.L'):
            exchange = "LSE"
        elif yahoo_symbol.endswith('.MI'):
            exchange = "Borsa Italiana"
        
        return {
            'symbol': symbol.upper(),
            'yahoo_symbol': yahoo_symbol,
            'current_price': current_price,
            'price_display': price_display,
            'price_change_pct': round(price_change, 2),
            'volume': info.get('volume', 0),
            'market_cap': info.get('marketCap', 0),
            'short_interest_pct': short_interest_pct,
            'shares_short': shares_short,
            'float_shares': float_shares,
            'reddit_mentions_24h': mentions_24h,
            'reddit_mentions_change': delta_mentions,
            'company_name': info.get('longName', symbol),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'exchange': exchange,
            'currency': currency,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return {
            'symbol': symbol.upper(),
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def create_slack_block_kit(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Slack Block Kit card for the stock analysis.
    """
    if 'error' in data:
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Error analyzing {data['symbol']}*\n{data['error']}"
                    }
                }
            ]
        }
    
    # Determine emoji based on price change
    price_emoji = "🚀" if data['price_change_pct'] > 5 else "📈" if data['price_change_pct'] > 0 else "📉" if data['price_change_pct'] < -5 else "➡️"
    
    # Determine Reddit sentiment emoji
    reddit_emoji = "🔥" if data['reddit_mentions_24h'] > 100 else "📱" if data['reddit_mentions_24h'] > 10 else "💤"
    
    # Format numbers
    market_cap_formatted = f"${data['market_cap']/1e9:.1f}B" if data['market_cap'] > 1e9 else f"${data['market_cap']/1e6:.1f}M"
    volume_formatted = f"{data['volume']/1e6:.1f}M" if data['volume'] > 1e6 else f"{data['volume']/1e3:.1f}K"
    
    # Format short interest
    short_interest_text = f"{data['short_interest_pct']:.1f}%" if isinstance(data['short_interest_pct'], (int, float)) else str(data['short_interest_pct'])
    
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{price_emoji} {data['symbol']} Analysis",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Price:* {data['price_display']} ({data['price_change_pct']:+.2f}%)"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Market Cap:* {market_cap_formatted}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Volume:* {volume_formatted}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Short Interest:* {short_interest_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Reddit Mentions:* {reddit_emoji} {data['reddit_mentions_24h']} ({data['reddit_mentions_change']:+.0f})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Sector:* {data['sector']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{data['company_name']}*\n{data['industry']}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📊 Analysis generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} • Exchange: {data['exchange']}"
                    }
                ]
            }
        ]
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    Expects: {"ticker": "SYMBOL"} in the request body
    Returns: Slack Block Kit formatted response
    """
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        ticker = body.get('ticker', '').strip().upper()
        
        if not ticker:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing or invalid ticker symbol'
                })
            }
        
        # Get stock data
        stock_data = get_stock_data(ticker)
        
        # Create Slack Block Kit response
        slack_response = create_slack_block_kit(stock_data)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(slack_response)
        }
        
    except Exception as e:
        print(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }

# For local testing
if __name__ == "__main__":
    # Test the handler
    test_event = {
        'body': json.dumps({'ticker': 'TSLA'})
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2)) 