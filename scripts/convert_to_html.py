#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBレポートをHTMLに変換するスクリプト（1ページ最適配置版）
- 空白を適切に配分
- コンテンツを垂直方向に均等配置
"""

import re
import os
from pathlib import Path
from datetime import datetime

# チーム名とロゴのマッピング（既存のまま）
TEAM_LOGOS = {
    'Blue Jays': 'https://a.espncdn.com/i/teamlogos/mlb/500/tor.png',
    'Toronto Blue Jays': 'https://a.espncdn.com/i/teamlogos/mlb/500/tor.png',
    'Pirates': 'https://a.espncdn.com/i/teamlogos/mlb/500/pit.png',
    'Pittsburgh Pirates': 'https://a.espncdn.com/i/teamlogos/mlb/500/pit.png',
    'Mariners': 'https://a.espncdn.com/i/teamlogos/mlb/500/sea.png',
    'Seattle Mariners': 'https://a.espncdn.com/i/teamlogos/mlb/500/sea.png',
    'Phillies': 'https://a.espncdn.com/i/teamlogos/mlb/500/phi.png',
    'Philadelphia Phillies': 'https://a.espncdn.com/i/teamlogos/mlb/500/phi.png',
    'Astros': 'https://a.espncdn.com/i/teamlogos/mlb/500/hou.png',
    'Houston Astros': 'https://a.espncdn.com/i/teamlogos/mlb/500/hou.png',
    'Tigers': 'https://a.espncdn.com/i/teamlogos/mlb/500/det.png',
    'Detroit Tigers': 'https://a.espncdn.com/i/teamlogos/mlb/500/det.png',
    'Guardians': 'https://a.espncdn.com/i/teamlogos/mlb/500/cle.png',
    'Cleveland Guardians': 'https://a.espncdn.com/i/teamlogos/mlb/500/cle.png',
    'Diamondbacks': 'https://a.espncdn.com/i/teamlogos/mlb/500/ari.png',
    'Arizona Diamondbacks': 'https://a.espncdn.com/i/teamlogos/mlb/500/ari.png',
    'Cardinals': 'https://a.espncdn.com/i/teamlogos/mlb/500/stl.png',
    'St. Louis Cardinals': 'https://a.espncdn.com/i/teamlogos/mlb/500/stl.png',
    'Marlins': 'https://a.espncdn.com/i/teamlogos/mlb/500/mia.png',
    'Miami Marlins': 'https://a.espncdn.com/i/teamlogos/mlb/500/mia.png',
    'Mets': 'https://a.espncdn.com/i/teamlogos/mlb/500/nym.png',
    'New York Mets': 'https://a.espncdn.com/i/teamlogos/mlb/500/nym.png',
    'Nationals': 'https://a.espncdn.com/i/teamlogos/mlb/500/wsh.png',
    'Washington Nationals': 'https://a.espncdn.com/i/teamlogos/mlb/500/wsh.png',
    'White Sox': 'https://a.espncdn.com/i/teamlogos/mlb/500/cws.png',
    'Chicago White Sox': 'https://a.espncdn.com/i/teamlogos/mlb/500/cws.png',
    'Braves': 'https://a.espncdn.com/i/teamlogos/mlb/500/atl.png',
    'Atlanta Braves': 'https://a.espncdn.com/i/teamlogos/mlb/500/atl.png',
    'Yankees': 'https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png',
    'New York Yankees': 'https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png',
    'Rays': 'https://a.espncdn.com/i/teamlogos/mlb/500/tb.png',
    'Tampa Bay Rays': 'https://a.espncdn.com/i/teamlogos/mlb/500/tb.png',
    'Rangers': 'https://a.espncdn.com/i/teamlogos/mlb/500/tex.png',
    'Texas Rangers': 'https://a.espncdn.com/i/teamlogos/mlb/500/tex.png',
    'Royals': 'https://a.espncdn.com/i/teamlogos/mlb/500/kc.png',
    'Kansas City Royals': 'https://a.espncdn.com/i/teamlogos/mlb/500/kc.png',
    'Athletics': 'https://a.espncdn.com/i/teamlogos/mlb/500/oak.png',
    'Oakland Athletics': 'https://a.espncdn.com/i/teamlogos/mlb/500/oak.png',
    'Twins': 'https://a.espncdn.com/i/teamlogos/mlb/500/min.png',
    'Minnesota Twins': 'https://a.espncdn.com/i/teamlogos/mlb/500/min.png',
    'Brewers': 'https://a.espncdn.com/i/teamlogos/mlb/500/mil.png',
    'Milwaukee Brewers': 'https://a.espncdn.com/i/teamlogos/mlb/500/mil.png',
    'Cubs': 'https://a.espncdn.com/i/teamlogos/mlb/500/chc.png',
    'Chicago Cubs': 'https://a.espncdn.com/i/teamlogos/mlb/500/chc.png',
    'Dodgers': 'https://a.espncdn.com/i/teamlogos/mlb/500/lad.png',
    'Los Angeles Dodgers': 'https://a.espncdn.com/i/teamlogos/mlb/500/lad.png',
    'Rockies': 'https://a.espncdn.com/i/teamlogos/mlb/500/col.png',
    'Colorado Rockies': 'https://a.espncdn.com/i/teamlogos/mlb/500/col.png',
    'Reds': 'https://a.espncdn.com/i/teamlogos/mlb/500/cin.png',
    'Cincinnati Reds': 'https://a.espncdn.com/i/teamlogos/mlb/500/cin.png',
    'Angels': 'https://a.espncdn.com/i/teamlogos/mlb/500/ana.png',
    'Los Angeles Angels': 'https://a.espncdn.com/i/teamlogos/mlb/500/ana.png',
    'Giants': 'https://a.espncdn.com/i/teamlogos/mlb/500/sf.png',
    'San Francisco Giants': 'https://a.espncdn.com/i/teamlogos/mlb/500/sf.png',
    'Padres': 'https://a.espncdn.com/i/teamlogos/mlb/500/sd.png',
    'San Diego Padres': 'https://a.espncdn.com/i/teamlogos/mlb/500/sd.png',
    'Red Sox': 'https://a.espncdn.com/i/teamlogos/mlb/500/bos.png',
    'Boston Red Sox': 'https://a.espncdn.com/i/teamlogos/mlb/500/bos.png',
    'Orioles': 'https://a.espncdn.com/i/teamlogos/mlb/500/bal.png',
    'Baltimore Orioles': 'https://a.espncdn.com/i/teamlogos/mlb/500/bal.png',
}

def get_team_logo(team_name):
    """チーム名からロゴURLを取得"""
    return TEAM_LOGOS.get(team_name, 'https://a.espncdn.com/i/teamlogos/mlb/500/mlb.png')

def parse_report(file_path):
    """レポートをパースして試合データを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sections = content.split('=' * 60)
    games = []
    
    for i in range(len(sections)):
        section = sections[i]
        
        match = re.search(r'([A-Za-z\s.]+?)\s*@\s*([A-Za-z\s.]+)', section)
        if not match:
            continue
        
        away_team = match.group(1).strip()
        home_team = match.group(2).strip()
        
        time_match = re.search(r'開始時刻:\s*(\d+/\d+\s+\d+:\d+)', section)
        start_time = time_match.group(1) if time_match else ''
        
        game_content = section
        if i + 1 < len(sections):
            next_section = sections[i + 1]
            if not re.search(r'([A-Za-z\s.]+?)\s*@\s*([A-Za-z\s.]+)', next_section):
                game_content += next_section
        
        away_data = parse_team_data(game_content, away_team, is_away=True)
        home_data = parse_team_data(game_content, home_team, is_away=False)
        
        game_data = {
            'away_team': away_team,
            'home_team': home_team,
            'start_time': start_time,
            'away_data': away_data,
            'home_data': home_data
        }
        
        games.append(game_data)
    
    return games

