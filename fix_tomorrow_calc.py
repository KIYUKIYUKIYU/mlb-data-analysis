# 531行目の日付計算を修正
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 531行目を修正
for i, line in enumerate(lines):
    if i == 530:  # 531行目（0から始まるので530）
        # 古い行をコメントアウト
        lines[i] = "        # " + line
        # 新しい計算を追加
        new_line = "        tomorrow_est = (now_jst - timedelta(hours=13)).date()  # 日本時間をアメリカ東部時間に変換\n"
        lines.insert(i + 1, new_line)
        break

# ファイルを保存
with open("scripts/discord_report_with_table.py", 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("日付計算を修正しました！")
print("修正内容：")
print("旧: tomorrow_est = (now_jst - timedelta(hours=13) + timedelta(days=1)).date()")
print("新: tomorrow_est = (now_jst - timedelta(hours=13)).date()")
print("\nこれで日本時間の今夜〜明日早朝の試合が表示されます")