#!/usr/bin/env python3
"""
Test file for the serverless handler with Ape Wisdom integration.
"""

import json
import pytest
from unittest.mock import patch, Mock
from handler import apewisdom_mentions, get_stock_data, create_slack_block_kit, lambda_handler

def test_apewisdom_mentions_success():
    """Test successful Ape Wisdom API call"""
    mock_response = Mock()
    mock_response.json.return_value = [
        {'ticker': 'TSLA', 'mentions': 150, 'mentions_24h_ago': 100},
        {'ticker': 'AAPL', 'mentions': 75, 'mentions_24h_ago': 80},
        {'ticker': 'GME', 'mentions': 200, 'mentions_24h_ago': 180}
    ]
    mock_response.raise_for_status.return_value = None
    
    with patch('requests.get', return_value=mock_response):
        mentions, delta = apewisdom_mentions('TSLA')
        assert mentions == 150
        assert delta == 50

def test_apewisdom_mentions_not_found():
    """Test when ticker is not in top-100"""
    mock_response = Mock()
    mock_response.json.return_value = [
        {'ticker': 'TSLA', 'mentions': 150, 'mentions_24h_ago': 100},
        {'ticker': 'AAPL', 'mentions': 75, 'mentions_24h_ago': 80}
    ]
    mock_response.raise_for_status.return_value = None
    
    with patch('requests.get', return_value=mock_response):
        mentions, delta = apewisdom_mentions('UNKNOWN')
        assert mentions == 0
        assert delta == 0

def test_apewisdom_mentions_api_error():
    """Test API error handling"""
    with patch('requests.get', side_effect=Exception("API Error")):
        mentions, delta = apewisdom_mentions('TSLA')
        assert mentions == 0
        assert delta == 0

@patch('handler.apewisdom_mentions')
@patch('yfinance.Ticker')
def test_get_stock_data_success(mock_ticker, mock_apewisdom):
    """Test successful stock data retrieval"""
    # Mock yfinance data
    mock_stock = Mock()
    mock_stock.info = {
        'volume': 1000000,
        'marketCap': 50000000000,
        'sharesShort': 5000000,
        'floatShares': 100000000,
        'longName': 'Tesla, Inc.',
        'sector': 'Consumer Cyclical',
        'industry': 'Auto Manufacturers'
    }
    mock_stock.history.return_value = Mock()
    mock_stock.history.return_value.iloc = [
        Mock(return_value={'Close': 250.0}),
        Mock(return_value={'Close': 240.0})
    ]
    mock_stock.history.return_value.__len__ = lambda: 2
    mock_ticker.return_value = mock_stock
    
    # Mock Ape Wisdom data
    mock_apewisdom.return_value = (150, 50)
    
    result = get_stock_data('TSLA')
    
    assert result['symbol'] == 'TSLA'
    assert result['current_price'] == 250.0
    assert result['price_change_pct'] == 4.17  # (250-240)/240 * 100
    assert result['short_interest_pct'] == 5.0  # (5M/100M) * 100
    assert result['reddit_mentions_24h'] == 150
    assert result['reddit_mentions_change'] == 50

@patch('handler.apewisdom_mentions')
@patch('yfinance.Ticker')
def test_get_stock_data_urnm_lse(mock_ticker, mock_apewisdom):
    """Test URNM.L LSE stock with GBX to EUR conversion"""
    # Mock yfinance data for URNM.L
    mock_stock = Mock()
    mock_stock.info = {
        'volume': 500000,
        'marketCap': 1000000000,
        'currency': 'GBX',
        'longName': 'Sprott Uranium Miners ETF',
        'sector': 'Energy',
        'industry': 'ETF'
    }
    mock_stock.history.return_value = Mock()
    mock_stock.history.return_value.iloc = [
        Mock(return_value={'Close': 4810}),
        Mock(return_value={'Close': 4800})
    ]
    mock_stock.history.return_value.__len__ = lambda: 2
    
    # Mock exchange rate
    mock_exchange = Mock()
    mock_exchange.info = {"regularMarketPrice": 1.18}
    
    mock_ticker.side_effect = [mock_stock, mock_exchange]
    
    # Mock Ape Wisdom data
    mock_apewisdom.return_value = (25, 5)
    
    result = get_stock_data('URNM')
    
    assert result['symbol'] == 'URNM'
    assert result['yahoo_symbol'] == 'URNM.L'
    assert result['current_price'] == 4810
    assert result['price_display'] == "€56.76 (GBX 4810)"
    assert result['exchange'] == 'LSE'
    assert result['currency'] == 'GBX'

