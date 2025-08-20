import sys
sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats
import json

# BullpenEnhancedStatsのインスタンス作成
bullpen_stats = BullpenEnhancedStats()

# 投手IDリスト（様々なタイプの投手）
test_pitchers = [
    (677076, "Clayton Andrews"),
    (656302, "Clay Holmes"),  # クローザー候補
    (445926, "Gerrit Cole")   # 先発投手
]

for pitcher_id, pitcher_name in test_pitchers:
    print(f"\n{'='*60}")
    print(f"投手: {pitcher_name} (ID: {pitcher_id})")
    print('='*60)
    
    # 統計データ取得
    stats_data = bullpen_stats.api_client.get_player_stats(pitcher_id, season=2024, group="pitching")
    
    if isinstance(stats_data, list) and len(stats_data) > 0:
        stat_data = stats_data[0].get('stat', {})
        
        print(f"\nstat の型: {type(stat_data)}")
        print(f"stat の内容:")
        
        if isinstance(stat_data, dict):
            # 全てのキーと値を表示
            for key, value in stat_data.items():
                print(f"  {key}: {value}")
                
            # リリーフ投手判定
            print(f"\n【リリーフ投手判定】")
            games_pitched = stat_data.get('gamesPitched', 0)
            games_started = stat_data.get('gamesStarted', 0)
            saves = stat_data.get('saves', 0)
            holds = stat_data.get('holds', 0)
            
            is_reliever = False
            reason = ""
            
            if saves > 0 or holds > 0:
                is_reliever = True
                reason = f"SV/HLD有り (SV:{saves}, HLD:{holds})"
            elif games_pitched >= 10 and games_started == 0:
                is_reliever = True
                reason = "先発登板なし"
            elif games_pitched > 0:
                innings_str = stat_data.get('inningsPitched', '0')
                try:
                    # 文字列形式の投球回を数値に変換
                    if '.' in innings_str:
                        parts = innings_str.split('.')
                        innings = int(parts[0]) + int(parts[1]) / 3.0
                    else:
                        innings = float(innings_str)
                    
                    avg_ip = innings / games_pitched
                    if games_pitched >= 10 and avg_ip < 2.0:
                        is_reliever = True
                        reason = f"平均投球回 {avg_ip:.2f}"
                except:
                    pass
            
            print(f"  判定結果: {'リリーフ投手' if is_reliever else '先発投手/その他'}")
            if reason:
                print(f"  理由: {reason}")
                
print("\n\n【結論】")
print("stats_data[0]['stat'] に実際の統計データが格納されています。")
print("bullpen_enhanced_stats.py の修正が必要です。")