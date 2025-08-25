# デバッグ用スクリプト - test_pitcher.py として保存
with open('daily_reports/MLB08月22日(金)レポート.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    
# 最初の試合部分を取得
import re
game_pattern = r'\*\*([^*]+) @ ([^*]+)\*\*'
matches = list(re.finditer(game_pattern, content))

if matches:
    # 最初の試合のデータを表示
    start = matches[0].start()
    end = matches[1].start() if len(matches) > 1 else start + 2000
    
    game_section = content[start:end]
    
    # 先発投手に関する行を探す
    lines = game_section.split('\n')
    for i, line in enumerate(lines):
        if '先発' in line:
            print(f"Line {i}: {line}")
            # 前後の行も表示
            if i > 0:
                print(f"Line {i-1}: {lines[i-1]}")
            if i < len(lines) - 1:
                print(f"Line {i+1}: {lines[i+1]}")