@patch('handler.apewisdom_mentions')
@patch('yfinance.Ticker')
def test_get_stock_data_race_borsa(mock_ticker, mock_apewisdom):
    """Test RACE.MI Borsa Italiana stock"""
    # Mock yfinance data for RACE.MI
    mock_stock = Mock()
    mock_stock.info = {
        'volume': 300000,
        'marketCap': 50000000000,
        'currency': 'EUR',
        'longName': 'Ferrari N.V.',
        'sector': 'Consumer Cyclical',
        'industry': 'Auto Manufacturers'
    }
    mock_stock.history.return_value = Mock()
    mock_stock.history.return_value.iloc = [
        Mock(return_value={'Close': 443.39}),
        Mock(return_value={'Close': 440.00})
    ]
    mock_stock.history.return_value.__len__ = lambda: 2
    mock_ticker.return_value = mock_stock
    
    # Mock Ape Wisdom data
    mock_apewisdom.return_value = (15, -2)
    
    result = get_stock_data('RACE')
    
    assert result['symbol'] == 'RACE'
    assert result['yahoo_symbol'] == 'RACE.MI'
    assert result['current_price'] == 443.39
    assert result['price_display'] == "€443.39"
    assert result['exchange'] == 'Borsa Italiana'
    assert result['currency'] == 'EUR'

def test_create_slack_block_kit_success():
    """Test Slack Block Kit creation"""
    data = {
        'symbol': 'TSLA',
        'current_price': 250.0,
        'price_display': '$250.00',
        'price_change_pct': 4.17,
        'volume': 1000000,
        'market_cap': 50000000000,
        'short_interest_pct': 5.0,
        'reddit_mentions_24h': 150,
        'reddit_mentions_change': 50,
        'company_name': 'Tesla, Inc.',
        'sector': 'Consumer Cyclical',
        'industry': 'Auto Manufacturers',
        'exchange': 'NASDAQ'
    }
    
    result = create_slack_block_kit(data)
    
    assert 'blocks' in result
    assert len(result['blocks']) == 4  # header, section, section, context
    assert result['blocks'][0]['type'] == 'header'
    assert 'TSLA Analysis' in result['blocks'][0]['text']['text']
    assert 'Exchange: NASDAQ' in result['blocks'][3]['elements'][0]['text']

def test_create_slack_block_kit_error():
    """Test Slack Block Kit creation with error"""
    data = {
        'symbol': 'TSLA',
        'error': 'API Error'
    }
    
    result = create_slack_block_kit(data)
    
    assert 'blocks' in result
    assert len(result['blocks']) == 1
    assert 'Error analyzing TSLA' in result['blocks'][0]['text']['text']

@patch('handler.get_stock_data')
@patch('handler.create_slack_block_kit')
def test_lambda_handler_success(mock_create_slack, mock_get_stock):
    """Test successful Lambda handler execution"""
    # Mock stock data
    mock_get_stock.return_value = {
        'symbol': 'TSLA',
        'current_price': 250.0,
        'price_change_pct': 4.17
    }
    
    # Mock Slack response
    mock_create_slack.return_value = {'blocks': []}
    
    event = {
        'body': json.dumps({'ticker': 'TSLA'})
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 200
    assert 'Content-Type' in result['headers']
    assert 'application/json' in result['headers']['Content-Type']

def test_lambda_handler_missing_ticker():
    """Test Lambda handler with missing ticker"""
    event = {
        'body': json.dumps({})
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 400
    assert 'Missing or invalid ticker symbol' in result['body']

def test_lambda_handler_empty_ticker():
    """Test Lambda handler with empty ticker"""
    event = {
        'body': json.dumps({'ticker': ''})
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 400
    assert 'Missing or invalid ticker symbol' in result['body']

@patch('handler.get_stock_data')
def test_lambda_handler_error(mock_get_stock):
    """Test Lambda handler error handling"""
    mock_get_stock.side_effect = Exception("Test error")
    
    event = {
        'body': json.dumps({'ticker': 'TSLA'})
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 500
    assert 'Internal server error' in result['body']

if __name__ == "__main__":
    # Run basic tests
    print("Testing Ape Wisdom integration...")
    
    # Test with a real API call (if available)
    try:
        mentions, delta = apewisdom_mentions('TSLA')
        print(f"TSLA mentions: {mentions}, delta: {delta}")
    except Exception as e:
        print(f"API test failed: {e}")
    
    print("All tests completed!") 