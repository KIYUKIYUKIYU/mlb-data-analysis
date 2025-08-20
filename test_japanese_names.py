from scripts.accurate_name_database import AccurateNameDatabase

# データベースをテスト
db = AccurateNameDatabase()
db.load_database()

# チーム名をテスト
print("チーム名テスト:")
print(f"Detroit Tigers → {db.get_team_name_jp('Detroit Tigers')}")
print(f"New York Yankees → {db.get_team_name_jp('New York Yankees')}")

# 選手名をテスト
print("\n選手名テスト:")
print(f"Shohei Ohtani → {db.get_player_name_jp('Shohei Ohtani')}")