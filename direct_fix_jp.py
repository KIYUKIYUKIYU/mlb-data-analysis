#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
games_data作成部分を直接修正
"""

with open("scripts/discord_report_with_table_jp.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 550行目付近のgames_data作成部分を探して修正
new_lines = []
in_append_section = False

for i, line in enumerate(lines):
    # games_data.append({ を探す
    if "games_data.append({" in line:
        new_lines.append(line)
        in_append_section = True
        continue
    
    # append内でaway_team/home_teamの行を修正
    if in_append_section:
        if "'away_team':" in line and "self.to_japanese_team" not in line:
            # インデントを保持
            indent = line[:len(line) - len(line.lstrip())]
            # チーム名を直接取得して変換
            new_lines.append(f"{indent}'away_team': self.to_japanese_team(game['teams']['away']['team']['name']) if hasattr(self, 'to_japanese_team') else game['teams']['away']['team']['name'],\n")
        elif "'home_team':" in line and "self.to_japanese_team" not in line:
            # インデントを保持
            indent = line[:len(line) - len(line.lstrip())]
            # チーム名を直接取得して変換
            new_lines.append(f"{indent}'home_team': self.to_japanese_team(game['teams']['home']['team']['name']) if hasattr(self, 'to_japanese_team') else game['teams']['home']['team']['name'],\n")
        else:
            new_lines.append(line)
            
        # append終了を検出
        if "})" in line:
            in_append_section = False
    else:
        new_lines.append(line)

# ファイルを保存
with open("scripts/discord_report_with_table_jp_fixed.py", 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("新しいファイルを作成: discord_report_with_table_jp_fixed.py")
print("\n実行:")
print("python -m scripts.discord_report_with_table_jp_fixed")