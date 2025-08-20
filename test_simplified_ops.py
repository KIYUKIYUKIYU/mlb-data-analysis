 
import sys
sys.path.append('.')
from src.mlb_api_client import MLBApiClient
from datetime import datetime, timedelta

# MLBApiClientに新しいメソッドを追加する必要があります
# まず、現在のcalculate_team_recent_opsメソッドをバックアップして
# 上記の簡略化されたバージョンに置き換えます

client = MLBApiClient()
team_id = 144  # Atlanta Braves

print(f"Testing simplified OPS calculation for team {team_id}")
print(f"Current date: {datetime.now()}")

# 過去5試合
ops_5 = client.calculate_team_recent_ops(team_id, 5)
print(f"\nLast 5 games OPS: {ops_5}")

# 過去10試合
ops_10 = client.calculate_team_recent_ops(team_id, 10)
print(f"Last 10 games OPS: {ops_10}")

# gameLogエンドポイントのテスト
import requests
response = requests.get(
    f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats",
    params={
        'stats': 'gameLog',
        'season': 2024,
        'gameType': 'R'
    }
)
print(f"\nGameLog API status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if data.get('stats'):
        print("GameLog data available!")