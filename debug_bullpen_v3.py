import sys
sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from datetime import datetime, timedelta
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats

# テスト実行
print("=== ブルペンデバッグ開始（詳細版） ===")

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
                print(f"投手発見: {player.get('person', {}).get('fullName')} - {pos_abbr}")

print(f"\n投手人数: {len(pitchers)}")

# 最初の3人の投手の統計を詳細に確認
print("\n=== 投手統計詳細（最初の3人） ===")
cutoff_date = datetime.now() - timedelta(days=30)
print(f"カットオフ日付（30日前）: {cutoff_date.strftime('%Y-%m-%d')}")

for i, pitcher in enumerate(pitchers[:3]):
    pitcher_info = pitcher.get('person', {})
    pitcher_id = pitcher_info.get('id')
    pitcher_name = pitcher_info.get('fullName', 'Unknown')
    
    print(f"\n--- {i+1}. {pitcher_name} (ID: {pitcher_id}) ---")
    
    # 統計取得
    try:
        stats_data = bullpen_stats.api_client.get_player_stats(pitcher_id, season=2024, group="pitching")
        print(f"統計データ取得: {'成功' if stats_data else '失敗'}")
        
        if stats_data:
            print(f"stats_dataのキー: {list(stats_data.keys())}")
            stats_list = stats_data.get('stats', [])
            print(f"stats_listの長さ: {len(stats_list)}")
            
            if stats_list and len(stats_list) > 0:
                first_stat = stats_list[0]
                print(f"first_statのキー: {list(first_stat.keys())}")
                
                stat = first_stat.get('stats', {})
                print(f"利用可能な統計キー（一部）: {list(stat.keys())[:10]}")
                
                games_pitched = stat.get('gamesPitched', 0)
                games_started = stat.get('gamesStarted', 0)
                saves = stat.get('saves', 0)
                holds = stat.get('holds', 0)
                innings_pitched = stat.get('inningsPitched', '0')
                
                print(f"GP: {games_pitched}, GS: {games_started}, SV: {saves}, HLD: {holds}, IP: {innings_pitched}")
                
                # リリーフ投手判定の詳細
                if saves > 0 or holds > 0:
                    print("→ リリーフ投手判定: SV/HLD有り")
                elif games_pitched >= 10 and games_started == 0:
                    print("→ リリーフ投手判定: 先発なし")
                else:
                    print("→ リリーフ投手判定: 該当せず")
                
                # ゲームログ取得テスト
                print("\n最近のゲームログ取得テスト:")
                try:
                    game_logs = bullpen_stats.api_client.get_player_game_logs(pitcher_id, season=2024)
                    if game_logs:
                        print(f"ゲームログ取得成功: {len(game_logs)}試合")
                        if len(game_logs) > 0:
                            print(f"最新試合: {game_logs[0].get('date', 'N/A')}")
                    else:
                        print("ゲームログなし")
                except Exception as e:
                    print(f"ゲームログ取得エラー: {e}")
                    
    except Exception as e:
        print(f"統計取得エラー: {e}")

print("\n=== 実際のブルペン統計を取得（デバッグモード） ===")
# get_enhanced_bullpen_statsの内部処理を一部再現
try:
    # キャッシュを無効化して強制的に再計算
    result = bullpen_stats.get_enhanced_bullpen_stats(team_id, season=2024)
    
    print(f"\nActive relievers: {result.get('active_relievers', 0)}")
    print(f"ERA: {result.get('era', 'N/A')}")
    print(f"WHIP: {result.get('whip', 'N/A')}")
    print(f"K-BB%: {result.get('k_bb_percent', 'N/A')}%")
    print(f"総投球回: {result.get('total_innings', 0)}")
    
    # 結果の詳細を表示
    print(f"\n結果の全キー: {list(result.keys())}")
    
except Exception as e:
    print(f"\nエラー発生: {e}")
    import traceback
    traceback.print_exc()