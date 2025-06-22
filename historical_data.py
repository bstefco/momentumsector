#!/usr/bin/env python3
"""
Historical data management for momentum tracking.
Stores and compares month-over-month changes for top 5 tickers.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

HISTORICAL_FILE = "historical_momentum.json"

def load_historical_data() -> Dict:
    """Load historical momentum data from file."""
    if os.path.exists(HISTORICAL_FILE):
        try:
            with open(HISTORICAL_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {"months": {}}

def save_historical_data(data: Dict) -> None:
    """Save historical momentum data to file."""
    with open(HISTORICAL_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_current_top5(momentum_data: List[Dict]) -> List[Dict]:
    """Extract top 5 tickers from current momentum data."""
    # Sort by momentum score (descending) and take top 5
    sorted_data = sorted(momentum_data, key=lambda x: x.get('MomentumScore', 0), reverse=True)
    top5 = []
    
    for i, entry in enumerate(sorted_data[:5]):
        top5.append({
            'ticker': entry.get('Ticker', ''),
            'momentum': entry.get('MomentumScore', 0),
            'rank': i + 1,
            'return12m': entry.get('Return12m', 0)
        })
    
    return top5

def compare_with_previous_month(current_top5: List[Dict], historical_data: Dict) -> Dict:
    """Compare current top 5 with previous month's data."""
    current_month = datetime.now().strftime('%Y-%m')
    
    # Get previous month's data
    previous_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m')
    previous_top5 = historical_data.get('months', {}).get(previous_month, [])
    
    if not previous_top5:
        return {
            'current_month': current_month,
            'previous_month': previous_month,
            'changes': [],
            'new_entries': current_top5,
            'exits': [],
            'rank_changes': [],
            'message': 'No previous month data available for comparison'
        }
    
    # Create lookup dictionaries
    current_lookup = {entry['ticker']: entry for entry in current_top5}
    previous_lookup = {entry['ticker']: entry for entry in previous_top5}
    
    # Find new entries and exits
    current_tickers = set(current_lookup.keys())
    previous_tickers = set(previous_lookup.keys())
    
    new_entries = [current_lookup[ticker] for ticker in current_tickers - previous_tickers]
    exits = [previous_lookup[ticker] for ticker in previous_tickers - current_tickers]
    
    # Find rank changes for tickers in both months
    rank_changes = []
    common_tickers = current_tickers & previous_tickers
    
    for ticker in common_tickers:
        current_rank = current_lookup[ticker]['rank']
        previous_rank = previous_lookup[ticker]['rank']
        rank_change = previous_rank - current_rank  # Positive = improved rank
        
        if rank_change != 0:
            rank_changes.append({
                'ticker': ticker,
                'current_rank': current_rank,
                'previous_rank': previous_rank,
                'rank_change': rank_change,
                'current_momentum': current_lookup[ticker]['momentum'],
                'previous_momentum': previous_lookup[ticker]['momentum'],
                'momentum_change': current_lookup[ticker]['momentum'] - previous_lookup[ticker]['momentum']
            })
    
    # Create summary changes list
    changes = []
    
    # Add new entries
    for entry in new_entries:
        changes.append({
            'type': 'new_entry',
            'ticker': entry['ticker'],
            'rank': entry['rank'],
            'momentum': entry['momentum']
        })
    
    # Add exits
    for entry in exits:
        changes.append({
            'type': 'exit',
            'ticker': entry['ticker'],
            'previous_rank': entry['rank'],
            'previous_momentum': entry['momentum']
        })
    
    # Add rank changes
    for change in rank_changes:
        changes.append({
            'type': 'rank_change',
            'ticker': change['ticker'],
            'current_rank': change['current_rank'],
            'previous_rank': change['previous_rank'],
            'rank_change': change['rank_change'],
            'momentum_change': change['momentum_change']
        })
    
    return {
        'current_month': current_month,
        'previous_month': previous_month,
        'changes': changes,
        'new_entries': new_entries,
        'exits': exits,
        'rank_changes': rank_changes,
        'message': f'Compared with {previous_month} data'
    }

def update_historical_data(momentum_data: List[Dict]) -> Dict:
    """Update historical data with current month's top 5."""
    historical_data = load_historical_data()
    current_month = datetime.now().strftime('%Y-%m')
    
    # Get current top 5
    current_top5 = get_current_top5(momentum_data)
    
    # Store current month's data
    historical_data['months'][current_month] = current_top5
    
    # Compare with previous month
    comparison = compare_with_previous_month(current_top5, historical_data)
    
    # Save updated historical data
    save_historical_data(historical_data)
    
    return comparison

def format_changes_for_dashboard(comparison: Dict) -> Dict:
    """Format comparison data for the dashboard display."""
    formatted_changes = []
    
    for change in comparison['changes']:
        if change['type'] == 'new_entry':
            formatted_changes.append({
                'type': 'new',
                'ticker': change['ticker'],
                'rank': change['rank'],
                'momentum': f"{change['momentum']:.1f}%",
                'description': f"🆕 New entry at rank #{change['rank']}"
            })
        elif change['type'] == 'exit':
            formatted_changes.append({
                'type': 'exit',
                'ticker': change['ticker'],
                'previous_rank': change['previous_rank'],
                'previous_momentum': f"{change['previous_momentum']:.1f}%",
                'description': f"❌ Exited from rank #{change['previous_rank']}"
            })
        elif change['type'] == 'rank_change':
            direction = "↗️" if change['rank_change'] > 0 else "↘️"
            formatted_changes.append({
                'type': 'change',
                'ticker': change['ticker'],
                'current_rank': change['current_rank'],
                'previous_rank': change['previous_rank'],
                'rank_change': change['rank_change'],
                'momentum_change': f"{change['momentum_change']:+.1f}%",
                'description': f"{direction} Rank {change['previous_rank']} → {change['current_rank']} ({change['momentum_change']:+.1f}%)"
            })
    
    return {
        'current_month': comparison['current_month'],
        'previous_month': comparison['previous_month'],
        'changes': formatted_changes,
        'summary': {
            'new_entries': len(comparison['new_entries']),
            'exits': len(comparison['exits']),
            'rank_changes': len(comparison['rank_changes'])
        }
    }

if __name__ == "__main__":
    # Test the historical data functionality
    print("Historical data management system ready!")
    print("Use update_historical_data() to track month-over-month changes.") 