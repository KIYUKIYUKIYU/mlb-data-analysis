"""
投手データ取得のテスト（詳細版）
"""
from src.mlb_api_client import MLBApiClient
from datetime import datetime

print("Testing pitcher data retrieval...")
print(f"Current date: {datetime.now()}")

client = MLBApiClient()

# 複数の投手でテスト
test_pitchers = [
    (543037, "Gerrit Cole"),     # Yankees
    (605483, "Zac Gallen"),      # Diamondbacks  
    (669022, "MacKenzie Gore"),  # Nationals
]

for pitcher_id, name in test_pitchers:
    print(f"\n{'='*50}")
    print(f"Testing {name} (ID: {pitcher_id})")
    
    # 1. 選手情報を取得
    print("\n1. Getting player info...")
    player_info = client.get_player_info(pitcher_id)
    if player_info:
        print(f"Full name: {player_info.get('fullName', 'Unknown')}")
        print(f"Current team: {player_info.get('currentTeam', {}).get('name', 'Unknown')}")
    else:
        print("No player info found")
    
    # 2. 通常のget_player_statsメソッドも試す
    print("\n2. Getting stats with get_player_stats...")
    stats_old = client.get_player_stats(pitcher_id, 2025)
    if stats_old:
        print(f"Found stats with old method: ERA={stats_old.get('era', 'N/A')}")
    
    # 3. 2025年の統計を取得
    print("\n3. Getting 2025 season stats with get_player_stats_by_season...")
    stats = client.get_player_stats_by_season(pitcher_id, 2025, 'pitching')
    if stats:
        print(f"ERA: {stats.get('era', 'N/A')}")
        print(f"Wins: {stats.get('wins', 'N/A')}")
        print(f"Losses: {stats.get('losses', 'N/A')}")
        print(f"WHIP: {stats.get('whip', 'N/A')}")
        print(f"Games: {stats.get('gamesPlayed', 'N/A')}")
    else:
        print("No 2025 stats found")
    
    # 4. 直接APIエンドポイントを確認
    print("\n4. Checking raw API response...")
    endpoint = f"people/{pitcher_id}/stats"
    params = {'stats': 'season', 'season': 2025, 'group': 'pitching'}
    raw_result = client._make_request(endpoint, params)
    if raw_result and 'stats' in raw_result:
        print(f"Raw API returned {len(raw_result['stats'])} stat groups")
        if raw_result['stats']:
            splits = raw_result['stats'][0].get('splits', [])
            print(f"Found {len(splits)} splits")

print("\nTest completed.")