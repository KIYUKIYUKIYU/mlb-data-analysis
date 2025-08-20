import sys
sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from src.mlb_api_client import MLBApiClient
import json

# APIクライアント作成
api_client = MLBApiClient()

# Yankees (147) のブルペン統計を取得
team_id = 147
season = 2024

print("=== get_bullpen_stats の戻り値確認 ===")
bullpen_stats = api_client.get_bullpen_stats(team_id, season)

print(f"\n1. bullpen_statsの型: {type(bullpen_stats)}")
print(f"2. 要素数: {len(bullpen_stats)}")

if len(bullpen_stats) > 0:
    print("\n3. 最初の投手データ:")
    first_pitcher = bullpen_stats[0]
    print(f"   型: {type(first_pitcher)}")
    print(f"   キー: {list(first_pitcher.keys())}")
    
    print(f"\n4. 投手情報:")
    print(f"   ID: {first_pitcher.get('id')}")
    print(f"   名前: {first_pitcher.get('name')}")
    
    print(f"\n5. stats の内容:")
    stats = first_pitcher.get('stats', {})
    print(f"   型: {type(stats)}")
    print(f"   キー数: {len(stats)}")
    
    if isinstance(stats, dict):
        # 重要な統計情報を表示
        print(f"\n6. 重要な統計:")
        print(f"   gamesPitched: {stats.get('gamesPitched')}")
        print(f"   gamesStarted: {stats.get('gamesStarted')}")
        print(f"   saves: {stats.get('saves')}")
        print(f"   holds: {stats.get('holds')}")
        print(f"   era: {stats.get('era')}")
        print(f"   whip: {stats.get('whip')}")
        print(f"   strikeOuts: {stats.get('strikeOuts')}")
        print(f"   baseOnBalls: {stats.get('baseOnBalls')}")
        print(f"   battersFaced: {stats.get('battersFaced')}")

print("\n=== 結論 ===")
print("get_bullpen_stats は既に stats[0]['stat'] を抽出済み")
print("bullpen_enhanced_stats.py はこの形式を前提に処理すべき")