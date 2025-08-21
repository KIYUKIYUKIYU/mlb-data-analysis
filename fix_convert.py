#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

def parse_report(file_path):
    """レポートをパースして試合データを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    games = []
    
    # 試合ごとに分割（試合タイトルで分割）
    game_pattern = r'\*\*([^*]+) @ ([^*]+)\*\*'
    matches = list(re.finditer(game_pattern, content))
    
    for i, match in enumerate(matches):
        away_team = match.group(1).strip()
        home_team = match.group(2).strip()
        
        # この試合のデータ範囲を特定
        start = match.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(content)
        
        game_section = content[start:end]
        
        # データを抽出
        game_data = {
            'away_team': away_team,
            'home_team': home_team,
            'away_data': {},
            'home_data': {}
        }
        
        # 時刻
        time_match = re.search(r'開始時刻: (\d+/\d+ \d+:\d+)', game_section)
        if time_match:
            game_data['time'] = time_match.group(1)
        
        # 各チームのデータを抽出（【チーム名】の後のデータ）
        # Away team
        away_pattern = f'【{away_team}】([^【]+)'
        away_match = re.search(away_pattern, game_section)
        if away_match:
            away_section = away_match.group(1)
            game_data['away_data'] = parse_team_data(away_section)
        
        # Home team  
        home_pattern = f'【{home_team}】([^=]+)'
        home_match = re.search(home_pattern, game_section)
        if home_match:
            home_section = home_match.group(1)
            game_data['home_data'] = parse_team_data(home_section)
        
        games.append(game_data)
        
        # デバッグ出力
        print(f"試合 {i+1}: {away_team} @ {home_team}")
        print(f"  Away先発: {game_data['away_data'].get('pitcher_name', '未定')}")
        print(f"  Home先発: {game_data['home_data'].get('pitcher_name', '未定')}")
    
    return games

def parse_team_data(section):
    """チームセクションからデータを抽出"""
    data = {}
    
    # 先発投手
    pitcher_match = re.search(r'\*\*先発\*\*[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)', section)
    if pitcher_match:
        data['pitcher_name'] = pitcher_match.group(1)
        data['pitcher_record'] = pitcher_match.group(2)
    elif '先発**: 未定' in section or '先発: 未定' in section:
        data['pitcher_name'] = '未定'
    
    # 各種統計
    patterns = {
        'ERA': r'ERA:\s*([\d.]+)',
        'FIP': r'FIP:\s*([\d.]+)',
        'xFIP': r'xFIP:\s*([\d.]+)',
        'WHIP': r'WHIP:\s*([\d.]+)',
        'AVG': r'AVG:\s*([\d.]+)',
        'OPS': r'OPS:\s*([\d.]+)',
        'wOBA': r'wOBA:\s*([\d.]+)',
        'xwOBA': r'xwOBA:\s*([\d.]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, section)
        if match:
            data[key] = match.group(1)
    
    return data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_convert.py <input.txt>")
        sys.exit(1)
    
    games = parse_report(sys.argv[1])
    print(f"\n合計 {len(games)} 試合を処理しました")