# GitHub Actions Setup for Market Radar Bot

## Required Secrets

Add these secrets in your GitHub repository:
**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets:
- `SLACK_WEBHOOK`: Your Slack webhook URL
- `IEX_TOKEN`: Your IEX Cloud API token

### Optional Secrets (with defaults):
- `SI_TICKERS`: Comma-separated tickers (default: empty)
- `NEWS_TICKERS_EXTRA`: Comma-separated tickers (default: empty)
- `MENTION_MIN`: Minimum mentions (default: 25)
- `ACCEL_FACTOR`: Acceleration factor (default: 3)
- `SUBREDDITS`: Comma-separated subreddits (default: wallstreetbets)

## Schedule

The workflow runs:
- **Every hour** during US trading hours (14-20 UTC = 9AM-3PM EST)
- **Monday-Friday only**
- **Manual runs** available via "workflow_dispatch"

## Example Secret Values:

```
SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
IEX_TOKEN=pk_your_iex_cloud_token
SI_TICKERS=SANA,TMC,EOSE,GWH,ATLX,NBIS,VRT,BEAM,FLNC,BYDDY
NEWS_TICKERS_EXTRA=TSLA,NVDA
MENTION_MIN=25
ACCEL_FACTOR=3
SUBREDDITS=wallstreetbets,stocks,options
```

## Monitoring

- Check workflow runs in **Actions** tab
- Database artifacts uploaded for debugging
- Slack notifications for all alerts 