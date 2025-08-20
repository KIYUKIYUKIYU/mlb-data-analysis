import sys
sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from src.mlb_api_client import MLBApiClient

# APIクライアント作成
api_client = MLBApiClient()

# Yankees (147) のロースターを取得
team_id = 147
print("=== ロースターデータ形式確認 ===")

try:
    roster = api_client.get_team_roster(team_id, season=2025)
    
    print(f"\nロースターの型: {type(roster)}")
    print(f"ロースターの長さ: {len(roster) if hasattr(roster, '__len__') else 'N/A'}")
    
    if isinstance(roster, list):
        print("\n最初の3要素:")
        for i, item in enumerate(roster[:3]):
            print(f"\n要素{i+1}:")
            print(f"  型: {type(item)}")
            if isinstance(item, dict):
                print(f"  キー: {list(item.keys())[:5]}...")  # 最初の5キーのみ表示
                # positionキーを探す
                if 'position' in item:
                    print(f"  position: {item['position']}")
                if 'primaryPosition' in item:
                    print(f"  primaryPosition: {item['primaryPosition']}")
            else:
                print(f"  値: {item}")
    else:
        print(f"\nロースターの内容（最初の500文字）:\n{str(roster)[:500]}")
        
except Exception as e:
    print(f"\nエラー発生: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 別の方法でロースター取得を試行 ===")
try:
    # チーム統計から投手情報を取得してみる
    pitching_stats = api_client.get_team_pitching_stats(team_id, season=2025)
    print(f"\n投手統計の型: {type(pitching_stats)}")
    if isinstance(pitching_stats, dict):
        print(f"キー: {list(pitching_stats.keys())}")
except Exception as e:
    print(f"投手統計取得エラー: {e}")