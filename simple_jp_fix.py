# シンプルな日本語化修正
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 554-556行目付近を探して元に戻す
new_lines = []
for i, line in enumerate(lines):
    if "'away_team': TEAM_NAMES_JP.get" in line:
        # 元の形式に戻す
        new_lines.append("                    'away_team': game['teams']['away']['team']['name'],\n")
    elif "'home_team': TEAM_NAMES_JP.get" in line:
        # 元の形式に戻す
        new_lines.append("                    'home_team': game['teams']['home']['team']['name'],\n")
    else:
        new_lines.append(line)

# ファイル保存
with open("scripts/discord_report_with_table.py", 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("元の状態に戻しました！")
print("まずは英語版で動作確認しましょう")