import sys
sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from datetime import datetime, timedelta
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats
import json

# テスト実行
print("=== APIレスポンス形式確認 ===")

# BullpenEnhancedStatsのインスタンス作成
bullpen_stats = BullpenEnhancedStats()

# 最初の投手でテスト（Clayton Andrews）
pitcher_id = 677076
pitcher_name = "Clayton Andrews"

print(f"\n投手: {pitcher_name} (ID: {pitcher_id})")
print("="*50)

# 統計データ取得
stats_data = bullpen_stats.api_client.get_player_stats(pitcher_id, season=2024, group="pitching")

print(f"\n1. stats_dataの型: {type(stats_data)}")

if isinstance(stats_data, list):
    print(f"   リストの長さ: {len(stats_data)}")
    if len(stats_data) > 0:
        print(f"\n2. 最初の要素の型: {type(stats_data[0])}")
        if isinstance(stats_data[0], dict):
            print(f"   最初の要素のキー: {list(stats_data[0].keys())}")
            
            # statsキーを探す
            if 'stats' in stats_data[0]:
                stats_content = stats_data[0]['stats']
                print(f"\n3. stats_data[0]['stats']の型: {type(stats_content)}")
                
                if isinstance(stats_content, list) and len(stats_content) > 0:
                    print(f"   statsリストの長さ: {len(stats_content)}")
                    print(f"   stats[0]の型: {type(stats_content[0])}")
                    
                    if isinstance(stats_content[0], dict):
                        print(f"   stats[0]のキー: {list(stats_content[0].keys())}")
                        
                        # 実際の統計データを探す
                        if 'stat' in stats_content[0]:
                            actual_stats = stats_content[0]['stat']
                            print(f"\n4. 実際の統計データ（stat）:")
                            print(f"   型: {type(actual_stats)}")
                            if isinstance(actual_stats, dict):
                                print(f"   利用可能な統計（一部）:")
                                for key in list(actual_stats.keys())[:10]:
                                    print(f"     - {key}: {actual_stats[key]}")
                                    
                                # リリーフ投手判定に必要な統計
                                print(f"\n5. リリーフ投手判定用の統計:")
                                print(f"   gamesPitched: {actual_stats.get('gamesPitched', 'N/A')}")
                                print(f"   gamesStarted: {actual_stats.get('gamesStarted', 'N/A')}")
                                print(f"   saves: {actual_stats.get('saves', 'N/A')}")
                                print(f"   holds: {actual_stats.get('holds', 'N/A')}")
                                print(f"   inningsPitched: {actual_stats.get('inningsPitched', 'N/A')}")
                        
                        elif 'stats' in stats_content[0]:
                            # 別の構造の可能性
                            actual_stats = stats_content[0]['stats']
                            print(f"\n4. 別構造: stats_content[0]['stats']")
                            print(f"   型: {type(actual_stats)}")
                            if isinstance(actual_stats, dict):
                                print(f"   キー（一部）: {list(actual_stats.keys())[:10]}")

elif isinstance(stats_data, dict):
    print(f"   辞書のキー: {list(stats_data.keys())}")
    
print("\n" + "="*50)
print("6. ゲームログ取得テスト:")
try:
    game_logs = bullpen_stats.api_client.get_player_game_logs(pitcher_id, season=2024)
    print(f"   game_logsの型: {type(game_logs)}")
    
    if isinstance(game_logs, list) and len(game_logs) > 0:
        print(f"   ゲーム数: {len(game_logs)}")
        print(f"   最新試合データ:")
        latest_game = game_logs[0]
        if isinstance(latest_game, dict):
            for key in ['date', 'opponent', 'inningsPitched', 'earnedRuns']:
                print(f"     - {key}: {latest_game.get(key, 'N/A')}")
    elif isinstance(game_logs, dict):
        print(f"   辞書のキー: {list(game_logs.keys())}")
except Exception as e:
    print(f"   エラー: {e}")

print("\n" + "="*50)
print("7. 修正案:")
print("   bullpen_enhanced_stats.pyのget_player_stats呼び出し部分で、")
print("   返り値の形式を正しく処理する必要があります。")