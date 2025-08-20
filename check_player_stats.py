import requests
from datetime import datetime

def get_player_stats(player_id, season=2025):
    """選手の統計情報を取得"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
    params = {
        "stats": "season",
        "season": season,
        "group": "pitching"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get('stats'):
        for stat_group in data['stats']:
            if stat_group.get('splits'):
                for split in stat_group['splits']:
                    stats = split.get('stat', {})
                    print(f"\n選手ID {player_id} の{season}年成績:")
                    print(f"登板: {stats.get('gamesPlayed', 0)}")
                    print(f"勝敗: {stats.get('wins', 0)}勝{stats.get('losses', 0)}敗")
                    print(f"ERA: {stats.get('era', 'N/A')}")
                    print(f"WHIP: {stats.get('whip', 'N/A')}")
                    print(f"奪三振: {stats.get('strikeOuts', 0)}")
                    return stats
    return None

# 例: Tarik Skubal (ID: 669373)
print("=== Tarik Skubal ===")
get_player_stats(669373)

# 例: Paul Skenes (仮のID - 実際のIDに置き換えてください)
print("\n=== Paul Skenes ===")
get_player_stats(695077)  # このIDは仮です

# チーム成績も確認
def get_team_stats(team_id, season=2025):
    """チームの打撃成績を取得"""
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
    params = {
        "season": season,
        "stats": "season",
        "group": "hitting"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get('stats'):
        for stat_group in data['stats']:
            if stat_group.get('splits'):
                for split in stat_group['splits']:
                    stats = split.get('stat', {})
                    print(f"\nチームID {team_id} の{season}年打撃成績:")
                    print(f"打率: {stats.get('avg', 'N/A')}")
                    print(f"OPS: {stats.get('ops', 'N/A')}")
                    print(f"得点: {stats.get('runs', 0)}")
                    print(f"本塁打: {stats.get('homeRuns', 0)}")
                    return stats
    return None

# Yankees (ID: 147)
print("\n=== New York Yankees ===")
get_team_stats(147)