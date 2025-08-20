import sys
sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from datetime import datetime, timedelta
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats

# テスト実行
print("=== ブルペンデバッグ開始 ===")

# Yankees (147) でテスト
team_id = 147
print(f"\nチームID: {team_id} (Yankees)")

# BullpenEnhancedStatsのインスタンス作成
bullpen_stats = BullpenEnhancedStats()

# get_bullpen_statsメソッドを直接呼び出す前に、
# 内部の処理を確認するため、一時的にデバッグ版を作成
import json

# APIクライアントから投手リストを取得
roster = bullpen_stats.api_client.get_team_roster(team_id, season=2025)
print(f"\nロースター人数: {len(roster)}")

# 投手だけをフィルタ
pitchers = [p for p in roster if p.get('position', {}).get('abbreviation') == 'P']
print(f"投手人数: {len(pitchers)}")

# 最初の5人の投手の統計を確認
print("\n=== 投手統計サンプル（最初の5人） ===")
for i, pitcher in enumerate(pitchers[:5]):
    pitcher_id = pitcher.get('person', {}).get('id')
    pitcher_name = pitcher.get('person', {}).get('fullName', 'Unknown')
    
    # 統計取得
    stats_data = bullpen_stats.api_client.get_player_stats(pitcher_id, season=2025, group="pitching")
    
    if stats_data and 'stats' in stats_data and stats_data['stats']:
        stat = stats_data['stats'][0].get('stats', {})
        games_pitched = stat.get('gamesPitched', 0)
        games_started = stat.get('gamesStarted', 0)
        saves = stat.get('saves', 0)
        holds = stat.get('holds', 0)
        
        print(f"\n{i+1}. {pitcher_name}")
        print(f"   GP: {games_pitched}, GS: {games_started}, SV: {saves}, HLD: {holds}")
        
        # リリーフ投手判定
        is_reliever = False
        if saves > 0 or holds > 0:
            is_reliever = True
            print("   → リリーフ投手（SV/HLD有り）")
        elif games_pitched >= 10 and games_started == 0:
            is_reliever = True
            print("   → リリーフ投手（先発なし）")
        elif games_pitched >= 10 and games_pitched > 0:
            avg_ip = stat.get('inningsPitched', 0) / games_pitched if games_pitched > 0 else 0
            if avg_ip < 2.0:
                is_reliever = True
                print(f"   → リリーフ投手（平均IP: {avg_ip:.2f}）")
        
        if not is_reliever:
            print("   → 先発投手またはデータ不足")

print("\n=== 実際のブルペン統計を取得 ===")
try:
    result = bullpen_stats.get_bullpen_stats(team_id)
    print(f"\nActive relievers: {result.get('active_relievers', 0)}")
    print(f"ERA: {result.get('era', 'N/A')}")
    print(f"WHIP: {result.get('whip', 'N/A')}")
    print(f"K-BB%: {result.get('k_bb_percent', 'N/A')}")
except Exception as e:
    print(f"\nエラー発生: {e}")
    import traceback
    traceback.print_exc()