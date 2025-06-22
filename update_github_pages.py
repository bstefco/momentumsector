#!/usr/bin/env python3
"""
Script to update GitHub Pages files locally.
This ensures the docs/ folder has the latest data for GitHub Pages deployment.
"""

import os
import shutil
import subprocess
from datetime import datetime

def update_github_pages():
    """Update the docs folder with latest files for GitHub Pages."""
    print(f"🔄 Updating GitHub Pages files at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ensure docs folder exists
    if not os.path.exists('docs'):
        os.makedirs('docs')
        print("📁 Created docs folder")
    
    # Files to copy to docs folder
    files_to_copy = [
        'data.json',
        'index.html', 
        'historical_momentum.json'
    ]
    
    # Copy files
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, f'docs/{file}')
            print(f"✅ Copied {file} to docs/")
        else:
            print(f"⚠️  Warning: {file} not found")
    
    # Check if files were copied successfully
    docs_files = os.listdir('docs')
    print(f"\n📋 Files in docs folder: {', '.join(docs_files)}")
    
    # Verify data.json has the right content
    try:
        import json
        with open('docs/data.json', 'r') as f:
            data = json.load(f)
        
        ticker_count = len(data.get('allEtfs', []))
        has_historical = 'historical_changes' in data
        
        print(f"✅ data.json verification:")
        print(f"   📊 Total tickers: {ticker_count}")
        print(f"   📈 Historical changes: {'Yes' if has_historical else 'No'}")
        
    except Exception as e:
        print(f"❌ Error verifying data.json: {e}")
    
    print(f"\n🎉 GitHub Pages files updated successfully!")
    print("💡 Next steps:")
    print("   1. Commit changes: git add docs/ && git commit -m 'Update GitHub Pages'")
    print("   2. Push to GitHub: git push origin main")
    print("   3. Wait a few minutes for GitHub Pages to update")

if __name__ == "__main__":
    update_github_pages() 