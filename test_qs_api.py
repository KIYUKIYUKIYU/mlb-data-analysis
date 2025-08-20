from src.mlb_api_client import MLBApiClient
import json

client = MLBApiClient()

# テスト用投手ID（例：Kevin Gausman）
pitcher_id = 592332

# 1. 基本的なseason統計
print("=== Season Stats ===")
season_stats = client.get_player_stats_by_season(pitcher_id, 2025, "pitching")
print(json.dumps(season_stats, indent=2))

# 2. sabermetrics統計を確認
print("\n=== Sabermetrics Stats ===")
try:
    response = client.session.get(
        f"{client.base_url}/api/v1/people/{pitcher_id}/stats",
        params={
            'stats': 'sabermetrics',
            'season': 2025,
            'group': 'pitching'
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

# 3. seasonAdvanced統計を確認
print("\n=== Season Advanced Stats ===")
try:
    response = client.session.get(
        f"{client.base_url}/api/v1/people/{pitcher_id}/stats",
        params={
            'stats': 'seasonAdvanced',
            'season': 2025,
            'group': 'pitching'
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

# 4. 利用可能な統計タイプを確認
print("\n=== Available Stat Types ===")
try:
    response = client.session.get(
        f"{client.base_url}/api/v1/statTypes"
    )
    if response.status_code == 200:
        data = response.json()
        for stat_type in data:
            if 'quality' in stat_type.get('name', '').lower():
                print(f"- {stat_type['name']}")
except Exception as e:
    print(f"Error: {e}")