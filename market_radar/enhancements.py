#!/usr/bin/env python3
"""
Market Radar Bot Enhancements
Additional features that could be integrated into the main radar.py
"""

import requests
import feedparser
from datetime import datetime, timedelta
import yfinance as yf

def sec_filings_monitor(tickers, days_back=1):
    """
    Monitor SEC filings for specified tickers
    Uses SEC RSS feeds for recent filings
    """
    today = datetime.now()
    cutoff_date = today - timedelta(days=days_back)
    
    for ticker in tickers:
        try:
            # SEC RSS feed for company filings
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=exclude&output=atom&count=40"
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                # Parse filing date
                filing_date = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S%z")
                if filing_date.date() >= cutoff_date.date():
                    # Check for important filing types
                    filing_type = entry.get('category', {}).get('term', '')
                    if filing_type in ['4', '8-K', '10-K', '10-Q']:
                        return {
                            'ticker': ticker,
                            'filing_type': filing_type,
                            'title': entry.title,
                            'link': entry.link,
                            'date': filing_date.strftime("%Y-%m-%d")
                        }
        except Exception as e:
            print(f"Error monitoring SEC filings for {ticker}: {e}")
    
    return None

def earnings_calendar_check(tickers, days_ahead=7):
    """
    Check upcoming earnings dates for specified tickers
    Uses Yahoo Finance for earnings data
    """
    earnings_alerts = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            
            if calendar is not None and isinstance(calendar, dict) and len(calendar) > 0:
                # Handle calendar as dictionary
                for earnings_date_str, earnings_data in calendar.items():
                    try:
                        earnings_date = datetime.strptime(earnings_date_str, "%Y-%m-%d")
                        days_until = (earnings_date - datetime.now()).days
                        
                        if 0 <= days_until <= days_ahead:
                            earnings_alerts.append({
                                'ticker': ticker,
                                'earnings_date': earnings_date.strftime("%Y-%m-%d"),
                                'days_until': days_until,
                                'estimate': earnings_data.get('EPS Estimate', 'N/A'),
                                'actual': earnings_data.get('EPS Actual', 'N/A')
                            })
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Error checking earnings for {ticker}: {e}")
    
    return earnings_alerts

def options_flow_monitor(tickers):
    """
    Monitor unusual options activity
    Note: This would require a paid API like CBOE or similar
    """
    # Placeholder for options flow monitoring
    # Would need integration with options data provider
    pass

def institutional_ownership_changes(tickers):
    """
    Monitor institutional ownership changes
    Uses SEC 13F filings data
    """
    # Placeholder for institutional ownership monitoring
    # Would need to parse 13F filings
    pass

def market_sentiment_analysis(tickers):
    """
    Basic sentiment analysis using news headlines
    """
    sentiment_scores = {}
    
    for ticker in tickers:
        try:
            # Get recent news headlines
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
            feed = feedparser.parse(url)
            
            # Simple keyword-based sentiment
            positive_words = ['up', 'gain', 'rise', 'positive', 'beat', 'exceed', 'growth', 'profit']
            negative_words = ['down', 'loss', 'fall', 'negative', 'miss', 'decline', 'drop', 'crash']
            
            positive_count = 0
            negative_count = 0
            
            for entry in feed.entries[:10]:  # Last 10 headlines
                title = entry.title.lower()
                positive_count += sum(1 for word in positive_words if word in title)
                negative_count += sum(1 for word in negative_words if word in title)
            
            if positive_count > negative_count:
                sentiment = 'positive'
            elif negative_count > positive_count:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            sentiment_scores[ticker] = {
                'sentiment': sentiment,
                'positive_score': positive_count,
                'negative_score': negative_count
            }
            
        except Exception as e:
            print(f"Error analyzing sentiment for {ticker}: {e}")
    
    return sentiment_scores

def volume_spike_detector(tickers, threshold=2.0):
    """
    Detect unusual volume spikes
    """
    volume_alerts = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if len(hist) >= 2:
                current_volume = hist.iloc[-1]['Volume']
                avg_volume = hist.iloc[:-1]['Volume'].mean()
                
                if current_volume > (avg_volume * threshold):
                    volume_alerts.append({
                        'ticker': ticker,
                        'current_volume': current_volume,
                        'avg_volume': avg_volume,
                        'ratio': current_volume / avg_volume
                    })
        except Exception as e:
            print(f"Error detecting volume spike for {ticker}: {e}")
    
    return volume_alerts

def price_momentum_alert(tickers, threshold=0.05):
    """
    Alert on significant price movements
    """
    momentum_alerts = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            
            if len(hist) >= 2:
                current_price = hist.iloc[-1]['Close']
                prev_price = hist.iloc[-2]['Close']
                change_pct = (current_price - prev_price) / prev_price
                
                if abs(change_pct) > threshold:
                    momentum_alerts.append({
                        'ticker': ticker,
                        'change_pct': change_pct * 100,
                        'current_price': current_price,
                        'prev_price': prev_price,
                        'direction': 'up' if change_pct > 0 else 'down'
                    })
        except Exception as e:
            print(f"Error detecting momentum for {ticker}: {e}")
    
    return momentum_alerts

# Example usage functions
def run_enhanced_monitoring(tickers):
    """
    Run all enhanced monitoring features
    """
    alerts = []
    
    # SEC filings
    sec_alert = sec_filings_monitor(tickers)
    if sec_alert:
        alerts.append(('SEC Filing', sec_alert))
    
    # Earnings calendar
    earnings_alerts = earnings_calendar_check(tickers)
    for alert in earnings_alerts:
        alerts.append(('Earnings', alert))
    
    # Volume spikes
    volume_alerts = volume_spike_detector(tickers)
    for alert in volume_alerts:
        alerts.append(('Volume Spike', alert))
    
    # Price momentum
    momentum_alerts = price_momentum_alert(tickers)
    for alert in momentum_alerts:
        alerts.append(('Momentum', alert))
    
    # Sentiment analysis
    sentiment_scores = market_sentiment_analysis(tickers)
    for ticker, score in sentiment_scores.items():
        if score['sentiment'] != 'neutral':
            alerts.append(('Sentiment', {'ticker': ticker, **score}))
    
    return alerts

if __name__ == "__main__":
    # Test the enhancements
    test_tickers = ['TSLA', 'NVDA', 'AAPL']
    alerts = run_enhanced_monitoring(test_tickers)
    
    for alert_type, alert_data in alerts:
        print(f"{alert_type}: {alert_data}") 