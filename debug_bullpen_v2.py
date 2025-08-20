import sys
sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from datetime import datetime, timedelta
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats

# テスト実行
print("=== ブルペンデバッグ開始（修正版） ===")

# Yankees (147) でテスト
team_id = 147
print(f"\nチームID: {team_id} (Yankees)")

# BullpenEnhancedStatsのインスタンス作成
bullpen_stats = BullpenEnhancedStats()

# APIクライアントから投手リストを取得
roster_data = bullpen_stats.api_client.get_team_roster(team_id, season=2024)
roster = roster_data.get('roster', []) if isinstance(roster_data, dict) else roster_data
print(f"\nロースター人数: {len(roster)}")

# 投手だけをフィルタ（Pで始まるポジション）
pitchers = []
for player in roster:
    if isinstance(player, dict):
        position = player.get('position', {})
        if isinstance(position, dict):
            pos_type = position.get('type', '')
            pos_abbr = position.get('abbreviation', '')
            if pos_type == 'Pitcher' or pos_abbr in ['P', 'SP', 'RP']:
                pitchers.append(player)

print(f"投手人数: {len(pitchers)}")

# 最初の5人の投手の統計を確認
print("\n=== 投手統計サンプル（最初の5人） ===")
cutoff_date = datetime.now() - timedelta(days=30)
print(f"カットオフ日付（30日前）: {cutoff_date.strftime('%Y-%m-%d')}")

for i, pitcher in enumerate(pitchers[:5]):
    pitcher_info = pitcher.get('person', {})
    pitcher_id = pitcher_info.get('id')
    pitcher_name = pitcher_info.get('fullName', 'Unknown')
    
    # 統計取得
    stats_data = bullpen_stats.api_client.get_player_stats(pitcher_id, season=2024, group="pitching")
    
    if stats_data and 'stats' in stats_data:
        stats_list = stats_data.get('stats', [])
        if stats_list and len(stats_list) > 0:
            stat = stats_list[0].get('stats', {})
            games_pitched = stat.get('gamesPitched', 0)
            games_started = stat.get('gamesStarted', 0)
            saves = stat.get('saves', 0)
            holds = stat.get('holds', 0)
            innings_pitched = stat.get('inningsPitched', '0')
            
            # inningsPitchedを数値に変換
            try:
                ip_float = float(innings_pitched) if innings_pitched else 0
            except:
                ip_float = 0
            
            print(f"\n{i+1}. {pitcher_name} (ID: {pitcher_id})")
            print(f"   GP: {games_pitched}, GS: {games_started}, SV: {saves}, HLD: {holds}")
            print(f"   IP: {innings_pitched}")
            
            # リリーフ投手判定
            is_reliever = False
            reason = ""
            
            if saves > 0 or holds > 0:
                is_reliever = True
                reason = f"SV: {saves}, HLD: {holds}"
            elif games_pitched >= 10 and games_started == 0:
                is_reliever = True
                reason = "先発なし"
            elif games_pitched >= 10 and games_pitched > 0:
                avg_ip = ip_float / games_pitched if games_pitched > 0 else 0
                if avg_ip < 2.0:
                    is_reliever = True
                    reason = f"平均IP: {avg_ip:.2f}"
            
            if is_reliever:
                print(f"   → リリーフ投手（{reason}）")
                
                # 最近の活動をチェック
                recent_activity = bullpen_stats._check_recent_activity(pitcher_id, cutoff_date)
                print(f"   最近30日の登板: {recent_activity.get('games_in_period', 0)}試合")
                print(f"   アクティブ: {recent_activity.get('has_recent_appearance', False)}")
            else:
                print("   → 先発投手またはデータ不足")
        else:
            print(f"\n{i+1}. {pitcher_name} - 統計データなし")

print("\n=== 実際のブルペン統計を取得 ===")
try:
    result = bullpen_stats.get_enhanced_bullpen_stats(team_id, season=2024)
    print(f"\nActive relievers: {result.get('active_relievers', 0)}")
    print(f"ERA: {result.get('era', 'N/A')}")
    print(f"WHIP: {result.get('whip', 'N/A')}")
    print(f"K-BB%: {result.get('k_bb_percent', 'N/A')}%")
    print(f"総投球回: {result.get('total_innings', 0)}")
except Exception as e:
    print(f"\nエラー発生: {e}")
    import traceback
    traceback.print_exc()