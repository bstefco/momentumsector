import os
import pandas as pd
from datetime import datetime
from markdown import markdown

# Load the momentum scores
df: pd.DataFrame
try:
    df = pd.read_csv('momentum_scores.csv')
    df = df.dropna(subset=['MomentumScore'])
    df['MomentumScore'] = pd.to_numeric(df['MomentumScore'], errors='coerce')
    df = df.dropna(subset=['MomentumScore'])
except (FileNotFoundError, KeyError) as e:
    print(f"Error reading or processing momentum_scores.csv: {e}")
    # Create an empty DataFrame with expected columns if file is missing or broken
    df = pd.DataFrame({'Ticker': pd.Series(dtype='str'), 'MomentumScore': pd.Series(dtype='float')})

# Get top 3 winners
winners: pd.DataFrame
if not df.empty:
    winners = df.nlargest(n=3, columns='MomentumScore')
else:
    winners = pd.DataFrame({'Ticker': pd.Series(dtype='str'), 'MomentumScore': pd.Series(dtype='float')})

# Get current time for the report
report_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

# Set subject
subject = f"Your Momentum Sector Report for {datetime.utcnow().strftime('%B %Y')}"

# Load email template from file
try:
    with open('email_template.txt', 'r') as f:
        body_markdown = f.read()
except FileNotFoundError:
    body_markdown = "Email template not found."

# Replace time placeholder
body_markdown = body_markdown.replace('{{ report_time }}', report_time)

# Generate winner table markdown
table_markdown = "| Rank | Ticker | Momentum Score |\n|------|--------|----------------|\n"
if not winners.empty:
    for i in range(len(winners)):
        rank = i + 1
        row = winners.iloc[i]
        ticker = row['Ticker']
        score = f"{row['MomentumScore']:.1%}"
        table_markdown += f"| {rank} | **{ticker}** | {score} |\n"
else:
    # Add placeholder rows if there are no winners
    for i in range(3):
        table_markdown += f"| {i+1} | N/A | N/A |\n"

body_markdown = body_markdown.replace('{{ winner_table }}', table_markdown)

# Convert body to HTML with professional styling
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

# Save subject and body to files
with open('email_subject.txt', 'w') as f:
    f.write(subject)
with open('email_body.html', 'w') as f:
    f.write(body_html)

print("HTML email content and subject generated successfully.") 