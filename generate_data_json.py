import pandas as pd
import json
from datetime import datetime, timedelta
from historical_data import update_historical_data, format_changes_for_dashboard

# This dictionary provides the country and segment for each ticker.
UNIVERSE_DETAILS = {
    # US Sectors
    "XLK": {"country": "US", "segment": "Technology"},
    "XLE": {"country": "US", "segment": "Energy"},
    "XLF": {"country": "US", "segment": "Financials"},
    "XLV": {"country": "US", "segment": "Health Care"},
    "XLI": {"country": "US", "segment": "Industrials"},
    "XLP": {"country": "US", "segment": "Cons. Staples"},
    "XLY": {"country": "US", "segment": "Cons. Discretionary"},
    "XLU": {"country": "US", "segment": "Utilities"},
    "XLB": {"country": "US", "segment": "Materials"},
    "XLRE": {"country": "US", "segment": "Real Estate"},
    "XLC": {"country": "US", "segment": "Communication"},
    # EU Sectors
    "EXV3.DE": {"country": "EU", "segment": "Technology"},
    "EXV1.DE": {"country": "EU", "segment": "Banks"},
    "EXV4.DE": {"country": "EU", "segment": "Health Care"},
    "EXV7.DE": {"country": "EU", "segment": "Industrials"},
    "EXV6.DE": {"country": "EU", "segment": "Consumer Staples"},
    "CDIS.L":  {"country": "EU", "segment": "Consumer Discretionary"},
    "EXV5.DE": {"country": "EU", "segment": "Utilities"},
    "EXV8.DE": {"country": "EU", "segment": "Materials"},
    "EXV2.DE": {"country": "EU", "segment": "Communication Services"},  # správny label pre EXV2
    "EXV0.DE": {"country": "EU", "segment": "Oil & Gas"},               # správny label pre EXV0
    "EXV9.DE": {"country": "EU", "segment": "Real Estate"},
    # Country Specific
    "KWEB": {"country": "CN", "segment": "Internet"},
    "FXI": {"country": "CN", "segment": "Large Cap"},
    "EWJ": {"country": "JP", "segment": "Broad Market"},
    "XCTE.L": {"country": "CN", "segment": "Technology"},
    "JPJP.L": {"country": "JP", "segment": "Broad Market"},
    # Bonds
    "AGG": {"country": "US", "segment": "Aggregate Bond"},
    "SUAG.L": {"country": "EU", "segment": "Bonds"},
    # Default
    "DEFAULT": {"country": "N/A", "segment": "N/A"}
}

def get_details(ticker):
    return UNIVERSE_DETAILS.get(ticker, UNIVERSE_DETAILS["DEFAULT"])

# Load and process data
try:
    df = pd.read_csv('momentum_scores.csv')
    df.dropna(subset=['MomentumScore', 'Return12m'], inplace=True)
    df['MomentumScore'] = pd.to_numeric(df['MomentumScore'], errors='coerce') * 100
    df['Return12m'] = pd.to_numeric(df['Return12m'], errors='coerce') * 100
    df.sort_values(by='MomentumScore', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
except FileNotFoundError:
    print("Error: momentum_scores.csv not found.")
    exit(1)

# Configuration
bond_ticker = 'SUAG.L'
target_eur = "1,650" 

# Get bond data
bond_data = df[df['Ticker'] == bond_ticker]
bond_return = bond_data['Return12m'].iloc[0] if not bond_data.empty else 0.0

# Get winners (top 3 non-bond)
winners_df = df[df['Ticker'] != bond_ticker].head(3).reset_index(drop=True)
winners_list = []
for i, row in winners_df.iterrows():
    details = get_details(row['Ticker'])
    winners_list.append({
        "rank": i + 1,
        "ticker": row['Ticker'],
        "country": details['country'],
        "segment": details['segment'],
        "momentum": f"{row['MomentumScore']:.1f}"
    })

# Get all ETFs list (excluding bonds)
all_etfs_df = df[df['Ticker'] != bond_ticker].reset_index(drop=True)
all_etfs_list = []
for i, row in all_etfs_df.iterrows():
    details = get_details(row['Ticker'])
    all_etfs_list.append({
        "rank": i + 1,
        "ticker": row['Ticker'],
        "country": details['country'],
        "segment": details['segment'],
        "ret12": f"{row['Return12m']:.1f}",
        "momentum": f"{row['MomentumScore']:.1f}"
    })

# Get historical comparison data for top 5
try:
    # Convert DataFrame to list of dictionaries for historical analysis
    momentum_data = df.to_dict('records')
    historical_comparison = update_historical_data(momentum_data)
    formatted_changes = format_changes_for_dashboard(historical_comparison)
except Exception as e:
    print(f"Warning: Could not generate historical comparison: {e}")
    formatted_changes = {
        'current_month': datetime.now().strftime('%Y-%m'),
        'previous_month': (datetime.now() - timedelta(days=30)).strftime('%Y-%m'),
        'changes': [],
        'summary': {'new_entries': 0, 'exits': 0, 'rank_changes': 0}
    }

# Dates
today = datetime.now()
next_rebalance_date = (today.replace(day=1) + timedelta(days=32)).replace(day=14)

# Final JSON structure
output_data = {
    "run_date": today.strftime('%Y-%m-%d'),
    "bond_ticker": bond_ticker,
    "bond_return": f"{bond_return:.2f}",
    "target_eur": target_eur,
    "next_rebalance_date": next_rebalance_date.strftime('%Y-%m-%d'),
    "winners": winners_list,
    "allEtfs": all_etfs_list,
    "historical_changes": formatted_changes
}

# Write to file
with open('data.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print("data.json generated successfully.") 