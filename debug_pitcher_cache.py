import os
import json
from datetime import datetime

# キャッシュファイルの場所を確認
cache_files = [
    "cache/advanced_stats/pitcher_694973_2025.json",  # Paul Skenes
    "cache/advanced_stats/pitcher_669373_2025.json",  # Tarik Skubal
    "cache/advanced_stats/pitcher_554430_2025.json",  # Zack Wheeler
]

for file_path in cache_files:
    if os.path.exists(file_path):
        print(f"\nFound cache file: {file_path}")
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"Last modified: {mtime}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            if 'stats' in data:
                print(f"Cached W-L: {data['stats'].get('wins', 0)}-{data['stats'].get('losses', 0)}")
                print(f"Cached ERA: {data['stats'].get('era', 'N/A')}")
                print(f"Cache timestamp: {data.get('timestamp', 'N/A')}")
    else:
        print(f"\nCache file not found: {file_path}")