# K-BB%修正スクリプト
# このスクリプトを実行してmlb_complete_report_real.pyを修正します

import os

file_path = r"scripts\mlb_complete_report_real.py"

# ファイルを読み込む
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# k_bb_pctをk_bb_percentに置換
content = content.replace("'k_bb_pct'", "'k_bb_percent'")

# ファイルに書き戻す
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("修正完了: k_bb_pct → k_bb_percent")
print("修正箇所:")
print("- 100行目: pitcher_stats.get('k_bb_percent', 0.0)")
print("- 126行目: bullpen_data.get('k_bb_percent', 0.0)")