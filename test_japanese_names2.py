from scripts.accurate_name_database import AccurateNameDatabase

db = AccurateNameDatabase()
db.load_database()

# 正しいメソッド名でテスト
print("チーム名テスト:")
print(f"Detroit Tigers → {db.get_team_name('Detroit Tigers')}")

# 利用可能なメソッドを確認
print("\n利用可能なメソッド:")
print([m for m in dir(db) if not m.startswith('_')])