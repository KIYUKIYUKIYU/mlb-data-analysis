import requests
import json

team_id = 147  # Yankees
base_url = "https://statsapi.mlb.com"

print("=== 2025年シーズン統計の取得テスト ===\n")

# 1. 基本的なリクエスト
print("1. 基本リクエスト:")
url = f"{base_url}/api/v1/teams/{team_id}/stats"
params = {
    'stats': 'season',
    'season': 2025,
    'gameType': 'R'
}
response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
print(f"URL: {response.url}")

# 2. パラメータを文字列に
print("\n2. パラメータを文字列に:")
params_str = {
    'stats': 'season',
    'season': '2025',
    'gameType': 'R'
}
response2 = requests.get(url, params=params_str)
print(f"Status: {response2.status_code}")

# 3. 2024年で試す
print("\n3. 2024年シーズン:")
params_2024 = {
    'stats': 'season',
    'season': 2024,
    'gameType': 'R'
}
response3 = requests.get(url, params=params_2024)
print(f"Status: {response3.status_code}")
if response3.status_code == 200:
    data = response3.json()
    if data.get('stats'):
        stat = data['stats'][0]['splits'][0]['stat']
        print(f"2024 AVG: {stat.get('avg')}, OPS: {stat.get('ops')}")

# 4. 異なるstatsタイプ
print("\n4. 利用可能なstatsタイプ:")
stats_types = ['season', 'seasonAdvanced', 'yearByYear', 'career']
for stat_type in stats_types:
    params = {'stats': stat_type, 'season': 2025, 'gameType': 'R'}
    response = requests.get(url, params=params)
    print(f"  {stat_type}: Status {response.status_code}")

# 5. hydrate付き
print("\n5. hydrateパラメータ付き:")
params_hydrate = {
    'stats': 'season',
    'season': 2025,
    'gameType': 'R',
    'hydrate': 'team'
}
response5 = requests.get(url, params=params_hydrate)
print(f"Status: {response5.status_code}")