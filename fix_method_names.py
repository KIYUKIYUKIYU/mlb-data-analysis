# メソッド名を修正
file_path = "scripts/discord_report_with_table_jp.py"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# get_team_name_jp → get_team_name に修正
content = content.replace('get_team_name_jp', 'get_team_name')
content = content.replace('get_player_name_jp', 'get_player_name')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("メソッド名を修正しました")