from datetime import datetime, timedelta

print("現在の日本時間:", datetime.now())
print("明日の日本時間:", datetime.now() + timedelta(days=1))

# MLBの時間計算
japan_tomorrow = datetime.now() + timedelta(days=1)
us_game_date = japan_tomorrow - timedelta(hours=14)

print("\n日本の明日:", japan_tomorrow.strftime('%Y-%m-%d'))
print("MLBの日付（-14時間）:", us_game_date.strftime('%Y-%m-%d'))

# もし6/26の試合を取得したい場合
japan_626 = datetime(2025, 6, 26)
us_626 = japan_626 - timedelta(hours=14)
print("\n6/26の試合を取得するためのMLB日付:", us_626.strftime('%Y-%m-%d'))