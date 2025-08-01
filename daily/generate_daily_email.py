import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys
import pathlib
import pandas as pd

# Add parent directory to path to import slack_utils
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from slack_utils import send_slack_message

# --- Email Configuration ---
SENDER_EMAIL = "boris.stefanik@me.com"
RECEIVER_EMAIL = "boris.stefanik@me.com"
SMTP_SERVER = "smtp.mail.me.com"
SMTP_PORT = 587
REPORT_URL = "https://bstefco.github.io/momentumsector/daily_screen.html"

# --- Get Password ---
password = os.environ.get("EMAIL_PASSWORD")
if not password:
    print("Error: EMAIL_PASSWORD environment variable not set.")
    exit(1)
password = password.strip()

# --- Check for EXIT signals and send Slack notifications ---
def check_exit_signals():
    """Check for EXIT signals and send Slack notifications."""
    csv_path = pathlib.Path(__file__).parent.parent / "docs" / "daily_screen.csv"
    
    if not csv_path.exists():
        print(f"Warning: CSV file not found at {csv_path}")
        return
    
    try:
        df = pd.read_csv(csv_path)
        exit_rows = df[df['Signal'] == 'EXIT']
        
        if exit_rows.empty:
            print("No EXIT signals found today.")
            return
        
        # Send Slack notification for each EXIT signal
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("Warning: No Slack webhook URL configured for EXIT notifications.")
            return
        
        for _, row in exit_rows.iterrows():
            # Determine SMA period based on ticker category
            sma_period = "50"  # Default
            if row['Ticker'] in ['URNM', 'NUKZ', 'XYL', 'ALFA.ST', 'LEU', 'SMR', 'TSLA']:
                sma_period = "100"  # Thematic
            elif row['Ticker'] in ['ATLX', 'BEAM', 'BMI', 'EOSE', 'FLNC', 'FLS', 'GWH', 'KD', 'ONON', 'SANA', 'VEEV', 'VRT', 'WIX']:
                sma_period = "30"   # High-Beta
            
            message = f":warning: *EXIT flag* – {row['Ticker']} closed {row['Close']:.2f} < SMA-{sma_period}. Follow sleeve rule."
            send_slack_message(message, webhook_url)
            print(f"EXIT notification sent for {row['Ticker']}")
            
    except Exception as e:
        print(f"Error processing EXIT signals: {e}")

# --- Build the Email ---
subject = f"Your Daily Screen is Ready - {datetime.utcnow().strftime('%Y-%m-%d')}"
body_html = f"""
<!DOCTYPE html>
<html>
<body>
    <p>Hi Boris,</p>
    <p>Your daily screen is ready.</p>
    <p><strong><a href=\"{REPORT_URL}\">View the daily screen online.</a></strong></p>
    <br>
    <p>— Your Momentum Bot 🚀</p>
</body>
</html>
"""

message = MIMEMultipart("alternative")
message["Subject"] = subject
message["From"] = SENDER_EMAIL
message["To"] = RECEIVER_EMAIL
message.attach(MIMEText(body_html, "html"))

# --- Send the Email ---
context = ssl.create_default_context()
email_sent = False
try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SENDER_EMAIL, password)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
    print("Daily notification email sent successfully!")
    email_sent = True
except Exception as e:
    print(f"Error sending daily email: {e}")

# --- Check for EXIT signals and send notifications ---
check_exit_signals()

# --- Send Slack Notification ---
def send_daily_notification(report_url: str) -> bool:
    """Send daily screen notification to Slack."""
    message = f"""📊 *Daily Screen Ready*
Your daily momentum screen is ready for review.

<{report_url}|View the daily screen online> 📈

— Your Momentum Bot 🚀"""
    
    # Use dedicated webhook for reports, fallback to main webhook
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL_REPORTS") or os.environ.get("SLACK_WEBHOOK_URL")
    if os.environ.get("SLACK_WEBHOOK_URL_REPORTS"):
        print("Using dedicated reports webhook for daily notification")
    else:
        print("Using main webhook for daily notification (reports webhook not configured)")
    return send_slack_message(message, webhook_url)

slack_sent = send_daily_notification(REPORT_URL)
if slack_sent:
    print("Daily notification Slack message sent successfully!")
else:
    print("Slack notification failed or not configured")

# Exit with error only if both email and Slack failed
if not email_sent and not slack_sent:
    print("Both email and Slack notifications failed!")
    exit(1) 