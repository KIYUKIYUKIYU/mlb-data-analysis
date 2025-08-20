# fix_newline_v2.py

# ファイルを読み込み
with open("scripts/mlb_complete_report_real.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 修正後の内容
fixed_lines = []
for line in lines:
    # print文の中の \\n を実際の改行に修正
    if 'print(f"\\\\n{' in line:
        line = line.replace('print(f"\\\\n{', 'print(f"\\n{')
    elif 'print("\\\\n' in line:
        line = line.replace('print("\\\\n', 'print("\\n')
    elif "print(f'\\\\n{" in line:
        line = line.replace("print(f'\\\\n{", "print(f'\\n{")
    fixed_lines.append(line)

# 保存
with open("scripts/mlb_complete_report_real.py", "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("✅ 改行文字を修正しました")

# 確認
count = 0
for line in fixed_lines:
    if '\\\\n' in line and 'print' in line:
        count += 1
        if count < 5:  # 最初の5個だけ表示
            print(f"  残っている\\\\n: {line.strip()}")

if count == 0:
    print("✅ すべての改行文字が修正されました")
else:
    print(f"⚠️ まだ {count} 箇所の\\\\nが残っています")