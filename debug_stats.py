from scripts.enhanced_stats_collector import EnhancedStatsCollector
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats
from scripts.batting_quality_stats import BattingQualityStats

# Yankees (147)でテスト
team_id = 147

print("=== Enhanced Stats Collector ===")
esc = EnhancedStatsCollector()
# 適当な投手IDでテスト（例：Gerrit Cole = 543037）
pitcher_stats = esc.get_pitcher_enhanced_stats(543037)
print(f"Pitcher stats keys: {list(pitcher_stats.keys())}")
print(f"K-BB%: {pitcher_stats.get('k_bb_pct')}")

print("\n=== Bullpen Stats ===")
bes = BullpenEnhancedStats()
bullpen = bes.get_enhanced_bullpen_stats(team_id)
print(f"Bullpen keys: {list(bullpen.keys())}")
print(f"Active relievers: {len(bullpen.get('active_relievers', []))}")

print("\n=== Batting Quality ===")
bqs = BattingQualityStats()
quality = bqs.get_team_quality_stats(team_id)
print(f"Quality stats: {quality}")