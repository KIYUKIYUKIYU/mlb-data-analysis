# KeyErrorを修正
with open("scripts/discord_report_with_table_jp.py", 'r', encoding='utf-8') as f:
    content = f.read()

# 582行目のprint文を修正
# 古い書き方を新しい書き方に変更
old_line = "print(f\"試合 {i+1}/{min(3, len(games_data))}: {game['away_team']} @ {game['home_team']}\")"
new_line = """print(f"試合 {i+1}/{min(3, len(games_data))}: {game.get('away_team', 'Unknown')} @ {game.get('home_team', 'Unknown')}")"""

content = content.replace(old_line, new_line)

# もう一つの方法：tryでエラーハンドリング
alternative = """
            try:
                print(f"試合 {i+1}/{min(3, len(games_data))}: {game.get('away_team', game['teams']['away']['team']['name'])} @ {game.get('home_team', game['teams']['home']['team']['name'])}")
            except:
                print(f"試合 {i+1}/{min(3, len(games_data))}: 処理中...")
"""

# ファイルを保存
with open("scripts/discord_report_with_table_jp.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("KeyError修正完了！")