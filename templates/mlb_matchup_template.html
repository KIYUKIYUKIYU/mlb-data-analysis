# 先発投手のGB%/FB%を追加
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    content = f.read()

# get_complete_pitcher_stats メソッドを探す
import re

# GB%/FB%の計算を追加（FIPの計算の後に追加）
gb_fb_calc = '''
            
            # GB%/FB%を計算
            gb_percent = 0.0
            fb_percent = 0.0
            balls_in_play = stats.get('groundOuts', 0) + stats.get('airOuts', 0) + stats.get('hits', 0) - stats.get('homeRuns', 0)
            
            if balls_in_play > 0:
                ground_balls = stats.get('groundOuts', 0) * 0.8  # 推定値
                fly_balls = stats.get('airOuts', 0) * 0.7  # 推定値
                gb_percent = round((ground_balls / balls_in_play) * 100, 1)
                fb_percent = round((fly_balls / balls_in_play) * 100, 1)
'''

# FIP計算の後に追加
fip_pattern = r'(fip = round\([^)]+\), 2\))'
replacement = r'\1' + gb_fb_calc

content = re.sub(fip_pattern, replacement, content)

# 返り値の辞書にGB%/FB%を追加
dict_pattern = r"('fip': fip,)"
dict_replacement = r"'fip': fip,\n                'gb_percent': gb_percent,\n                'fb_percent': fb_percent,"

content = re.sub(dict_pattern, dict_replacement, content)

# 表示部分を修正（ERA/FIP/WHIPの行の後にGB%/FB%を追加）
display_pattern = r'(ERA: {p\[\'era\'\]} \| FIP: {p\[\'fip\'\]} \| WHIP: {p\[\'whip\'\]} \| K-BB%: {p\[\'k_bb\'\]})'
display_replacement = r'\1 | GB%: {p[\'gb_percent\']}% | FB%: {p[\'fb_percent\']}%'

content = content.replace(
    "ERA: {p['era']} | FIP: {p['fip']} | WHIP: {p['whip']} | K-BB%: {p['k_bb']}",
    "ERA: {p['era']} | FIP: {p['fip']} | WHIP: {p['whip']} | K-BB%: {p['k_bb']} | GB%: {p.get('gb_percent', 'N/A')}% | FB%: {p.get('fb_percent', 'N/A')}%"
)

# ファイル保存
with open("scripts/discord_report_with_table.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("GB%/FB%を追加しました！")