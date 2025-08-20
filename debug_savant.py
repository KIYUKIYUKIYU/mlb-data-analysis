import json
import os

# キャッシュファイルを直接読み込む
cache_file = "cache/statcast_data/all_teams_statcast_2025.json"

print(f"Cache file exists: {os.path.exists(cache_file)}")

if os.path.exists(cache_file):
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\nCache timestamp: {data.get('timestamp')}")
    print(f"Number of teams: {len(data.get('data', {}))}")
    
    # データの構造を確認
    if data.get('data'):
        first_key = list(data['data'].keys())[0]
        print(f"\nFirst key type: {type(first_key)} ({first_key})")
        print(f"First value: {data['data'][first_key]}")
        
        # 特定のチームを確認
        for team_id in [147, 121, 136, 133]:
            # 文字列と数値の両方で試す
            if str(team_id) in data['data']:
                print(f"\nTeam {team_id} (as string): {data['data'][str(team_id)]}")
            elif team_id in data['data']:
                print(f"\nTeam {team_id} (as int): {data['data'][team_id]}")
            else:
                print(f"\nTeam {team_id}: NOT FOUND")