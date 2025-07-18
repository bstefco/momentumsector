# Sector-Momentum ETF Screener

[**View the Daily Screen Report**](https://bstefco.github.io/momentumsector/daily_screen.html)

A momentum-based ETF screening tool that identifies the best-performing sector ETFs for portfolio rebalancing.

## Features

- Screens 25 global sector ETFs using momentum analysis
- Calculates average momentum across 3, 6, 9, and 12-month periods
- Filters out ETFs with returns below bond performance
- **NEW: Tracks month-over-month changes for top 5 tickers**
- Provides web dashboard for easy viewing
- Automated monthly updates via GitHub Actions

## Quick Start

### Option 1: Use the Local Server (Recommended)
```bash
# Refresh data and start local server with cache-busting
python3 refresh_data.py
python3 serve.py
```
Then open http://localhost:8000 in your browser.

### Option 2: Direct File Access
```bash
# Refresh data
python3 refresh_data.py

# Open index.html in your browser
open index.html
```

### Option 3: GitHub Pages (Public URL)
The dashboard is also available at: `https://bstefco.github.io/momentumsector/`

**To update GitHub Pages with latest data:**
```bash
# Update local data
python3 refresh_data.py

# Update GitHub Pages files
python3 update_github_pages.py

# Commit and push
git add docs/ && git commit -m "Update GitHub Pages"
git push origin main
```

## Historical Tracking

The dashboard now includes a **"Top 5 Changes vs Previous Month"** section that shows:

- **🆕 New entries** - Tickers that entered the top 5
- **❌ Exits** - Tickers that dropped out of the top 5  
- **↗️↘️ Rank changes** - Tickers that moved up or down in rank
- **Momentum changes** - Percentage change in momentum scores

This helps you understand:
- Which sectors are gaining/losing momentum
- How stable the top performers are
- Market rotation patterns over time

## Cache Issues and Solutions

If you're seeing outdated data or fewer tickers than expected:

### Browser Cache Issues
1. **Hard Refresh**: Press `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
2. **Clear Cache**: Clear your browser's cache for this site
3. **Incognito Mode**: Open the dashboard in incognito/private browsing mode

### Server-Side Solutions
The dashboard now includes multiple cache-busting mechanisms:
- HTTP headers preventing caching
- URL parameters with timestamps
- Random values to ensure fresh requests
- Console logging to verify data loading

### Manual Data Refresh
```bash
# Run the complete refresh process
python3 refresh_data.py

# Or run individual steps
python3 sector_momentum_screen.py
python3 generate_data_json.py
```

## File Structure

- `sector_momentum_screen.py` - Main momentum calculation script
- `generate_data_json.py` - Converts CSV to JSON for dashboard
- `historical_data.py` - **NEW: Historical tracking and comparison**
- `refresh_data.py` - Complete data refresh with verification
- `serve.py` - Local HTTP server with cache-busting headers
- `index.html` - Web dashboard
- `data.json` - Dashboard data (generated)
- `momentum_scores.csv` - Raw momentum data (generated)
- `historical_momentum.json` - **NEW: Historical top 5 data**

## Data Verification

The refresh script automatically verifies:
- ✅ Total number of tickers (should be 24)
- ✅ Number of winners (should be 3)
- ✅ Unique momentum scores (should be 22+ different values)
- ✅ Data freshness (run date)
- ✅ Historical comparison data

## Troubleshooting

### Still seeing old data?
1. Run `python3 refresh_data.py`
2. Use `python3 serve.py` instead of opening files directly
3. Check browser console for loading messages
4. Verify `data.json` has the correct number of tickers

### Momentum scores all the same?
This indicates a calculation bug. The refresh script will detect this and warn you.

### Missing tickers?
Check that all 25 tickers in the universe are available. Some may be delisted.

### No historical changes showing?
- First run: No previous data available (normal)
- Subsequent runs: Check that `historical_momentum.json` exists and is valid

## GitHub Actions

The workflow runs monthly and includes:
- Momentum screening
- Data generation
- Historical comparison
- Data verification
- Automatic commits
- Email notifications

## Dependencies

- Python 3.11+
- pandas
- yfinance
- numpy

Install with: `pip install pandas yfinance numpy` 