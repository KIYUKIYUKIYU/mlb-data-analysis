# 3試合制限を完全に解除
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    content = f.read()

# すべての min(3, を探して修正
import re

# パターン1: min(3, len(games_data))
content = re.sub(r'min\(3,\s*len\(games_data\)\)', 'len(games_data)', content)

# パターン2: range(min(3, ...))
content = re.sub(r'range\(min\(3,\s*len\(games[^)]*\)\)\)', 'range(len(games_data))', content)

# パターン3: [:3] のスライス制限
content = re.sub(r'games_data\[:3\]', 'games_data', content)

# パターン4: for i in range(3) のような固定数
# これは慎重に（誤って他の3を変更しないように）

# 変更箇所を確認
if 'min(3' in content:
    print("まだ min(3 が残っています！")
else:
    print("すべての3試合制限を解除しました！")

# ファイル保存
with open("scripts/discord_report_with_table.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("\n修正完了！")
print("全試合が処理されるようになりました")