def parse_team_data(content, team_name, is_away):
    """チームデータをパース（既存のまま）"""
    data = {
        'team': team_name,
        'pitcher': {},
        'bullpen': {},
        'batting': {},
        'stats': {}
    }
    
    team_sections = re.split(r'【(.+?)】', content)
    
    for j in range(1, len(team_sections), 2):
        if j >= len(team_sections):
            break
        
        section_team = team_sections[j]
        section_content = team_sections[j+1] if j+1 < len(team_sections) else ""
        
        if team_name not in section_team and section_team not in team_name:
            continue
        
        # 先発投手情報
        pitcher_match = re.search(r'先発:\s*(.+?)\s*(?:\(([左右両])\))?\s*\((\d+)勝(\d+)敗\)', section_content)
        if pitcher_match:
            data['pitcher'] = {
                'name': pitcher_match.group(1),
                'hand': pitcher_match.group(2) if pitcher_match.group(2) else '',
                'wins': pitcher_match.group(3),
                'losses': pitcher_match.group(4)
            }
            data['stats']['sp_name'] = pitcher_match.group(1)
        else:
            if '先発' in section_content and '未定' in section_content:
                data['pitcher'] = {'name': '未定', 'hand': '', 'wins': '0', 'losses': '0'}
                data['stats']['sp_name'] = '未定'
        
        # 投手統計
        stats_patterns = {
            'era': r'ERA:\s*([\d.]+)',
            'fip': r'FIP:\s*([\d.]+)',
            'xfip': r'xFIP:\s*([\d.]+)',
            'whip': r'WHIP:\s*([\d.]+)',
            'k_bb': r'K-BB%:\s*([\d.]+)%',
            'gb': r'GB%:\s*([\d.]+)%',
            'fb': r'FB%:\s*([\d.]+)%',
            'qs': r'QS率:\s*([\d.]+)%',
            'swstr': r'SwStr%:\s*([\d.]+)%',
            'babip': r'BABIP:\s*([\d.]+)'
        }
        
        for key, pattern in stats_patterns.items():
            match = re.search(pattern, section_content)
            if match:
                data['pitcher'][key] = match.group(1)
                if key == 'xfip':
                    data['stats']['sp_xfip'] = float(match.group(1))
        
        # 対左右成績
        vs_patterns = {
            'vs_left': r'対左:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)',
            'vs_right': r'対右:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)'
        }
        
        for key, pattern in vs_patterns.items():
            match = re.search(pattern, section_content)
            if match:
                data['pitcher'][f'{key}_avg'] = match.group(1)
                data['pitcher'][f'{key}_ops'] = match.group(2)
        
        # 中継ぎ陣情報
        bullpen_count = re.search(r'中継ぎ陣\s*\((\d+)名\)', section_content)
        if bullpen_count:
            data['bullpen']['count'] = bullpen_count.group(1)
        
        bullpen_stats = {
            'era': r'中継ぎ陣.*?ERA:\s*([\d.]+)',
            'fip': r'中継ぎ陣.*?FIP:\s*([\d.]+)',
            'xfip': r'中継ぎ陣.*?xFIP:\s*([\d.]+)',
            'whip': r'中継ぎ陣.*?WHIP:\s*([\d.]+)',
            'k_bb': r'中継ぎ陣.*?K-BB%:\s*([\d.]+)%'
        }
        
        for key, pattern in bullpen_stats.items():
            match = re.search(pattern, section_content, re.DOTALL)
            if match:
                data['bullpen'][key] = match.group(1)
                if key == 'fip':
                    data['stats']['bp_fip'] = float(match.group(1))
        
        # クローザー・セットアップ
        closer_match = re.search(r'CL:\s*(.+?)(?:\(FIP:\s*([\d.]+)\))?', section_content)
        if closer_match:
            data['bullpen']['closer'] = closer_match.group(1).strip()
            if closer_match.group(2):
                data['bullpen']['closer_fip'] = closer_match.group(2)
        
        setup_match = re.search(r'SU:\s*(.+?)(?:\n|疲労度|$)', section_content)
        if setup_match:
            data['bullpen']['setup'] = setup_match.group(1).strip()
        
        # 疲労度
        fatigue_match = re.search(r'疲労度:\s*(.+?)(?:\n|$)', section_content)
        if fatigue_match:
            data['bullpen']['fatigue'] = fatigue_match.group(1).strip()
        
        # チーム打撃
        batting_patterns = {
            'avg': r'AVG:\s*([\d.]+)',
            'runs': r'得点:\s*(\d+)',
            'hr': r'本塁打:\s*(\d+)',
            'woba': r'wOBA:\s*([\d.]+)',
            'xwoba': r'xwOBA:\s*([\d.]+)',
            'barrel': r'Barrel%:\s*([\d.]+)%',
            'hardhit': r'Hard-Hit%:\s*([\d.]+)%'
        }
        
        ops_match = re.search(r'AVG:\s*[\d.]+.*?\|\s*OPS:\s*([\d.]+)', section_content)
        if ops_match:
            data['batting']['ops'] = ops_match.group(1)
        
        for key, pattern in batting_patterns.items():
            match = re.search(pattern, section_content)
            if match:
                data['batting'][key] = match.group(1)
        
        # 対左右投手
        vs_pitcher_patterns = {
            'vs_left': r'対左投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)',
            'vs_right': r'対右投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)'
        }
        
        for key, pattern in vs_pitcher_patterns.items():
            match = re.search(pattern, section_content)
            if match:
                data['batting'][f'{key}_avg'] = match.group(1)
                data['batting'][f'{key}_ops'] = match.group(2)
        
        # 過去試合OPS
        recent_match = re.search(r'過去5試合OPS:\s*([\d.]+).*?過去10試合OPS:\s*([\d.]+)', section_content)
        if recent_match:
            data['batting']['ops_5'] = recent_match.group(1)
            data['batting']['ops_10'] = recent_match.group(2)
            data['stats']['bat_ops_10g'] = float(recent_match.group(2))
        
        break
    
    data['stats'].setdefault('sp_xfip', 99)
    data['stats'].setdefault('bp_fip', 99)
    data['stats'].setdefault('bat_ops_10g', 0)
    
    return data

