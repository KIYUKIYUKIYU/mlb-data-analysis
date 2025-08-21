#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from pathlib import Path

# ファイル読み込み
file_path = "daily_reports/MLB08月22日(金)レポート.txt"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 60)
print("デバッグ情報")
print("=" * 60)

# 1. ファイルサイズ
print(f"ファイルサイズ: {len(content)} 文字")

# 2. 試合セクションを分割
game_sections = re.split(r'={40,}', content)
print(f"セクション数: {len(game_sections)}")

# 3. Athleticsの試合を探す
for i, section in enumerate(game_sections):
    if 'Athletics' in section and '@' in section:
        print(f"\n--- セクション {i} (Athletics) ---")
        
        # チーム名抽出テスト
        patterns = [
            r'\*\*([\w\s]+) @ ([\w\s]+)\*\*',  # 現在のパターン
            r'\*\*(.+?) @ (.+?)\*\*',           # より緩いパターン
            r'([A-Za-z\s]+) @ ([A-Za-z\s]+)',   # アスタリスクなし
        ]
        
        for j, pattern in enumerate(patterns):
            match = re.search(pattern, section)
            if match:
                print(f"パターン{j+1}: {match.group(1)} @ {match.group(2)}")
        
        # チームセクション抽出
        team_sections = re.split(r'【(.+?)】', section)
        print(f"チームセクション数: {len(team_sections)}")
        if len(team_sections) > 1:
            print(f"チーム1: {team_sections[1] if len(team_sections) > 1 else 'なし'}")
            print(f"チーム2: {team_sections[3] if len(team_sections) > 3 else 'なし'}")
        
        # 先発投手抽出テスト
        pitcher_patterns = [
            r'\*\*先発\*\*[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)',
            r'先発[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)',
            r'\*\*先発\*\*[:：]\s*未定',
        ]
        
        for j, pattern in enumerate(pitcher_patterns):
            match = re.search(pattern, section)
            if match:
                if '未定' in pattern:
                    print(f"投手パターン{j+1}: 未定")
                else:
                    print(f"投手パターン{j+1}: {match.group(1)} ({match.group(2)})")
        
        # ERA行を探す
        era_match = re.search(r'ERA:\s*([\d.]+)', section)
        if era_match:
            print(f"ERA found: {era_match.group(1)}")
        
        break

print("\n" + "=" * 60)