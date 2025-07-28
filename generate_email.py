import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from slack_utils import send_monthly_notification

# --- Email Configuration ---
SENDER_EMAIL = "boris.stefanik@me.com"
RECEIVER_EMAIL = "boris.stefanik@me.com"
SMTP_SERVER = "smtp.mail.me.com"
SMTP_PORT = 587
REPORT_URL = "https://bstefco.github.io/momentumsector/"

# --- Get Password ---
password = os.environ.get("EMAIL_PASSWORD")
if not password:
    print("Error: EMAIL_PASSWORD environment variable not set.")
    exit(1)
password = password.strip()

# --- Build the Email ---
subject = f"Your Momentum Report is Ready - {datetime.utcnow().strftime('%B %Y')}"
body_html = f"""
<!DOCTYPE html>
<html>
<body>
    <p>Hi Boris,</p>
    <p>Your monthly sector-momentum report is ready.</p>
    <p><strong><a href="{REPORT_URL}">View the full, interactive report online.</a></strong></p>
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
    print("Notification email sent successfully!")
    email_sent = True
except Exception as e:
    print(f"Error sending email: {e}")

# --- Send Slack Notification ---
slack_sent = send_monthly_notification(REPORT_URL)
if slack_sent:
    print("Monthly notification Slack message sent successfully!")
else:
    print("Slack notification failed or not configured")

# Exit with error only if both email and Slack failed
if not email_sent and not slack_sent:
    print("Both email and Slack notifications failed!")
    exit(1) 