import requests

def search_player(name):
    """選手名で検索"""
    # 現在のロースターから検索
    teams_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    teams_response = requests.get(teams_url)
    teams = teams_response.json()['teams']
    
    for team in teams:
        roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team['id']}/roster/active"
        roster_response = requests.get(roster_url)
        roster_data = roster_response.json()
        
        for player in roster_data.get('roster', []):
            if name.lower() in player['person']['fullName'].lower():
                print(f"Found: {player['person']['fullName']} (ID: {player['person']['id']}) - {team['name']}")
                # 投手の場合、成績も表示
                if player['position']['type'] == 'Pitcher':
                    get_pitcher_stats(player['person']['id'])

def get_pitcher_stats(player_id):
    """投手成績を取得"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
    params = {"stats": "season", "season": 2025, "group": "pitching"}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get('stats'):
        for stat_group in data['stats']:
            if stat_group.get('splits'):
                for split in stat_group['splits']:
                    stats = split.get('stat', {})
                    print(f"  勝敗: {stats.get('wins', 0)}-{stats.get('losses', 0)}, ERA: {stats.get('era', 'N/A')}")

# Paul Skenesを検索
print("Searching for Paul Skenes...")
search_player("Skenes")

print("\n" + "="*50 + "\n")

# 他の注目選手も検索
print("Searching for pitchers with good records...")
search_player("Wheeler")  # Zack Wheeler
search_player("Strider")  # Spencer Strider