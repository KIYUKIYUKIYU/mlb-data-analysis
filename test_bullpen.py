 
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats
from src.mlb_api_client import MLBApiClient

# チームのロースターを確認
client = MLBApiClient()
roster = client.get_team_roster(117)  # Astros
print(f"ロースター人数: {len(roster)}")

# ブルペン統計を確認
bullpen = BullpenEnhancedStats()
data = bullpen.get_enhanced_bullpen_stats(117)
print(f"アクティブリリーバー: {len(data.get('active_relievers', []))}")
print(f"ERA: {data.get('era')}")
print(f"FIP: {data.get('fip')}")