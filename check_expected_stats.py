 
import requests
import json

print("=== Expected Statistics 詳細確認 ===\n")

team_id = 147  # Yankees

url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
params = {
    'stats': 'expectedStatistics',
    'group': 'hitting',
    'season': 2025,
    'gameType': 'R'
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    stats_list = data.get('stats', [])
    
    if stats_list and stats_list[0].get('splits'):
        stat = stats_list[0]['splits'][0].get('stat', {})
        print(f"取得できた統計項目数: {len(stat)}")
        
        print("\n全ての統計項目:")
        for key, value in sorted(stat.items()):
            print(f"  {key}: {value}")
else:
    print(f"Error: Status {response.status_code}")

# 個別の試合データからBarrel%を集計できるか確認
print("\n\n=== 個別試合データの確認 ===")

# 最新の試合を1つ取得
schedule_url = "https://statsapi.mlb.com/api/v1/schedule"
schedule_params = {
    'teamId': team_id,
    'startDate': '2025-06-20',
    'endDate': '2025-06-26',
    'sportId': 1,
    'gameType': 'R'
}

schedule_response = requests.get(schedule_url, params=schedule_params)
if schedule_response.status_code == 200:
    schedule_data = schedule_response.json()
    
    # 最新の試合を探す
    for date_info in schedule_data.get('dates', []):
        for game in date_info.get('games', []):
            if game.get('status', {}).get('abstractGameState') == 'Final':
                game_pk = game['gamePk']
                print(f"\nGame {game_pk} の詳細データ:")
                
                # 試合の詳細データを取得
                game_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
                game_response = requests.get(game_url)
                
                if game_response.status_code == 200:
                    game_data = game_response.json()
                    
                    # プレイバイプレイデータを確認
                    plays = game_data.get('liveData', {}).get('plays', {}).get('allPlays', [])
                    
                    if plays:
                        print(f"  プレイ数: {len(plays)}")
                        
                        # 最初のプレイのデータ構造を確認
                        first_play = plays[0]
                        if 'playEvents' in first_play:
                            events = first_play['playEvents']
                            if events:
                                print("\n  プレイイベントのデータ構造:")
                                event = events[0]
                                for key in event.keys():
                                    if 'hit' in key.lower() or 'launch' in key.lower() or 'exit' in key.lower():
                                        print(f"    {key}: {event.get(key)}")
                
                break  # 1試合だけ確認
        break  # 1日だけ確認