import requests
from datetime import datetime
import pytz

print("スクリプト開始...")

try:
    # 基本的な試合データを取得
    print("試合データ取得中...")
    url = "https://statsapi.mlb.com/api/v1/schedule?date=2025-06-22&sportId=1"
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    
    data = response.json()
    
    if 'dates' in data and data['dates']:
        games = data['dates'][0]['games']
        print(f"\n見つかった試合数: {len(games)}")
        
        # 最初の3試合だけ処理
        for i, game in enumerate(games[:3], 1):
            print(f"\n{'='*60}")
            print(f"試合 {i}")
            
            # 基本情報
            away = game['teams']['away']['team']['name']
            home = game['teams']['home']['team']['name']
            
            # 時間
            game_date = datetime.fromisoformat(game['gameDate'].replace('Z', '+00:00'))
            jst = pytz.timezone('Asia/Tokyo')
            game_jst = game_date.astimezone(jst)
            
            print(f"時間: {game_jst.strftime('%m/%d %H:%M')} JST")
            print(f"対戦: {away} @ {home}")
            print(f"状態: {game['status']['detailedState']}")
            
            # 先発投手（もしあれば）
            if 'probablePitcher' in game['teams']['away']:
                away_pitcher = game['teams']['away']['probablePitcher']['fullName']
                pitcher_id = game['teams']['away']['probablePitcher']['id']
                print(f"\nAway先発: {away_pitcher} (ID: {pitcher_id})")
                
                # 投手統計を試す
                try:
                    stats_url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=season&season=2025"
                    stats_resp = requests.get(stats_url)
                    stats_data = stats_resp.json()
                    
                    if 'stats' in stats_data and stats_data['stats']:
                        print("  統計データ: 取得成功")
                    else:
                        print("  統計データ: なし")
                except Exception as e:
                    print(f"  統計エラー: {e}")
            
    else:
        print("試合データが見つかりません")
        
except Exception as e:
    print(f"エラー発生: {e}")
    import traceback
    traceback.print_exc()
    
print("\n完了")