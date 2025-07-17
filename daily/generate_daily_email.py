import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

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
try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SENDER_EMAIL, password)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
    print("Daily notification email sent successfully!")
except Exception as e:
    print(f"Error sending daily email: {e}")
    exit(1) 