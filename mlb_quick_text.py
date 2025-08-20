import requests
from datetime import datetime
import pytz

# 6月22日（アメリカ時間）= 6月23日（日本時間）の試合を取得
url = "https://statsapi.mlb.com/api/v1/schedule?date=2025-06-22&sportId=1&hydrate=team,probablePitcher"
response = requests.get(url)
data = response.json()

print("=" * 80)
print("MLB 2025年6月23日（日本時間）試合一覧")
print("=" * 80)

if 'dates' in data and data['dates']:
    games = data['dates'][0]['games']
    
    for i, game in enumerate(games, 1):
        # チーム情報
        away_team = game['teams']['away']['team']['name']
        home_team = game['teams']['home']['team']['name']
        
        # 日時変換
        game_date = datetime.fromisoformat(game['gameDate'].replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        game_date_jst = game_date.astimezone(jst)
        
        # 先発投手
        away_pitcher = "TBA"
        home_pitcher = "TBA"
        
        if 'probablePitcher' in game['teams']['away']:
            away_pitcher = game['teams']['away']['probablePitcher']['fullName']
        if 'probablePitcher' in game['teams']['home']:
            home_pitcher = game['teams']['home']['probablePitcher']['fullName']
        
        # ステータス
        status = game['status']['detailedState']
        
        print(f"\n【試合 {i}】")
        print(f"時間: {game_date_jst.strftime('%m/%d %H:%M')} (日本時間)")
        print(f"対戦: {away_team} @ {home_team}")
        print(f"先発: {away_pitcher} vs {home_pitcher}")
        print(f"状態: {status}")
        print("-" * 60)

print(f"\n合計: {len(games)}試合")