def generate_summary(away_data, home_data):
    """詳細な総括を生成（既存のまま）"""
    away_stats = away_data.get('stats', {})
    home_stats = home_data.get('stats', {})
    away_name = away_data['team']
    home_name = home_data['team']
    
    if not away_stats or not home_stats or away_stats.get('sp_name') == '未定' or home_stats.get('sp_name') == '未定':
        return "先発投手が未定またはデータが不足しているため、詳細な予想は困難です。"
    
    away_sp_xfip = away_stats.get('sp_xfip', 99)
    home_sp_xfip = home_stats.get('sp_xfip', 99)
    away_bp_fip = away_stats.get('bp_fip', 99)
    home_bp_fip = home_stats.get('bp_fip', 99)
    away_ops_10g = away_stats.get('bat_ops_10g', 0)
    home_ops_10g = home_stats.get('bat_ops_10g', 0)
    
    score = 0
    factors = []
    
    if abs(away_sp_xfip - home_sp_xfip) > 0.5:
        if away_sp_xfip < home_sp_xfip:
            score += 1.5
            factors.append(f"先発投手で{away_name}が優位（xFIP {away_sp_xfip:.2f} vs {home_sp_xfip:.2f}）")
        else:
            score -= 1.5
            factors.append(f"先発投手で{home_name}が優位（xFIP {home_sp_xfip:.2f} vs {away_sp_xfip:.2f}）")
    
    if abs(away_bp_fip - home_bp_fip) > 0.3:
        if away_bp_fip < home_bp_fip:
            score += 1
            factors.append(f"ブルペンで{away_name}が優勢（FIP {away_bp_fip:.2f} vs {home_bp_fip:.2f}）")
        else:
            score -= 1
            factors.append(f"ブルペンで{home_name}が優勢（FIP {home_bp_fip:.2f} vs {away_bp_fip:.2f}）")
    
    if abs(away_ops_10g - home_ops_10g) > 0.05:
        if away_ops_10g > home_ops_10g:
            score += 1.2
            factors.append(f"直近10試合の打線は{away_name}が好調（OPS {away_ops_10g:.3f} vs {home_ops_10g:.3f}）")
        else:
            score -= 1.2
            factors.append(f"直近10試合の打線は{home_name}が好調（OPS {home_ops_10g:.3f} vs {away_ops_10g:.3f}）")
    
    if score > 1.0:
        conclusion = f"総合的に{away_name}が有利と予想されます。"
    elif score < -1.0:
        conclusion = f"総合的に{home_name}が有利と予想されます。"
    else:
        conclusion = f"両チームが拮抗しており、接戦が予想されます。ホームアドバンテージを考慮すると、わずかに{home_name}が有利かもしれません。"
    
    if factors:
        return "。".join(factors) + "。" + conclusion
    else:
        return conclusion

