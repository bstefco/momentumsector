#!/usr/bin/env python3
"""
Refresh data script - runs the momentum screen and regenerates all data files
with proper timestamps to ensure fresh data.
"""

import os
import json
import subprocess
from datetime import datetime

def main():
    print(f"🔄 Refreshing momentum data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Run the momentum screen
    print("📊 Running momentum screen...")
    try:
        subprocess.run(["python3", "sector_momentum_screen.py"], check=True)
        print("✅ Momentum screen completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running momentum screen: {e}")
        return
    
    # Step 2: Generate the data.json file
    print("📄 Generating data.json...")
    try:
        subprocess.run(["python3", "generate_data_json.py"], check=True)
        print("✅ data.json generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating data.json: {e}")
        return
    
    # Step 3: Verify the data
    print("🔍 Verifying data...")
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        
        ticker_count = len(data.get('allEtfs', []))
        winners_count = len(data.get('winners', []))
        
        print(f"✅ Data verification complete:")
        print(f"   📊 Total tickers: {ticker_count}")
        print(f"   🏆 Winners: {winners_count}")
        print(f"   📅 Run date: {data.get('run_date', 'N/A')}")
        
        # Check for duplicate momentum scores
        momentum_scores = [etf.get('momentum', 0) for etf in data.get('allEtfs', [])]
        unique_scores = len(set(momentum_scores))
        
        if unique_scores == 1:
            print("⚠️  WARNING: All tickers have the same momentum score!")
        else:
            print(f"✅ Momentum scores are unique ({unique_scores} different values)")
            
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return
    
    # Step 4: Copy to docs folder if it exists
    if os.path.exists('docs'):
        print("📁 Copying to docs folder...")
        try:
            subprocess.run(["cp", "data.json", "docs/"], check=True)
            subprocess.run(["cp", "momentum_scores.json", "docs/"], check=True)
            print("✅ Files copied to docs folder")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error copying to docs: {e}")
    
    print(f"🎉 Data refresh completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 Tip: Use 'python3 serve.py' to start a local server with cache-busting headers")

if __name__ == "__main__":
    main() 