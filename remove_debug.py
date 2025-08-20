# remove_debug.py

# ファイルを読み込み
with open("scripts/mlb_complete_report_real.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Debug行を削除
cleaned_lines = []
for line in lines:
    # Debug出力を含む行をスキップ
    if 'print(f"Debug' in line or 'print("Debug' in line:
        # 完全に削除（何も追加しない）
        continue
    cleaned_lines.append(line)

# 保存
with open("scripts/mlb_complete_report_real.py", "w", encoding="utf-8") as f:
    f.writelines(cleaned_lines)

print("✅ Debug出力を削除しました")

# 確認
debug_count = 0
for line in cleaned_lines:
    if 'Debug' in line and 'print' in line:
        debug_count += 1

if debug_count == 0:
    print("✅ すべてのDebug出力が削除されました")
else:
    print(f"⚠️ まだ {debug_count} 箇所のDebug出力が残っています")