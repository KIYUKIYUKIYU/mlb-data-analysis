#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

# ファイル読み込み
with open("daily_reports/MLB08月22日(金)レポート.txt", 'r', encoding='utf-8') as f:
    content = f.read()

# Athleticsセクションを取得
sections = re.split(r'={40,}', content)
for section in sections:
    if 'Athletics' in section and '@' in section:
        print("=== Athletics試合セクション全体（最初の2000文字） ===\n")
        print(section[:2000])
        print("\n" + "="*60)
        
        # 行ごとに分析
        lines = section.strip().split('\n')
        print(f"\n総行数: {len(lines)}")
        print("\n--- 最初の30行 ---")
        for i, line in enumerate(lines[:30]):
            print(f"{i:3}: {line}")
        
        break