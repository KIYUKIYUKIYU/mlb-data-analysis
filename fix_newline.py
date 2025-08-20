# fix_newline.py
import re

# ファイルを読み込み
with open("scripts/mlb_complete_report_real.py", "r", encoding="utf-8") as f:
    content = f.read()

# 問題のある print文を修正
# print(f"\\n{'='*60}") を print(f"\\n{'='*60}") に変更
patterns = [
    (r'print\\(f"\\\\n\\{', 'print(f"\\n{'),
    (r'print\\("\\\\n', 'print("\\n'),
]

for old, new in patterns:
    content = re.sub(old, new, content)

# 保存
with open("scripts/mlb_complete_report_real.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 改行文字を修正しました")