def create_game_page(game_data):
    """1試合分のHTMLページを生成（空白最適化版）"""
    away_team = game_data['away_team']
    home_team = game_data['home_team']
    away_data = game_data['away_data']
    home_data = game_data['home_data']
    start_time = game_data.get('start_time', '未定')
    
    def get_hand_badge(hand):
        if hand == '右':
            return '<span class="handedness-rhp">右</span>'
        elif hand == '左':
            return '<span class="handedness-lhp">左</span>'
        else:
            return ''
    
    away_pitcher = away_data.get('pitcher', {})
    home_pitcher = home_data.get('pitcher', {})
    
    away_pitcher_html = ''
    home_pitcher_html = ''
    
    if away_pitcher.get('name') == '未定' or not away_pitcher.get('name'):
        away_pitcher_html = '<div class="no-sp mt-2">先発投手 未定</div>'
    else:
        away_pitcher_html = f'''
            <p class="text-lg font-bold">{away_pitcher.get('name', '未定')} {get_hand_badge(away_pitcher.get('hand', ''))}</p>
            <p class="text-gray-600 data-font">{away_pitcher.get('wins', '0')}勝{away_pitcher.get('losses', '0')}敗</p>
        '''
    
    if home_pitcher.get('name') == '未定' or not home_pitcher.get('name'):
        home_pitcher_html = '<div class="no-sp mt-2">先発投手 未定</div>'
    else:
        home_pitcher_html = f'''
            <p class="text-lg font-bold">{home_pitcher.get('name', '未定')} {get_hand_badge(home_pitcher.get('hand', ''))}</p>
            <p class="text-gray-600 data-font">{home_pitcher.get('wins', '0')}勝{home_pitcher.get('losses', '0')}敗</p>
        '''
    
    summary = generate_summary(away_data, home_data)
    
    away_vs_type = "vs RHP" if home_pitcher.get('hand') == '右' else "vs LHP" if home_pitcher.get('hand') == '左' else "攻撃"
    home_vs_type = "vs RHP" if away_pitcher.get('hand') == '右' else "vs LHP" if away_pitcher.get('hand') == '左' else "攻撃"
    
    away_ops_10 = float(away_data.get('batting', {}).get('ops_10', '0') or '0')
    home_ops_10 = float(home_data.get('batting', {}).get('ops_10', '0') or '0')
    
    away_ops_class = "text-red-600 font-bold" if away_ops_10 > home_ops_10 else "text-blue-600"
    home_ops_class = "text-red-600 font-bold" if home_ops_10 > away_ops_10 else "text-blue-600"
    
    html = f'''
    <div class="game-page">
        <header class="flex justify-between items-center pb-3 border-b-2 border-gray-400">
            <div class="team-info text-center w-1/3">
                <img src="{get_team_logo(away_team)}" alt="{away_team} Logo" class="w-14 h-14 mx-auto mb-2">
                <h1 class="text-2xl font-black">{away_team}</h1>
                {away_pitcher_html}
            </div>
            <div class="game-time text-center w-1/3">
                <p class="text-sm text-gray-500 mb-1">日本時間</p>
                <p class="text-4xl font-bold">{start_time}</p>
                <p class="text-base font-bold mt-1">試合開始</p>
            </div>
            <div class="team-info text-center w-1/3">
                <img src="{get_team_logo(home_team)}" alt="{home_team} Logo" class="w-14 h-14 mx-auto mb-2">
                <h1 class="text-2xl font-black">{home_team}</h1>
                {home_pitcher_html}
            </div>
        </header>
        <main class="flex-grow mt-4 grid grid-cols-2 gap-6">
            <div class="team-stats">
                <section class="mb-4">
                    <h2 class="section-title">先発投手: {away_pitcher.get('name', '未定')}</h2>
                    <div class="stat-item"><span class="label">ERA/FIP/xFIP</span><span class="value data-font">{away_pitcher.get('era', '---')}/{away_pitcher.get('fip', '---')}/{away_pitcher.get('xfip', '---')}</span></div>
                    <div class="stat-item"><span class="label">WHIP/K-BB%</span><span class="value data-font">{away_pitcher.get('whip', '---')}/{away_pitcher.get('k_bb', '---')}%</span></div>
                    <div class="stat-item"><span class="label">QS率/GB%</span><span class="value data-font">{away_pitcher.get('qs', '---')}%/{away_pitcher.get('gb', '---')}%</span></div>
                    <div class="stat-item"><span class="label">SwStr%/BABIP</span><span class="value data-font">{away_pitcher.get('swstr', '---')}%/{away_pitcher.get('babip', '---')}</span></div>
                    <div class="stat-item"><span class="label">対左/右 OPS</span><span class="value data-font">{away_pitcher.get('vs_left_ops', '---')}/{away_pitcher.get('vs_right_ops', '---')}</span></div>
                </section>
                <section class="mb-4">
                    <h2 class="section-title">中継ぎ陣 ({away_data.get('bullpen', {}).get('count', '?')}名)</h2>
                    <div class="stat-item"><span class="label">ERA/FIP/xFIP</span><span class="value data-font">{away_data.get('bullpen', {}).get('era', '---')}/{away_data.get('bullpen', {}).get('fip', '---')}/{away_data.get('bullpen', {}).get('xfip', '---')}</span></div>
                    <div class="stat-item"><span class="label">CL FIP</span><span class="value data-font">{away_data.get('bullpen', {}).get('closer_fip', '---')} ({away_data.get('bullpen', {}).get('closer', '---')})</span></div>
                    <div class="stat-item"><span class="label">疲労度</span><span class="value">{away_data.get('bullpen', {}).get('fatigue', '---')}</span></div>
                </section>
                <section>
                    <h2 class="section-title">攻撃 ({away_vs_type})</h2>
                    <div class="stat-item"><span class="label">AVG/OPS</span><span class="value data-font">{away_data.get('batting', {}).get('avg', '---')}/{away_data.get('batting', {}).get('ops', '---')}</span></div>
                    <div class="stat-item"><span class="label">wOBA/xwOBA</span><span class="value data-font">{away_data.get('batting', {}).get('woba', '---')}/{away_data.get('batting', {}).get('xwoba', '---')}</span></div>
                    <div class="stat-item"><span class="label">過去10試合 OPS</span><span class="value data-font {away_ops_class}">{away_data.get('batting', {}).get('ops_10', '---')}</span></div>
                </section>
            </div>
            <div class="team-stats">
                <section class="mb-4">
                    <h2 class="section-title">先発投手: {home_pitcher.get('name', '未定')}</h2>
                    <div class="stat-item"><span class="label">ERA/FIP/xFIP</span><span class="value data-font">{home_pitcher.get('era', '---')}/{home_pitcher.get('fip', '---')}/{home_pitcher.get('xfip', '---')}</span></div>
                    <div class="stat-item"><span class="label">WHIP/K-BB%</span><span class="value data-font">{home_pitcher.get('whip', '---')}/{home_pitcher.get('k_bb', '---')}%</span></div>
                    <div class="stat-item"><span class="label">QS率/GB%</span><span class="value data-font">{home_pitcher.get('qs', '---')}%/{home_pitcher.get('gb', '---')}%</span></div>
                    <div class="stat-item"><span class="label">SwStr%/BABIP</span><span class="value data-font">{home_pitcher.get('swstr', '---')}%/{home_pitcher.get('babip', '---')}</span></div>
                    <div class="stat-item"><span class="label">対左/右 OPS</span><span class="value data-font">{home_pitcher.get('vs_left_ops', '---')}/{home_pitcher.get('vs_right_ops', '---')}</span></div>
                </section>
                <section class="mb-4">
                    <h2 class="section-title">中継ぎ陣 ({home_data.get('bullpen', {}).get('count', '?')}名)</h2>
                    <div class="stat-item"><span class="label">ERA/FIP/xFIP</span><span class="value data-font">{home_data.get('bullpen', {}).get('era', '---')}/{home_data.get('bullpen', {}).get('fip', '---')}/{home_data.get('bullpen', {}).get('xfip', '---')}</span></div>
                    <div class="stat-item"><span class="label">CL FIP</span><span class="value data-font">{home_data.get('bullpen', {}).get('closer_fip', '---')} ({home_data.get('bullpen', {}).get('closer', '---')})</span></div>
                    <div class="stat-item"><span class="label">疲労度</span><span class="value">{home_data.get('bullpen', {}).get('fatigue', '---')}</span></div>
                </section>
                <section>
                    <h2 class="section-title">攻撃 ({home_vs_type})</h2>
                    <div class="stat-item"><span class="label">AVG/OPS</span><span class="value data-font">{home_data.get('batting', {}).get('avg', '---')}/{home_data.get('batting', {}).get('ops', '---')}</span></div>
                    <div class="stat-item"><span class="label">wOBA/xwOBA</span><span class="value data-font">{home_data.get('batting', {}).get('woba', '---')}/{home_data.get('batting', {}).get('xwoba', '---')}</span></div>
                    <div class="stat-item"><span class="label">過去10試合 OPS</span><span class="value data-font {home_ops_class}">{home_data.get('batting', {}).get('ops_10', '---')}</span></div>
                </section>
            </div>
        </main>
        <footer class="mt-auto pt-3 border-t-3 border-black">
            <h3 class="text-xl font-bold mb-2">総括</h3>
            <p class="text-base leading-relaxed">{summary}</p>
        </footer>
    </div>
    '''
    return html

