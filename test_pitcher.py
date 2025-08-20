 
from src.mlb_api_client import MLBApiClient
import json

client = MLBApiClient()

# Kevin Gausmanの例（実際のIDに置き換え）
pitcher_id = 592332  # 仮のID

# 基本情報
info = client.get_player_info(pitcher_id)
print("Player Info:", json.dumps(info, indent=2))

# 2025年の統計
stats = client.get_player_stats_by_season(pitcher_id, 2025, "pitching")
print("\n2025 Stats:", json.dumps(stats, indent=2))

# 2024年の統計（比較用）
stats_2024 = client.get_player_stats_by_season(pitcher_id, 2024, "pitching")
print("\n2024 Stats:", json.dumps(stats_2024, indent=2))