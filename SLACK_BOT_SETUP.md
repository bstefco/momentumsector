# Slack Bot Setup and Troubleshooting

## Overview

The Slack bot integration sends notifications for both daily and monthly reports to your Slack workspace. It uses webhook URLs to post messages automatically.

## Setup

### 1. GitHub Secrets Configuration

You need to configure the following secrets in your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `SLACK_WEBHOOK_URL`: Your main Slack webhook URL
   - `SLACK_WEBHOOK_URL_REPORTS`: (Optional) Dedicated webhook for reports
   - `Email`: Your email password (already configured)

### 2. Creating Slack Webhooks

1. Go to your Slack workspace
2. Navigate to Apps → Manage apps → Custom Integrations → Incoming Webhooks
3. Click "Add Configuration"
4. Choose a channel for notifications
5. Copy the webhook URL
6. Add it to GitHub secrets

## Testing

### Local Testing

Run the test script to verify your setup:

```bash
# Set environment variables
export SLACK_WEBHOOK_URL="your_webhook_url_here"
export SLACK_WEBHOOK_URL_REPORTS="your_reports_webhook_url_here"  # optional

# Run test
python3 test_slack_notifications.py
```

### Manual Workflow Testing

You can manually trigger the workflows to test them:

1. Go to your repository → Actions
2. Select "Daily Screen" or "monthly run"
3. Click "Run workflow"
4. Check the logs for Slack notification status

## Troubleshooting

### Common Issues

1. **"No Slack webhook URL provided"**
   - Check that `SLACK_WEBHOOK_URL` is set in GitHub secrets
   - Verify the secret name matches exactly (case-sensitive)

2. **"Failed to send Slack message"**
   - Verify the webhook URL is valid and active
   - Check that the webhook hasn't been revoked
   - Ensure the channel still exists

3. **Email works but Slack doesn't**
   - Check GitHub Actions logs for detailed error messages
   - Verify the `requests` library is installed (added to workflows)
   - Test with the test script locally

### Debugging

The enhanced logging will show:
- Which webhook URL is being used
- Whether the webhook URL is configured
- Success/failure status of each notification attempt

### Workflow Logs

Check the GitHub Actions logs for these messages:
- ✅ "Slack message sent successfully!"
- ❌ "Failed to send Slack message: [error details]"
- ⚠️ "No Slack webhook URL provided"

## Files Modified

The following files were updated to fix the Slack notification issue:

1. `.github/workflows/daily.yml` - Added Slack environment variables
2. `.github/workflows/monthly.yml` - Added Slack environment variables and requests dependency
3. `slack_utils.py` - Enhanced logging and error handling
4. `test_slack_notifications.py` - New test script for verification

## Next Steps

1. Add the required GitHub secrets
2. Test the setup with the test script
3. Manually trigger a workflow to verify it works
4. Monitor the next automated run

The Slack notifications should now work for both daily and monthly automated runs! 