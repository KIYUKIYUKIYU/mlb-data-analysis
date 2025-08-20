# fix_all_newlines.py

# ファイルを読み込み
with open("scripts/mlb_complete_report_real.py", "r", encoding="utf-8") as f:
    content = f.read()

# すべての print文内の \\\\n を \\n に置換
replacements = [
    ('print(f"\\\\n', 'print(f"\\n'),
    ("print(f'\\\\n", "print(f'\\n"),
    ('print("\\\\n', 'print("\\n'),
    ("print('\\\\n", "print('\\n"),
]

for old, new in replacements:
    content = content.replace(old, new)

# 保存
with open("scripts/mlb_complete_report_real.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ すべての改行文字を修正しました")

# 確認
lines = content.split('\\n')
remaining = []
for i, line in enumerate(lines):
    if '\\\\n' in line and 'print' in line:
        remaining.append(f"Line {i+1}: {line.strip()}")

if remaining:
    print(f"⚠️ まだ {len(remaining)} 箇所の\\\\nが残っています:")
    for r in remaining[:5]:
        print(f"  {r}")
else:
    print("✅ すべての\\\\nが正常に修正されました")