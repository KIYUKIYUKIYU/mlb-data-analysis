#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

# ファイルを読み込み
with open("daily_reports/MLB08月22日(金)レポート.txt", 'r', encoding='utf-8') as f:
    content = f.read()

# 最初の50文字を確認
print("最初の50文字:", content[:50])

# Athleticsの試合を探す
if "Athletics" in content:
    print("✓ Athleticsが見つかりました")
    
# 区切り線を探す
sections = re.split(r'={40,}', content)
print(f"セクション数: {len(sections)}")

# 最初の試合セクションを取得
for section in sections:
    if 'Athletics' in section:
        print("\n--- Athletics セクション ---")
        print(section[:500])  # 最初の500文字
        
        # チーム名を抽出
        team_match = re.search(r'\*\*([\w\s]+) @ ([\w\s]+)\*\*', section)
        if team_match:
            print(f"\nチーム: {team_match.group(1)} @ {team_match.group(2)}")
        
        # 先発投手を抽出
        pitcher_match = re.search(r'\*\*先発\*\*[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)', section)
        if pitcher_match:
            print(f"先発: {pitcher_match.group(1)} ({pitcher_match.group(2)})")
        break