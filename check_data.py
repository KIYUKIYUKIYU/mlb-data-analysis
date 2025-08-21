#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

# ファイル読み込み
with open("daily_reports/MLB08月22日(金)レポート.txt", 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 60)
print("データ抽出テスト")
print("=" * 60)

# Athleticsの部分を探す
start = content.find("Athletics @ Minnesota Twins")
if start != -1:
    # 次の試合まで（またはファイル終端まで）
    end = content.find("Texas Rangers @ Kansas City", start)
    if end == -1:
        end = start + 3000  # 3000文字分
    
    game_section = content[start:end]
    
    print("\n--- Athletics vs Twins セクション（最初の1500文字） ---")
    print(game_section[:1500])
    
    print("\n" + "=" * 60)
    print("パターンマッチテスト")
    print("=" * 60)
    
    # 各種パターンをテスト
    patterns = [
        ('【Athletics】', r'【Athletics】'),
        ('［Athletics］', r'［Athletics］'),
        ('Athletics（改行後）', r'\nAthletics\n'),
        ('先発:', r'先発[:：]'),
        ('ERA:', r'ERA[:：]\s*([\d.]+)'),
        ('AVG:', r'AVG[:：]\s*([\d.]+)'),
        ('OPS:', r'OPS[:：]\s*([\d.]+)'),
    ]
    
    for name, pattern in patterns:
        if re.search(pattern, game_section):
            print(f"✓ {name} が見つかりました")
            match = re.search(pattern, game_section)
            if match and match.groups():
                print(f"  値: {match.group(1)}")
        else:
            print(f"✗ {name} が見つかりません")