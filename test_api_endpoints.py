 
import requests
import json
from datetime import datetime, timedelta

# 様々なエンドポイントをテスト
base_url = "https://statsapi.mlb.com"

# 日付設定
japan_tomorrow = datetime.now() + timedelta(days=1)
japan_tomorrow = japan_tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
mlb_datetime = japan_tomorrow - timedelta(hours=14)
target_date = mlb_datetime.strftime('%Y-%m-%d')

print(f"Testing date: {target_date}")
print("="*50)

# 1. 基本的なscheduleエンドポイント
print("\n1. Basic schedule endpoint:")
url = f"{base_url}/api/v1/schedule"
params = {'sportId': 1, 'date': target_date}
response = requests.get(url, params=params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if data.get('dates'):
        game = data['dates'][0]['games'][0] if data['dates'][0]['games'] else None
        if game:
            print(f"First game: {game['teams']['away']['team']['name']} @ {game['teams']['home']['team']['name']}")
            print(f"Away pitcher: {game['teams']['away'].get('probablePitcher', 'None')}")

# 2. hydrate付きのエンドポイント
print("\n2. Schedule with hydrate:")
params = {
    'sportId': 1,
    'date': target_date,
    'hydrate': 'team,probablePitcher(note),linescore'
}
response = requests.get(url, params=params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if data.get('dates') and data['dates'][0]['games']:
        game = data['dates'][0]['games'][0]
        away_pitcher = game['teams']['away'].get('probablePitcher')
        if away_pitcher:
            print(f"Away pitcher with hydrate: {away_pitcher.get('fullName')} - Note: {away_pitcher.get('note', 'No note')}")

# 3. 別のエンドポイント - game endpoint
print("\n3. Alternative - Games endpoint:")
# 最新の試合を取得
schedule_response = requests.get(f"{base_url}/api/v1/schedule", params={'sportId': 1, 'date': target_date})
if schedule_response.status_code == 200:
    schedule_data = schedule_response.json()
    if schedule_data.get('dates') and schedule_data['dates'][0]['games']:
        game_pk = schedule_data['dates'][0]['games'][0]['gamePk']
        
        # gameエンドポイント
        game_url = f"{base_url}/api/v1.1/game/{game_pk}/feed/live"
        game_response = requests.get(game_url)
        print(f"Game feed status: {game_response.status_code}")
        
        if game_response.status_code == 200:
            game_data = game_response.json()
            probables = game_data.get('gameData', {}).get('probablePitchers', {})
            if probables:
                print(f"Probable pitchers from game feed: {probables}")

# 4. pybaseballのアプローチ（参考）
print("\n4. Alternative approach (like pybaseball):")
print("pybaseball uses these endpoints:")
print("- https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={date}")
print("- https://statsapi.mlb.com/api/v1/people/{player_id}")

# 5. 実際のリクエストヘッダーを確認
print("\n5. Testing with different headers:")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}
response = requests.get(url, params=params, headers=headers)
print(f"With browser headers - Status: {response.status_code}")