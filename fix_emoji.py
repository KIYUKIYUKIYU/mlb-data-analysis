# fix_emoji.py

# ファイルを読み込み
with open("scripts/mlb_complete_report_real.py", "r", encoding="utf-8") as f:
    content = f.read()

# 絵文字を通常の文字に置換
replacements = [
    ('✅ データ信頼性: 高', '[高] データ信頼性: 高'),
    ('🟡 データ信頼性: 中', '[中] データ信頼性: 中'),
    ('🔴 データ信頼性: 要確認', '[低] データ信頼性: 要確認'),
    ('🟢', '[新]'),
    ('🟡', '[今日]'),
    ('🔴', '[古]'),
    ('✅', '[OK]'),
]

for old, new in replacements:
    content = content.replace(old, new)

# 保存
with open("scripts/mlb_complete_report_real.py", "w", encoding="utf-8") as f:
    f.write(content)

print("絵文字を削除しました")