import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mlb_api_client import MLBApiClient
from datetime import datetime, timedelta

# APIクライアントを初期化
api_client = MLBApiClient()

# 利用可能なメソッドを確認
print("Available methods in MLBApiClient:")
for method in dir(api_client):
    if not method.startswith('_'):
        print(f"  - {method}")

# 一般的なメソッド名を試す
print("\nTrying to fetch today's games...")

today = datetime.now().date()
yesterday = today - timedelta(days=1)

# 可能性のあるメソッド名を試す
possible_methods = [
    'get_games_for_date',
    'get_schedule',
    'get_games',
    'get_todays_games',
    'fetch_games',
    'get_daily_schedule'
]

for method_name in possible_methods:
    if hasattr(api_client, method_name):
        print(f"\nFound method: {method_name}")
        try:
            method = getattr(api_client, method_name)
            # メソッドのシグネチャを確認
            import inspect
            sig = inspect.signature(method)
            print(f"  Signature: {sig}")
        except Exception as e:
            print(f"  Error inspecting method: {e}")
        break
else:
    print("\nNo standard game fetching method found")
    
# schedule APIを直接試す
print("\nTrying direct API call...")
import requests

url = f"https://statsapi.mlb.com/api/v1/schedule?date={yesterday}"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    if 'dates' in data and data['dates']:
        print(f"Found {len(data['dates'][0].get('games', []))} games for {yesterday}")
    else:
        print("No games found")