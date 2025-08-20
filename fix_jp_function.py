# 関数定義エラーを修正
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    content = f.read()

# get_jp_team_nameの定義を確認
if "def get_jp_team_name" not in content:
    print("関数が定義されていません。修正します...")
    
    # TEAM_NAMES_JPの後に関数定義があるか確認
    if "TEAM_NAMES_JP" in content:
        # TEAM_NAMES_JPの定義の後に関数がない場合、追加
        team_dict_end = content.find("}\n", content.find("TEAM_NAMES_JP"))
        if team_dict_end != -1:
            insert_pos = team_dict_end + 2
            # インデントを修正（クラス内なのでインデントなし）
            content = content[:insert_pos] + "\ndef get_jp_team_name(team_name):\n    return TEAM_NAMES_JP.get(team_name, team_name)\n" + content[insert_pos:]
    else:
        print("TEAM_NAMES_JP辞書が見つかりません")

# 関数呼び出しをメソッド呼び出しに変更（より安全な方法）
content = content.replace(
    "'away_team': get_jp_team_name(game['teams']['away']['team']['name']),",
    "'away_team': TEAM_NAMES_JP.get(game['teams']['away']['team']['name'], game['teams']['away']['team']['name']),"
)
content = content.replace(
    "'home_team': get_jp_team_name(game['teams']['home']['team']['name']),",
    "'home_team': TEAM_NAMES_JP.get(game['teams']['home']['team']['name'], game['teams']['home']['team']['name']),"
)

# ファイル保存
with open("scripts/discord_report_with_table.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("修正完了！")
print("関数呼び出しを辞書の直接参照に変更しました")