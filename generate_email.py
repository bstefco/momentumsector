import os
import pandas as pd
from datetime import datetime, timedelta
from markdown import markdown

# This dictionary should be kept in sync with sector_momentum_screen.py
UNIVERSE = {
    "XLK": "US Technology", "XLE": "US Energy", "XLF": "US Financials",
    "XLV": "US Health Care", "XLI": "US Industrials", "XLP": "US Cons. Staples",
    "XLY": "US Cons. Discretionary", "XLU": "US Utilities", "XLB": "US Materials",
    "XLRE": "US Real Estate", "XLC": "US Communication", "IXN": "Global Technology",
    "IXG": "Global Financials", "IXJ": "Global Healthcare", "IXI": "Global Industrials",
    "IXP": "Global Telecom", "IXC": "Global Energy", "IXM": "Global Materials",
    "KWEB": "China Internet", "FXI": "China Large Cap", "EWJ": "Japan", "AGG": "US Aggregate Bond"
}

# Load the momentum scores
df: pd.DataFrame = pd.read_csv('momentum_scores.csv')
df = df.dropna(subset=['MomentumScore', 'Return12m'])
df[['MomentumScore', 'Return12m']] = df[['MomentumScore', 'Return12m']].apply(pd.to_numeric, errors='coerce')

# Get bond data
bond_ticker = 'AGG'
bond_return_series: pd.Series = df[df['Ticker'] == bond_ticker]['Return12m']
bond_return = bond_return_series.iloc[0] * 100 if not bond_return_series.empty else 0

# Get top 3 winners (excluding bond)
winners: pd.DataFrame = df[df['Ticker'] != bond_ticker].nlargest(n=3, columns='MomentumScore')

# Read the template
with open('email_template.txt', 'r') as f:
    template = f.read()

# Calculate next rebalance date
today = datetime.now()
next_rebalance_date = (today.replace(day=1) + timedelta(days=32)).replace(day=14)

# Prepare replacements
replacements = {
    '{{ run_date }}': today.strftime('%Y-%m-%d'),
    '{{ run_time }}': today.strftime('%H:%M'),
    '{{ winner1_ticker }}': winners.iloc[0]['Ticker'] if len(winners) > 0 else 'N/A',
    '{{ winner1_label }}': UNIVERSE.get(winners.iloc[0]['Ticker'], 'N/A') if len(winners) > 0 else 'N/A',
    '{{ winner1_score }}': f"{winners.iloc[0]['MomentumScore']*100:.1f}" if len(winners) > 0 else 'N/A',
    '{{ winner2_ticker }}': winners.iloc[1]['Ticker'] if len(winners) > 1 else 'N/A',
    '{{ winner2_label }}': UNIVERSE.get(winners.iloc[1]['Ticker'], 'N/A') if len(winners) > 1 else 'N/A',
    '{{ winner2_score }}': f"{winners.iloc[1]['MomentumScore']*100:.1f}" if len(winners) > 1 else 'N/A',
    '{{ winner3_ticker }}': winners.iloc[2]['Ticker'] if len(winners) > 2 else 'N/A',
    '{{ winner3_label }}': UNIVERSE.get(winners.iloc[2]['Ticker'], 'N/A') if len(winners) > 2 else 'N/A',
    '{{ winner3_score }}': f"{winners.iloc[2]['MomentumScore']*100:.1f}" if len(winners) > 2 else 'N/A',
    '{{ bond_ticker }}': bond_ticker,
    '{{ bond_return }}': f'{bond_return:.2f}',
    '{{ next_rebalance_date }}': next_rebalance_date.strftime('%Y-%m-%d'),
    # --- These are placeholders; you might want to calculate them dynamically ---
    '{{ target_eur }}': '10,000',
    '{{ total_book }}': '30,000',
    '{{ calc_shares(price, target_eur) }}': '...' 
}

# Apply replacements
email_content = template
for placeholder, value in replacements.items():
    email_content = email_content.replace(placeholder, str(value))

# Extract subject and body
lines = email_content.split('\n')
subject = lines[0].replace('Subject: ', '').strip()
body_markdown = '\n'.join(lines[2:])

# Convert markdown body to HTML
body_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
    th {{ background-color: #f2f2f2; }}
    h2 {{ border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
</style>
</head>
<body>
    {markdown(body_markdown, extensions=['tables'])}
</body>
</html>
"""

# Save to files for the workflow
with open('email_subject.txt', 'w') as f:
    f.write(subject)
with open('email_body.html', 'w') as f:
    f.write(body_html)

print("Email content generated from template and saved to files.") 