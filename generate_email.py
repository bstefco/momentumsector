import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime

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
    <p>The <code>momentum_scores.csv</code> file is attached for your records.</p>
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

# --- Attach CSV ---
try:
    with open("momentum_scores.csv", "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="csv")
    attachment.add_header('Content-Disposition', 'attachment', filename='momentum_scores.csv')
    message.attach(attachment)
    print("Attached momentum_scores.csv to the email.")
except FileNotFoundError:
    print("Warning: momentum_scores.csv not found, not sending as attachment.")

# --- Send the Email ---
context = ssl.create_default_context()
try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SENDER_EMAIL, password)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
    print("Notification email sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")
    exit(1) 