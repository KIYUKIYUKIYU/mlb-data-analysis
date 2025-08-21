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
        print("=== Athleticsセクションの詳細 ===\n")
        
        # 最初の1000文字を表示
        print("--- 生データ（最初の1000文字） ---")
        print(repr(section[:1000]))
        print()
        
        # チーム名の周辺を探す
        lines = section.split('\n')
        for i, line in enumerate(lines):
            if 'Athletics' in line and not '@' in line:
                print(f"Line {i}: {repr(line)}")
                # 前後の行も表示
                if i > 0:
                    print(f"Line {i-1}: {repr(lines[i-1])}")
                if i < len(lines) - 1:
                    print(f"Line {i+1}: {repr(lines[i+1])}")
                break
        
        # 異なるパターンでチームセクションを探す
        print("\n--- チーム区切りパターンテスト ---")
        
        # パターン1: Athletics単独行
        if '\nAthletics\n' in section:
            print("✓ Athletics単独行あり")
        
        # パターン2: 何らかの括弧
        brackets = ['【', '［', '[', '〔', '｛']
        for bracket in brackets:
            if bracket in section:
                print(f"✓ {bracket} が見つかりました")
        
        # パターン3: 先発で区切る
        parts = section.split('**先発**')
        print(f"'**先発**'で分割: {len(parts)}個")
        
        break