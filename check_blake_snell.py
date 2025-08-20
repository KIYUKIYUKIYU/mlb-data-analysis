import requests

def check_pitcher_by_name(first_name, last_name):
    """投手名で検索して最新成績を確認"""
    # まず選手を検索
    search_url = f"https://statsapi.mlb.com/api/v1/people/search"
    params = {
        "names": f"{first_name} {last_name}",
        "sportIds": 1,
        "active": True
    }
    
    response = requests.get(search_url, params=params)
    data = response.json()
    
    if data.get('people'):
        for player in data['people']:
            if player['primaryPosition']['code'] == '1':  # 投手
                player_id = player['id']
                print(f"Found: {player['fullName']} (ID: {player_id})")
                
                # 2025年の成績を取得
                stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
                stats_params = {
                    "stats": "season",
                    "season": 2025,
                    "group": "pitching"
                }
                
                stats_response = requests.get(stats_url, params=stats_params)
                stats_data = stats_response.json()
                
                if stats_data.get('stats'):
                    for stat_group in stats_data['stats']:
                        if stat_group.get('splits'):
                            for split in stat_group['splits']:
                                stats = split.get('stat', {})
                                team = split.get('team', {})
                                print(f"\n2025年成績 ({team.get('name', 'Unknown Team')}):")
                                print(f"  登板: {stats.get('gamesPlayed', 0)}")
                                print(f"  先発: {stats.get('gamesStarted', 0)}")
                                print(f"  勝敗: {stats.get('wins', 0)}勝{stats.get('losses', 0)}敗")
                                print(f"  ERA: {stats.get('era', 'N/A')}")
                                print(f"  WHIP: {stats.get('whip', 'N/A')}")
                                print(f"  奪三振: {stats.get('strikeOuts', 0)}")
                                print(f"  与四球: {stats.get('baseOnBalls', 0)}")

# Blake Snellを確認
print("=== Blake Snell ===")
check_pitcher_by_name("Blake", "Snell")

# 他の投手も確認
print("\n=== Drew Rasmussen ===")
check_pitcher_by_name("Drew", "Rasmussen")

print("\n=== Tarik Skubal ===")
check_pitcher_by_name("Tarik", "Skubal")