from datetime import datetime, timedelta

# 現在の日本時間
now_jst = datetime.now()
print(f"現在の日本時間: {now_jst}")

# コードの計算方法（現在の実装）
tomorrow_jst = now_jst + timedelta(days=1)
mlb_date = tomorrow_jst - timedelta(hours=14)
print(f"\n現在の実装:")
print(f"  明日の日本時間: {tomorrow_jst}")
print(f"  MLB APIに渡す日付: {mlb_date.strftime('%Y-%m-%d')}")

# 正しい計算方法
# 日本時間の6/27の試合 = MLB時間の6/26と6/27にまたがる
target_date_jst = now_jst.replace(hour=0, minute=0, second=0) + timedelta(days=1)
target_date_mlb = (target_date_jst - timedelta(hours=14)).strftime('%Y-%m-%d')

print(f"\n正しい計算:")
print(f"  日本時間6/27の0時: {target_date_jst}")
print(f"  対応するMLB時間: {target_date_jst - timedelta(hours=14)}")
print(f"  MLB APIに渡すべき日付: {target_date_mlb}")