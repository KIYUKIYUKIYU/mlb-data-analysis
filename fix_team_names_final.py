#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
discord_report_with_table_jp.pyの554-555行目を修正
"""

# ファイルを読み込み
with open("scripts/discord_report_with_table_jp.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 554行目と555行目を探して修正
new_lines = []
for i, line in enumerate(lines):
    if "'away_team': game['teams']['away']['team']['name']," in line:
        # 元の行を追加
        new_lines.append(line)
        # 次の行にインデントを合わせて変換を追加
        indent = " " * (len(line) - len(line.lstrip()))
        new_lines.append(f"{indent}'away_team': self.to_japanese_team(game['teams']['away']['team']['name']),\n")
        # 元の行をコメントアウト
        lines[i] = f"#{line}"
    elif "'home_team': game['teams']['home']['team']['name']," in line:
        # 元の行を追加
        new_lines.append(line)
        # 次の行にインデントを合わせて変換を追加
        indent = " " * (len(line) - len(line.lstrip()))
        new_lines.append(f"{indent}'home_team': self.to_japanese_team(game['teams']['home']['team']['name']),\n")
        # 元の行をコメントアウト
        lines[i] = f"#{line}"
    else:
        new_lines.append(line)

# より簡単な方法：直接置換
content = ''.join(lines)
content = content.replace(
    "'away_team': game['teams']['away']['team']['name'],",
    "'away_team': self.to_japanese_team(game['teams']['away']['team']['name']),"
)
content = content.replace(
    "'home_team': game['teams']['home']['team']['name'],",
    "'home_team': self.to_japanese_team(game['teams']['home']['team']['name']),"
)

# ファイルを保存
with open("scripts/discord_report_with_table_jp.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("修正完了！")
print("554-555行目でチーム名を日本語に変換するように修正しました")
print("\n実行コマンド:")
print("python -m scripts.discord_report_with_table_jp")