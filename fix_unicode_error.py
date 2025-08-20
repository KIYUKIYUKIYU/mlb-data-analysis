# Unicode文字（✓と✗）を通常の文字に変更
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    content = f.read()

# Unicode文字を置換
content = content.replace('\u2713', '[OK]')  # ✓ → [OK]
content = content.replace('\u2717', '[NG]')  # ✗ → [NG]

# ファイルを保存
with open("scripts/discord_report_with_table.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("Unicode文字を修正しました")