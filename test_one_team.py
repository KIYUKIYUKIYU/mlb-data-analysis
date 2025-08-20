 
import sys
sys.path.append('.')

from scripts.batting_quality_stats import BattingQualityStats

# テスト
stats = BattingQualityStats()

# Yankees (147)のデータを取得
team_id = 147
result = stats.get_team_quality_stats(team_id)

print(f"\nTeam {team_id} Quality Stats:")
print(f"Barrel%: {result['barrel_pct']:.1f}%")
print(f"Hard-Hit%: {result['hard_hit_pct']:.1f}%")
print(f"Source: {result['data_source']}")