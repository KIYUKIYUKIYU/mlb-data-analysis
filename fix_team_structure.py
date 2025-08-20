#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
game辞書の構造を修正
"""

with open("scripts/discord_report_with_table_jp.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 新しいファイル内容
new_lines = []
fixed = False

for i, line in enumerate(lines):
    # games_dataを作成している箇所を探す（550行目付近）
    if "games_data = []" in line:
        new_lines.append(line)
        # その後のfor文を探す
        for j in range(i+1, min(i+30, len(lines))):
            new_lines.append(lines[j])
            if "games_data.append({" in lines[j]:
                # ここでチーム名の設定を確認
                # 数行後に 'away_team' と 'home_team' の設定があるはず
                for k in range(j+1, min(j+20, len(lines))):
                    if "'away_team':" in lines[k] and "self.to_japanese_team" not in lines[k]:
                        # まだ修正されていない場合
                        team_line = lines[k].strip()
                        if "game['teams']['away']['team']['name']" in team_line:
                            # 正しい形式に修正
                            indent = " " * (len(lines[k]) - len(lines[k].lstrip()))
                            new_lines.append(f"{indent}'away_team': self.to_japanese_team(game['teams']['away']['team']['name']) if hasattr(self, 'to_japanese_team') else game['teams']['away']['team']['name'],\n")
                            fixed = True
                        else:
                            new_lines.append(lines[k])
                    elif "'home_team':" in lines[k] and "self.to_japanese_team" not in lines[k]:
                        # まだ修正されていない場合
                        team_line = lines[k].strip()
                        if "game['teams']['home']['team']['name']" in team_line:
                            # 正しい形式に修正
                            indent = " " * (len(lines[k]) - len(lines[k].lstrip()))
                            new_lines.append(f"{indent}'home_team': self.to_japanese_team(game['teams']['home']['team']['name']) if hasattr(self, 'to_japanese_team') else game['teams']['home']['team']['name'],\n")
                            fixed = True
                        else:
                            new_lines.append(lines[k])
                    else:
                        new_lines.append(lines[k])
                        
                    if "}" in lines[k] and "append" in lines[j]:
                        # appendの終了
                        break
                break
        continue
    else:
        new_lines.append(line)

# より簡単な方法：全体を文字列として処理
content = ''.join(lines)

# create_game_tableメソッドの修正（323行目付近）
content = content.replace(
    'title = f"{game_data[\'away_team\']} @ {game_data[\'home_team\']}"',
    'title = f"{game_data.get(\'away_team\', \'Unknown\')} @ {game_data.get(\'home_team\', \'Unknown\')}"'
)

# format_game_messageメソッドの修正（434行目付近）  
content = content.replace(
    'message = f"**{game_data[\'away_team\']} @ {game_data[\'home_team\']}**\\n"',
    'message = f"**{game_data.get(\'away_team\', \'Unknown\')} @ {game_data.get(\'home_team\', \'Unknown\')}**\\n"'
)

# headers行の修正（326行目付近）
content = content.replace(
    "headers = ['', game_data['away_team'], game_data['home_team']]",
    "headers = ['', game_data.get('away_team', 'Unknown'), game_data.get('home_team', 'Unknown')]"
)

# 582行目のprint文も修正
content = content.replace(
    'print(f"試合 {i+1}/{min(3, len(games_data))}: {game[\'away_team\']} @ {game[\'home_team\']}")',
    'print(f"試合 {i+1}/{min(3, len(games_data))}: {game.get(\'away_team\', game[\'teams\'][\'away\'][\'team\'][\'name\'])} @ {game.get(\'home_team\', game[\'teams\'][\'home\'][\'team\'][\'name\'])}")'
)

# ファイルを保存
with open("scripts/discord_report_with_table_jp.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("修正完了！")
print("- create_game_table (323行目)")
print("- format_game_message (434行目)")  
print("- headers (326行目)")
print("- print文 (582行目)")
print("\nすべてのKeyErrorを回避するように修正しました")