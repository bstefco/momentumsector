import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def send_slack_message(message: str, webhook_url: Optional[str] = None) -> bool:
    """
    Send a message to Slack using webhook URL.
    
    Args:
        message (str): The message to send
        webhook_url (str, optional): Slack webhook URL. If None, uses SLACK_WEBHOOK_URL env var.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if webhook_url is None:
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("No Slack webhook URL provided. Skipping Slack notification.")
        return False
    
    payload = {"text": message}
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Slack message sent successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to send Slack message: {e}")
        return False

def send_daily_notification(report_url: str) -> bool:
    """
    Send daily screen notification to Slack.
    
    Args:
        report_url (str): URL to the daily report
    
    Returns:
        bool: True if successful, False otherwise
    """
    message = f"""📊 *Daily Screen Ready*
Your daily momentum screen is ready for review.

<{report_url}|View the daily screen online> 📈

— Your Momentum Bot 🚀"""
    
    # Use dedicated webhook for reports, fallback to main webhook
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL_REPORTS") or os.environ.get("SLACK_WEBHOOK_URL")
    return send_slack_message(message, webhook_url)

def send_monthly_notification(report_url: str) -> bool:
    """
    Send monthly report notification to Slack.
    
    Args:
        report_url (str): URL to the monthly report
    
    Returns:
        bool: True if successful, False otherwise
    """
    message = f"""📈 *Monthly Momentum Report Ready*
Your comprehensive sector-momentum analysis is ready.

<{report_url}|View the full interactive report> 📊

— Your Momentum Bot 🚀"""
    
    # Use dedicated webhook for reports, fallback to main webhook
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL_REPORTS") or os.environ.get("SLACK_WEBHOOK_URL")
    return send_slack_message(message, webhook_url) 