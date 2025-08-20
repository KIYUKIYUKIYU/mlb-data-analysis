# 強制的に日本語化を適用
with open("scripts/discord_report_with_table_jp.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# format_game_for_discord メソッドを探して修正
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # home_team取得の直後に変換を追加
    if "home_team = game['teams']['home']['team'].get('name'" in line:
        new_lines.append("        home_team = self.to_japanese_team(home_team)\n")
    
    # away_team取得の直後に変換を追加
    elif "away_team = game['teams']['away']['team'].get('name'" in line:
        new_lines.append("        away_team = self.to_japanese_team(away_team)\n")
    
    # 投手名取得の直後に変換を追加
    elif "pitcher_name = game" in line and "get('fullName'" in line:
        new_lines.append("                pitcher_name = self.to_japanese_player(pitcher_name)\n")

# ファイルを保存
with open("scripts/discord_report_with_table_jp.py", 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("日本語化を強制適用しました！")
print("\n確認のため、最初の試合だけテスト実行してみてください：")
print("python -m scripts.discord_report_with_table_jp")