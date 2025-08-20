import re

# ファイルを確認
with open("scripts/discord_report_with_table_jp.py", 'r', encoding='utf-8') as f:
    content = f.read()

# format_game_for_discord内でto_japanese_teamが呼ばれているか確認
if "home_team = self.to_japanese_team(home_team)" in content:
    print("✓ home_teamの日本語変換あり")
else:
    print("✗ home_teamの日本語変換なし")
    # 変換を追加
    pattern = r"(home_team = game\['teams'\]\['home'\]\['team'\]\.get\('name', 'Unknown'\))"
    if re.search(pattern, content):
        content = re.sub(pattern, r"\1\n        home_team = self.to_japanese_team(home_team)", content)
        print("  → 修正を追加")

# away_teamも同様
if "away_team = self.to_japanese_team(away_team)" in content:
    print("✓ away_teamの日本語変換あり")
else:
    print("✗ away_teamの日本語変換なし")
    pattern = r"(away_team = game\['teams'\]\['away'\]\['team'\]\.get\('name', 'Unknown'\))"
    if re.search(pattern, content):
        content = re.sub(pattern, r"\1\n        away_team = self.to_japanese_team(away_team)", content)
        print("  → 修正を追加")

# ファイルを保存
with open("scripts/discord_report_with_table_jp.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("\n修正完了！")