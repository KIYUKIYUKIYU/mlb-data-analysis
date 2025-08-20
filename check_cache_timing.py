 
import os
import json
from datetime import datetime, timedelta

print("=== キャッシュ更新タイミング確認 ===\n")

# 現在時刻（日本時間）
now_jst = datetime.now()
print(f"現在時刻（日本）: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

# MLB時間（14時間前）
now_mlb = now_jst - timedelta(hours=14)
print(f"現在時刻（MLB）: {now_mlb.strftime('%Y-%m-%d %H:%M:%S')}")

# 試合開始時間の目安
typical_game_times = {
    "デーゲーム": "13:00",
    "ナイトゲーム": "19:00", 
    "西海岸ナイトゲーム": "22:00"
}

print("\n一般的な試合開始時刻（MLB時間）:")
for game_type, time in typical_game_times.items():
    print(f"  {game_type}: {time}")

# キャッシュ確認
savant_cache = "cache/statcast_data/all_teams_statcast_2025.json"

if os.path.exists(savant_cache):
    with open(savant_cache, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cache_time = datetime.fromisoformat(data['timestamp'])
    age = datetime.now() - cache_time
    
    print(f"\n現在のキャッシュ状態:")
    print(f"  作成時刻: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  経過時間: {age}")
    
    # 6時間キャッシュでの次回更新
    if age > timedelta(hours=6):
        print("  ⚠️ キャッシュ期限切れ - 次回実行時に更新されます")
    else:
        remaining = timedelta(hours=6) - age
        next_update = cache_time + timedelta(hours=6)
        print(f"  ✅ キャッシュ有効 - 残り: {remaining}")
        print(f"  次回更新時刻: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")

print("\n推奨更新タイミング:")
print("- 朝6時（日本時間）: 前日のナイトゲーム終了後のデータ")
print("- 正午（日本時間）: デーゲームの途中経過を含む")  
print("- 夕方18時（日本時間）: ナイトゲーム開始前の最新データ")
print("- 深夜0時（日本時間）: 東海岸のナイトゲーム途中経過")