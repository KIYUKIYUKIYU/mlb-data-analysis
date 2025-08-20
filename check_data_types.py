 
import sys
sys.path.append('.')
from src.mlb_api_client import MLBApiClient
from scripts.enhanced_stats_collector import EnhancedStatsCollector

client = MLBApiClient()
stats_collector = EnhancedStatsCollector()

# Jeffrey Springsのデータを確認
pitcher_id = 605488  # Jeffrey Springs
print("=== 投手データ型確認 ===")
enhanced_stats = stats_collector.get_pitcher_enhanced_stats(pitcher_id)

for key, value in enhanced_stats.items():
    print(f"{key}: {value} (type: {type(value).__name__})")

# チーム統計の確認
print("\n=== チーム統計データ型確認 ===")
team_id = 133  # Athletics
team_stats = client.get_team_stats(team_id, 2025)

for key, value in list(team_stats.items())[:10]:  # 最初の10項目
    print(f"{key}: {value} (type: {type(value).__name__})")