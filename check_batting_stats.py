import sys
sys.path.append('.')
from src.mlb_api_client import MLBApiClient
from scripts.batting_quality_stats import BattingQualityStats

client = MLBApiClient()
batting = BattingQualityStats()

# テストチーム
test_teams = [
    (147, "Yankees"),
    (133, "Athletics"),
    (116, "Tigers")
]

print("=== チーム打撃データ確認 ===\n")

for team_id, team_name in test_teams:
    print(f"\n【{team_name}】")
    
    # 1. シーズン統計（2025年）
    season_stats = client.get_team_stats(team_id, 2025)
    print(f"シーズン統計取得: {'成功' if season_stats else '失敗'}")
    
    if season_stats:
        print(f"  AVG: {season_stats.get('avg', 'N/A')}")
        print(f"  OPS: {season_stats.get('ops', 'N/A')}")
        print(f"  本塁打: {season_stats.get('homeRuns', 'N/A')}")
        print(f"  得点: {season_stats.get('runs', 'N/A')}")
    
    # 2. 過去試合OPS
    ops_5 = client.calculate_team_recent_ops_with_cache(team_id, 5)
    ops_10 = client.calculate_team_recent_ops_with_cache(team_id, 10)
    print(f"\n過去試合OPS:")
    print(f"  5試合: {ops_5}")
    print(f"  10試合: {ops_10}")
    
    # 3. Barrel%/Hard-Hit%
    quality = batting.get_team_quality_stats(team_id)
    print(f"\n品質統計:")
    print(f"  Barrel%: {quality['barrel_pct']}%")
    print(f"  Hard-Hit%: {quality['hard_hit_pct']}%")
    print(f"  データソース: {quality['data_source']}")
    
    # 4. 対左右投手成績
    splits = client.get_team_splits_vs_pitchers(team_id, 2025)
    print(f"\n対投手成績:")
    
    # 文字列の場合はfloatに変換
    vs_left_avg = float(splits['vs_left']['avg']) if isinstance(splits['vs_left']['avg'], str) else splits['vs_left']['avg']
    vs_left_ops = float(splits['vs_left']['ops']) if isinstance(splits['vs_left']['ops'], str) else splits['vs_left']['ops']
    vs_right_avg = float(splits['vs_right']['avg']) if isinstance(splits['vs_right']['avg'], str) else splits['vs_right']['avg']
    vs_right_ops = float(splits['vs_right']['ops']) if isinstance(splits['vs_right']['ops'], str) else splits['vs_right']['ops']
    
    print(f"  対左: AVG {vs_left_avg:.3f} (OPS {vs_left_ops:.3f})")
    print(f"  対右: AVG {vs_right_avg:.3f} (OPS {vs_right_ops:.3f})")
    
    print("-" * 50)