def convert_to_html(input_file, output_file=None):
    """メイン変換処理"""
    if output_file is None:
        base_name = Path(input_file).stem
        output_dir = Path("daily_reports/html")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{base_name}.html"
    
    games = parse_report(input_file)
    
    print(f"見つかった試合数: {len(games)}")
    
    if not games:
        print("エラー: 試合データが見つかりませんでした")
        return
    
    date_match = re.search(r'(\d+月\d+日)', str(input_file))
    date_str = date_match.group(1) if date_match else datetime.now().strftime('%m月%d日')
    
    japan_time = datetime.now().strftime('%Y/%m/%d')
    
    # HTML生成（空白最適化版）
    html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB試合予想レポート - 日本時間 {japan_time} の試合</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Noto Sans JP', sans-serif;
            background-color: #f3f4f6;
            margin: 0;
            padding: 0;
        }}
        .game-page {{
            width: 210mm;
            height: 297mm;
            padding: 12mm 10mm;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }}
        .data-font {{
            font-family: 'Roboto Mono', monospace;
            font-size: 0.9rem;
        }}
        header {{
            flex-shrink: 0;
            padding-bottom: 1rem;
            margin-bottom: 1rem;
        }}
        main {{
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            align-content: start;
        }}
        .team-stats {{
            display: grid;
            grid-template-rows: auto auto auto;
            align-content: start;
        }}
        .team-stats section {{
            min-height: 165px;
            display: flex;
            flex-direction: column;
        }}
        .team-stats section:first-child {{
            min-height: 200px;
        }}
        .team-stats section:nth-child(2) {{
            min-height: 120px;
        }}
        .team-stats section:last-child {{
            min-height: 120px;
        }}
        footer {{
            flex-shrink: 0;
            padding-top: 1rem;
            margin-top: auto;
        }}
        .team-info h1 {{
            font-size: 1.75rem !important;
            margin: 0.5rem 0;
        }}
        .team-info p {{
            font-size: 1rem !important;
            margin: 0.25rem 0;
        }}
        .game-time p {{
            margin: 0.25rem 0;
        }}
        .game-time .text-4xl {{
            font-size: 2.25rem !important;
        }}
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #1e3a8a;
            border-bottom: 2px solid #93c5fd;
            padding-bottom: 0.25rem;
            margin-bottom: 0.75rem;
            display: block;
            width: 100%;
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.4rem 0;
            border-bottom: 1px solid #e5e7eb;
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        .stat-item .label {{
            color: #4b5563;
            font-size: 0.85rem;
        }}
        .stat-item .value {{
            font-weight: 700;
            color: #111827;
            font-size: 0.85rem;
        }}
        .team-stats section {{
            margin-bottom: 1.5rem !important;
            min-height: 165px;
            display: flex;
            flex-direction: column;
        }}
        .team-stats section:first-child {{
            min-height: 200px;
        }}
        .team-stats section:nth-child(2) {{
            min-height: 120px;
        }}
        .team-stats section:last-child {{
            min-height: 120px;
            margin-bottom: 0 !important;
        }}
        .handedness-rhp {{
            background-color: #ef4444;
            color: white;
            padding: 0.1rem 0.4rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            display: inline-block;
        }}
        .handedness-lhp {{
            background-color: #3b82f6;
            color: white;
            padding: 0.1rem 0.4rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            display: inline-block;
        }}
        .no-sp {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 60px;
            background-color: #f9fafb;
            color: #6b7280;
            font-weight: 700;
            font-size: 0.9rem;
            border-radius: 0.375rem;
            margin-top: 0.75rem;
        }}
        footer h3 {{
            font-size: 1.25rem !important;
            margin-bottom: 0.5rem !important;
        }}
        footer p {{
            font-size: 1rem !important;
            line-height: 1.6 !important;
            margin: 0 !important;
        }}
        @media print {{
            body {{
                margin: 0;
                padding: 0;
                background: white;
            }}
            .game-page {{
                margin: 0;
                padding: 10mm;
                box-shadow: none;
                page-break-after: always;
                page-break-inside: avoid;
                height: 297mm;
                width: 210mm;
            }}
        }}
    </style>
</head>
<body class="bg-gray-200">
'''
    
    for game in games:
        html_content += create_game_page(game)
    
    html_content += '''
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTMLファイルを生成しました: {output_file}")
    print(f"   サイズ: {Path(output_file).stat().st_size / 1024:.1f} KB")

def main():
    """メイン関数"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python convert_to_html.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"エラー: ファイルが見つかりません: {input_file}")
        sys.exit(1)
    
    convert_to_html(input_file, output_file)

if __name__ == "__main__":
    main()