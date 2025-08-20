 
import requests
import json

# テスト用のチームID
team_ids = {
    147: "Yankees",
    110: "Orioles", 
    141: "Blue Jays",
    136: "Mariners"
}

print("=== MLB API Statcast データ確認 (2025年) ===\n")

# 1. 通常のチーム統計API
print("1. 通常のチーム統計 (season stats)")
for team_id, team_name in team_ids.items():
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        'stats': 'season',
        'group': 'hitting',
        'season': 2025,  # 必ず2025年
        'gameType': 'R'
    }
    response = requests.get(url, params=params)
    print(f"{team_name}: Status {response.status_code}")
    
# 2. Advanced Stats API
print("\n2. Advanced Stats (seasonAdvanced)")
for team_id, team_name in team_ids.items():
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        'stats': 'seasonAdvanced',
        'group': 'hitting',
        'season': 2025,  # 必ず2025年
        'gameType': 'R'
    }
    response = requests.get(url, params=params)
    print(f"{team_name}: Status {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        # 最初のチームだけ詳細を表示
        if team_id == 147:
            stats = data.get('stats', [{}])[0].get('splits', [{}])[0].get('stat', {})
            print("  利用可能な統計項目:")
            for key in sorted(stats.keys()):
                if 'barrel' in key.lower() or 'hard' in key.lower():
                    print(f"    - {key}: {stats[key]}")

# 3. Sabermetrics API
print("\n3. Sabermetrics Stats")
url = f"https://statsapi.mlb.com/api/v1/teams/147/stats"
params = {
    'stats': 'sabermetrics',
    'group': 'hitting',
    'season': 2025,  # 必ず2025年
    'gameType': 'R'
}
response = requests.get(url, params=params)
print(f"Yankees Sabermetrics: Status {response.status_code}")

# 4. 過去の試合から集計できるか確認
print("\n4. 最近の試合データから集計")
# 過去10試合のデータを取得して、Barrel%が含まれているか確認
url = "https://statsapi.mlb.com/api/v1/schedule"
params = {
    'teamId': 147,
    'startDate': '2025-06-16',
    'endDate': '2025-06-26',
    'sportId': 1,
    'gameType': 'R'
}
response = requests.get(url, params=params)
print(f"Recent games: Status {response.status_code}")