# チーム名日本語化を追加
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    content = f.read()

# インポート部分に辞書を追加
team_dict = '''
# チーム名日本語辞書
TEAM_NAMES_JP = {
    "Arizona Diamondbacks": "ダイヤモンドバックス",
    "Atlanta Braves": "ブレーブス",
    "Baltimore Orioles": "オリオールズ",
    "Boston Red Sox": "レッドソックス",
    "Chicago Cubs": "カブス",
    "Chicago White Sox": "ホワイトソックス",
    "Cincinnati Reds": "レッズ",
    "Cleveland Guardians": "ガーディアンズ",
    "Colorado Rockies": "ロッキーズ",
    "Detroit Tigers": "タイガース",
    "Houston Astros": "アストロズ",
    "Kansas City Royals": "ロイヤルズ",
    "Los Angeles Angels": "エンゼルス",
    "Los Angeles Dodgers": "ドジャース",
    "Miami Marlins": "マーリンズ",
    "Milwaukee Brewers": "ブルワーズ",
    "Minnesota Twins": "ツインズ",
    "New York Mets": "メッツ",
    "New York Yankees": "ヤンキース",
    "Oakland Athletics": "アスレチックス",
    "Philadelphia Phillies": "フィリーズ",
    "Pittsburgh Pirates": "パイレーツ",
    "San Diego Padres": "パドレス",
    "San Francisco Giants": "ジャイアンツ",
    "Seattle Mariners": "マリナーズ",
    "St. Louis Cardinals": "カージナルス",
    "Tampa Bay Rays": "レイズ",
    "Texas Rangers": "レンジャーズ",
    "Toronto Blue Jays": "ブルージェイズ",
    "Washington Nationals": "ナショナルズ"
}

def get_jp_team_name(team_name):
    return TEAM_NAMES_JP.get(team_name, team_name)
'''

# warningsの後に追加
import_pos = content.find('warnings.filterwarnings')
if import_pos != -1:
    end_line = content.find('\n', import_pos) + 1
    content = content[:end_line] + '\n' + team_dict + '\n' + content[end_line:]

# チーム名表示部分を変換（554-555行目付近）
content = content.replace(
    "'away_team': game['teams']['away']['team']['name'],",
    "'away_team': get_jp_team_name(game['teams']['away']['team']['name']),"
)
content = content.replace(
    "'home_team': game['teams']['home']['team']['name'],",
    "'home_team': get_jp_team_name(game['teams']['home']['team']['name']),"
)

# ファイル保存
with open("scripts/discord_report_with_table.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("チーム名日本語化を追加しました！")