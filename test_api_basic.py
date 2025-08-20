 
import requests

base_url = "https://statsapi.mlb.com"
team_id = 147  # Yankees

print("=== MLB API 基本動作確認 ===\n")

# 1. チーム情報（最も基本的なエンドポイント）
print("1. チーム基本情報:")
url = f"{base_url}/api/v1/teams/{team_id}"
response = requests.get(url)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    team = data.get('teams', [{}])[0]
    print(f"Team: {team.get('name')}")

# 2. statsエンドポイントの構造を確認
print("\n2. Stats APIの詳細確認:")
# groupパラメータを追加
url = f"{base_url}/api/v1/teams/{team_id}/stats"
params = {
    'stats': 'season',
    'season': 2024,
    'group': 'hitting'  # これが必要かも
}
response = requests.get(url, params=params)
print(f"With group=hitting: Status {response.status_code}")

# 3. 異なるアプローチ
print("\n3. 別のエンドポイント構造:")
# /stats/team のような構造
url2 = f"{base_url}/api/v1/stats"
params2 = {
    'stats': 'season',
    'season': 2024,
    'teamId': team_id,
    'group': 'hitting',
    'gameType': 'R'
}
response2 = requests.get(url2, params=params2)
print(f"Alternative endpoint: Status {response2.status_code}")

# 4. 現在利用可能なシーズンを確認
print("\n4. 利用可能なシーズン確認:")
for year in [2023, 2024, 2025]:
    url = f"{base_url}/api/v1/teams/{team_id}/stats"
    params = {
        'stats': 'season',
        'season': year,
        'group': 'hitting',
        'gameType': 'R'
    }
    response = requests.get(url, params=params)
    print(f"Year {year} (with group): Status {response.status_code}")

# 5. ドキュメントに記載されていそうな方法
print("\n5. sportIdを追加:")
params_sport = {
    'stats': 'season',
    'season': 2024,
    'group': 'hitting',
    'gameType': 'R',
    'sportId': 1
}
response5 = requests.get(f"{base_url}/api/v1/teams/{team_id}/stats", params=params_sport)
print(f"With sportId: Status {response5.status_code}")