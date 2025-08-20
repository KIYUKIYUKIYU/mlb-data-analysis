 
import requests
import json

print("=== 2025年 MLB API 詳細データ確認 ===\n")

team_id = 147  # Yankees

# 1. seasonAdvanced の詳細確認
print("1. Season Advanced Stats の内容:")
url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
params = {
    'stats': 'seasonAdvanced',
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
        print(f"  取得できた統計項目数: {len(stat)}")
        
        # 全ての項目を表示
        print("\n  全ての統計項目:")
        for key, value in sorted(stat.items()):
            print(f"    {key}: {value}")
            
        # Barrel%とHard-Hit%を探す
        print("\n  Statcast関連の項目:")
        statcast_found = False
        for key, value in stat.items():
            if any(term in key.lower() for term in ['barrel', 'hard', 'exit', 'launch']):
                print(f"    {key}: {value}")
                statcast_found = True
        
        if not statcast_found:
            print("    Statcast関連の項目は見つかりませんでした")

# 2. Sabermetrics の詳細確認
print("\n\n2. Sabermetrics Stats の内容:")
params['stats'] = 'sabermetrics'
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    stats_list = data.get('stats', [])
    
    if stats_list and stats_list[0].get('splits'):
        stat = stats_list[0]['splits'][0].get('stat', {})
        print(f"  取得できた統計項目数: {len(stat)}")
        
        # Statcast関連を探す
        statcast_found = False
        for key, value in stat.items():
            if any(term in key.lower() for term in ['barrel', 'hard', 'exit', 'launch']):
                print(f"    {key}: {value}")
                statcast_found = True
        
        if not statcast_found:
            print("    Statcast関連の項目は見つかりませんでした")

# 3. 通常のseason statsも確認
print("\n\n3. 通常のSeason Stats の内容:")
params['stats'] = 'season'
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    stats_list = data.get('stats', [])
    
    if stats_list and stats_list[0].get('splits'):
        stat = stats_list[0]['splits'][0].get('stat', {})
        
        # Statcast関連を探す
        statcast_found = False
        for key, value in stat.items():
            if any(term in key.lower() for term in ['barrel', 'hard', 'exit', 'launch']):
                print(f"    {key}: {value}")
                statcast_found = True
        
        if not statcast_found:
            print("    Statcast関連の項目は見つかりませんでした")

# 4. 利用可能な全てのstatsタイプを確認
print("\n\n4. 利用可能な全statsタイプ:")
stats_types = ['season', 'seasonAdvanced', 'sabermetrics', 'statcast', 
               'expectedStatistics', 'hotColdZones', 'spraychart']

for stat_type in stats_types:
    params['stats'] = stat_type
    response = requests.get(url, params=params)
    print(f"  {stat_type}: Status {response.status_code}")