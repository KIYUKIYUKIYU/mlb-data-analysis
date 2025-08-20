 
import sys
sys.path.append('.')

from scripts.batting_quality_stats import BattingQualityStats

stats = BattingQualityStats()

# いくつかのチームをテスト
test_teams = {
    147: "Yankees",
    121: "Mets", 
    136: "Mariners",
    133: "Athletics"
}

print("\nTeam Barrel% and Hard-Hit% (from Savant):")
print("-" * 50)

for team_id, team_name in test_teams.items():
    result = stats.get_team_quality_stats(team_id)
    print(f"{team_name:12} - Barrel: {result['barrel_pct']:5.1f}%, "
          f"Hard-Hit: {result['hard_hit_pct']:5.1f}% "
          f"(source: {result['data_source']})")