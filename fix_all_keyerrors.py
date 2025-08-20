#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
すべてのaway_team/home_team参照を修正
"""

with open("scripts/discord_report_with_table_jp.py", 'r', encoding='utf-8') as f:
    content = f.read()

# すべての game_data['away_team'] を game_data.get('away_team', 'Unknown') に置換
import re

# パターン1: game_data['away_team']
content = re.sub(r"game_data\['away_team'\]", "game_data.get('away_team', 'Unknown')", content)

# パターン2: game_data['home_team']
content = re.sub(r"game_data\['home_team'\]", "game_data.get('home_team', 'Unknown')", content)

# パターン3: game['away_team']
content = re.sub(r"game\['away_team'\]", "game.get('away_team', 'Unknown')", content)

# パターン4: game['home_team']
content = re.sub(r"game\['home_team'\]", "game.get('home_team', 'Unknown')", content)

# ファイルを保存
with open("scripts/discord_report_with_table_jp.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("すべてのKeyError箇所を修正しました！")
print("修正内容:")
print("- game_data['away_team'] → game_data.get('away_team', 'Unknown')")
print("- game_data['home_team'] → game_data.get('home_team', 'Unknown')")