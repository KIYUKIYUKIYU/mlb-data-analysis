#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
投手情報を取得してキャッシュ
"""

import re
from pathlib import Path

# まずレポートから投手名を抽出してみる
report_path = Path("daily_reports/MLB08月22日(金)レポート.txt")

if not report_path.exists():
    print(f"ファイルが見つかりません: {report_path}")
    # 他のレポートを探す
    reports = list(Path("daily_reports").glob("MLB*.txt"))
    if reports:
        report_path = reports[0]
        print(f"代わりに使用: {report_path}")
    else:
        print("レポートが見つかりません")
        exit()

with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"ファイル: {report_path}")
print("=" * 50)

# 先発を含む行を探す
lines = content.split('\n')
pitcher_lines = []

for i, line in enumerate(lines):
    if '先発' in line:
        print(f"Line {i+1}: {line}")
        pitcher_lines.append(line)
        
        # 前後の行も表示
        if i > 0:
            print(f"  前の行: {lines[i-1][:50]}")
        if i < len(lines) - 1:
            print(f"  次の行: {lines[i+1][:50]}")
        print()

print(f"\n先発を含む行: {len(pitcher_lines)}個")

# パターンマッチングを試す
patterns = [
    r'\*\*先発\*\*[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)',
    r'先発[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)',
    r'\*\*先発\*\*[:：]\s*([^(]+)',
    r'先発[:：]\s*([^(]+)',
]

for pattern_num, pattern in enumerate(patterns, 1):
    print(f"\nパターン{pattern_num}: {pattern}")
    matches = re.findall(pattern, content)
    if matches:
        print(f"  マッチ数: {len(matches)}")
        for match in matches[:5]:  # 最初の5個だけ表示
            print(f"    - {match}")