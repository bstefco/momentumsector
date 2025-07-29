#!/usr/bin/env python3
"""
Test script to verify Slack notifications are working properly.
Run this script to test both daily and monthly notification functions.
"""

import os
import sys
from slack_utils import send_daily_notification, send_monthly_notification

def test_slack_notifications():
    """Test both daily and monthly Slack notifications."""
    print("🧪 Testing Slack Notifications")
    print("=" * 40)
    
    # Check environment variables
    print("Environment Variables:")
    print(f"  SLACK_WEBHOOK_URL: {'✅ Set' if os.environ.get('SLACK_WEBHOOK_URL') else '❌ Not set'}")
    print(f"  SLACK_WEBHOOK_URL_REPORTS: {'✅ Set' if os.environ.get('SLACK_WEBHOOK_URL_REPORTS') else '❌ Not set'}")
    print()
    
    # Test daily notification
    print("📊 Testing Daily Notification...")
    daily_url = "https://bstefco.github.io/momentumsector/daily_screen.html"
    daily_success = send_daily_notification(daily_url)
    print(f"Daily notification: {'✅ SUCCESS' if daily_success else '❌ FAILED'}")
    print()
    
    # Test monthly notification
    print("📈 Testing Monthly Notification...")
    monthly_url = "https://bstefco.github.io/momentumsector/"
    monthly_success = send_monthly_notification(monthly_url)
    print(f"Monthly notification: {'✅ SUCCESS' if monthly_success else '❌ FAILED'}")
    print()
    
    # Summary
    print("=" * 40)
    print("SUMMARY:")
    if daily_success and monthly_success:
        print("🎉 All Slack notifications working correctly!")
        return True
    elif daily_success or monthly_success:
        print("⚠️  Partial success - some notifications working")
        return False
    else:
        print("❌ All Slack notifications failed")
        print("\nTroubleshooting tips:")
        print("1. Check that SLACK_WEBHOOK_URL is set in your environment")
        print("2. Verify the webhook URL is valid and active")
        print("3. Check your internet connection")
        print("4. Ensure the requests library is installed: pip install requests")
        return False

if __name__ == "__main__":
    success = test_slack_notifications()
    sys.exit(0 if success else 1) 