#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB試合レポートをHTMLに変換するスクリプト（完全版）
PDF最適化版 - 1試合1ページ - キャッシュから投手利き腕取得
"""

import re
import sys
import json
import os
from pathlib import Path
from datetime import datetime

def get_pitcher_hand_from_cache(pitcher_name):
    """キャッシュから投手の利き腕情報を取得"""
    cache_dir = Path("cache/pitcher_info")
    
    if not cache_dir.exists():
        print(f"  警告: キャッシュディレクトリが存在しません: {cache_dir}")
        return 'R'  # デフォルト
    
    # 投手名を正規化（スペースの違いなどに対応）
    normalized_name = pitcher_name.strip()
    
    # キャッシュファイルを検索
    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # JSONオブジェクトが複数連結している場合の対処
                # 各JSONオブジェクトを個別に処理
                json_objects = content.split('}{')
                for i, obj in enumerate(json_objects):
                    if i > 0:
                        obj = '{' + obj
                    if i < len(json_objects) - 1:
                        obj = obj + '}'
                    
                    try:
                        data = json.loads(obj)
                        if data.get('name', '').strip() == normalized_name:
                            hand = data.get('hand', '')
                            # 文字化け対応と判定
                            if '左' in hand or 'left' in hand.lower() or hand == '蟾ｦ' or 'L' in hand:
                                print(f"  {normalized_name}: 左投げ（キャッシュから）")
                                return 'L'
                            elif '右' in hand or 'right' in hand.lower() or hand == '蜿ｳ' or 'R' in hand:
                                print(f"  {normalized_name}: 右投げ（キャッシュから）")
                                return 'R'
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"  警告: キャッシュファイル読み込みエラー {cache_file}: {e}")
            continue
    
    print(f"  {normalized_name}: キャッシュに見つからず（デフォルト右）")
    return 'R'  # デフォルト

def parse_report(file_path):
    """レポートをパースして試合データを抽出（修正版）"""
    import re
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # セクションごとに分割
    sections = re.split(r'={50,}', content)
    
    games = []
    current_game = None
    
    for section in sections:
        # 試合情報を探す（チーム名のパターンを改善）
        match = re.search(r'([A-Za-z\s.]+?)\s*@\s*([A-Za-z\s.]+)', section)
        if match:
            if current_game:
                games.append(current_game)
            
            current_game = {
                'away_team': match.group(1).strip(),
                'home_team': match.group(2).strip(),
                'away_pitcher': {},
                'home_pitcher': {},
                'away_bullpen': {},
                'home_bullpen': {},
                'away_batting': {},
                'home_batting': {}
            }
            
            # 開始時刻を探す
            time_match = re.search(r'開始時刻:\s*(\d+/\d+\s+\d+:\d+)', section)
            if time_match:
                current_game['start_time'] = time_match.group(1)
    
    if current_game:
        games.append(current_game)
    
    # 各試合のデータを詳細にパース
    for i, game in enumerate(games):
        # 次の試合のインデックスを取得
        next_index = i + 1
        
        # 該当セクションを探す
        game_content = ""
        found = False
        for section in sections:
            if f"{game['away_team']} @ {game['home_team']}" in section:
                found = True
                game_content = section
                # 次の区切りまでのセクションも含める
                idx = sections.index(section)
                if idx + 1 < len(sections):
                    # 次のセクションに別の試合がなければ追加
                    next_section = sections[idx + 1]
                    if not re.search(r'([A-Za-z\s.]+?)\s*@\s*([A-Za-z\s.]+)', next_section):
                        game_content += "\n" + next_section
                break
        
        if not found:
            continue
        
        # チームデータをパース
        teams = re.split(r'【(.+?)】', game_content)
        
        for j in range(1, len(teams), 2):
            if j >= len(teams):
                break
                
            team_name = teams[j]
            team_data = teams[j+1] if j+1 < len(teams) else ""
            
            # どちらのチームか判定
            is_away = game['away_team'] in team_name or team_name in game['away_team']
            team_prefix = 'away' if is_away else 'home'
            
            # 先発投手情報
            pitcher_match = re.search(r'先発:\s*(.+?)\s*\(([左右両])\)\s*\((\d+)勝(\d+)敗\)', team_data)
            if pitcher_match:
                game[f'{team_prefix}_pitcher'] = {
                    'name': pitcher_match.group(1),
                    'hand': pitcher_match.group(2),
                    'wins': pitcher_match.group(3),
                    'losses': pitcher_match.group(4)
                }
                
                # ERA, FIP等の統計
                stats_match = re.search(r'ERA:\s*([\d.]+).*?FIP:\s*([\d.]+).*?xFIP:\s*([\d.]+).*?WHIP:\s*([\d.]+)', team_data)
                if stats_match:
                    game[f'{team_prefix}_pitcher'].update({
                        'era': stats_match.group(1),
                        'fip': stats_match.group(2),
                        'xfip': stats_match.group(3),
                        'whip': stats_match.group(4)
                    })
                
                # K-BB%等
                kbb_match = re.search(r'K-BB%:\s*([\d.]+)%', team_data)
                if kbb_match:
                    game[f'{team_prefix}_pitcher']['k_bb'] = kbb_match.group(1)
            
            # 中継ぎ陣情報
            bullpen_match = re.search(r'中継ぎ陣.*?ERA:\s*([\d.]+).*?FIP:\s*([\d.]+).*?xFIP:\s*([\d.]+).*?WHIP:\s*([\d.]+)', team_data, re.DOTALL)
            if bullpen_match:
                game[f'{team_prefix}_bullpen'] = {
                    'era': bullpen_match.group(1),
                    'fip': bullpen_match.group(2),
                    'xfip': bullpen_match.group(3),
                    'whip': bullpen_match.group(4)
                }
            
            # チーム打撃情報
            batting_match = re.search(r'AVG:\s*([\d.]+).*?OPS:\s*([\d.]+)', team_data)
            if batting_match:
                game[f'{team_prefix}_batting'] = {
                    'avg': batting_match.group(1),
                    'ops': batting_match.group(2)
                }
                
                # wOBA
                woba_match = re.search(r'wOBA:\s*([\d.]+).*?xwOBA:\s*([\d.]+)', team_data)
                if woba_match:
                    game[f'{team_prefix}_batting']['woba'] = woba_match.group(1)
                    game[f'{team_prefix}_batting']['xwoba'] = woba_match.group(2)
                
                # 過去試合OPS
                recent_match = re.search(r'過去5試合OPS:\s*([\d.]+).*?過去10試合OPS:\s*([\d.]+)', team_data)
                if recent_match:
                    game[f'{team_prefix}_batting']['ops_5'] = recent_match.group(1)
                    game[f'{team_prefix}_batting']['ops_10'] = recent_match.group(2)
    
    return games

def parse_team_data(section, team_name):
    """チームセクションからデータを抽出"""
    data = {}
    
    # チームセクションを抽出（【チーム名】から次の【まで）
    team_pattern = f'【{re.escape(team_name)}】([^【]+)'
    team_match = re.search(team_pattern, section, re.DOTALL)
    
    if not team_match:
        print(f"  警告: {team_name}のセクションが見つかりません")
        return data
    
    team_section = team_match.group(1)
    
    # 先発投手
    pitcher_match = re.search(r'\*\*先発\*\*[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)', team_section)
    if pitcher_match:
        data['pitcher_name'] = pitcher_match.group(1).strip()
        data['pitcher_record'] = pitcher_match.group(2)
        
        # キャッシュから利き腕を取得
        data['pitcher_hand'] = get_pitcher_hand_from_cache(data['pitcher_name'])
        
    elif '先発**: 未定' in team_section or '先発' in team_section and '未定' in team_section:
        data['pitcher_name'] = '未定'
        data['pitcher_record'] = ''
        data['pitcher_hand'] = 'R'
    
    # 投手統計（ERA行）- 先発が未定でない場合のみ
    if data.get('pitcher_name') != '未定':
        era_line = re.search(r'ERA:\s*([\d.]+)\s*\|\s*FIP:\s*([\d.]+)\s*\|\s*xFIP:\s*([\d.]+)\s*\|\s*WHIP:\s*([\d.]+)', team_section)
        if era_line:
            data['ERA'] = era_line.group(1)
            data['FIP'] = era_line.group(2)
            data['xFIP'] = era_line.group(3)
            data['WHIP'] = era_line.group(4)
        
        # 追加の投手統計
        kbb_match = re.search(r'K-BB%:\s*([\d.]+)%', team_section)
        if kbb_match:
            data['K-BB%'] = kbb_match.group(1) + '%'
        
        gb_match = re.search(r'GB%:\s*([\d.]+)%', team_section)
        if gb_match:
            data['GB%'] = gb_match.group(1) + '%'
        
        fb_match = re.search(r'FB%:\s*([\d.]+)%', team_section)
        if fb_match:
            data['FB%'] = fb_match.group(1) + '%'
        
        qs_match = re.search(r'QS率:\s*([\d.]+)%', team_section)
        if qs_match:
            data['QS_rate'] = qs_match.group(1) + '%'
        
        swstr_match = re.search(r'SwStr%:\s*([\d.]+)%', team_section)
        if swstr_match:
            data['SwStr%'] = swstr_match.group(1) + '%'
        
        babip_match = re.search(r'BABIP:\s*([\d.]+)', team_section)
        if babip_match:
            data['BABIP'] = babip_match.group(1)
    
    # 対左右成績
    vs_left = re.search(r'対左:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', team_section)
    if vs_left:
        data['vs_left_avg'] = vs_left.group(1)
        data['vs_left_ops'] = vs_left.group(2)
    
    vs_right = re.search(r'対右:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', team_section)
    if vs_right:
        data['vs_right_avg'] = vs_right.group(1)
        data['vs_right_ops'] = vs_right.group(2)
    
    # 中継ぎ陣
    bullpen_match = re.search(r'\*\*中継ぎ陣\*\*\s*\((\d+)名\)', team_section)
    if bullpen_match:
        data['bullpen_count'] = bullpen_match.group(1)
    
    bullpen_era = re.search(r'中継ぎ陣.*?\nERA:\s*([\d.]+)\s*\|\s*FIP:\s*([\d.]+)\s*\|\s*xFIP:\s*([\d.]+)', team_section, re.DOTALL)
    if bullpen_era:
        data['bullpen_ERA'] = bullpen_era.group(1)
        data['bullpen_FIP'] = bullpen_era.group(2)
        data['bullpen_xFIP'] = bullpen_era.group(3)
    
    bullpen_whip = re.search(r'中継ぎ陣.*?WHIP:\s*([\d.]+)', team_section, re.DOTALL)
    if bullpen_whip:
        data['bullpen_WHIP'] = bullpen_whip.group(1)
    
    bullpen_kbb = re.search(r'中継ぎ陣.*?K-BB%:\s*([\d.]+)%', team_section, re.DOTALL)
    if bullpen_kbb:
        data['bullpen_KBB'] = bullpen_kbb.group(1) + '%'
    
    # 疲労度
    fatigue_match = re.search(r'疲労度:\s*(.+)', team_section)
    if fatigue_match:
        data['fatigue'] = fatigue_match.group(1).strip()
    
    # チーム打撃
    team_avg = re.search(r'AVG:\s*([\d.]+)\s*\|\s*OPS:\s*([\d.]+)', team_section)
    if team_avg:
        data['AVG'] = team_avg.group(1)
        data['OPS'] = team_avg.group(2)
    
    # 得点と本塁打
    runs_hr = re.search(r'得点:\s*(\d+)\s*\|\s*本塁打:\s*(\d+)', team_section)
    if runs_hr:
        data['runs'] = runs_hr.group(1)
        data['homeruns'] = runs_hr.group(2)
    
    woba_match = re.search(r'wOBA:\s*([\d.]+)\s*\|\s*xwOBA:\s*([\d.]+)', team_section)
    if woba_match:
        data['wOBA'] = woba_match.group(1)
        data['xwOBA'] = woba_match.group(2)
    
    # Barrel%とHard-Hit%
    barrel_match = re.search(r'Barrel%:\s*([\d.]+)%', team_section)
    if barrel_match:
        data['Barrel%'] = barrel_match.group(1) + '%'
    
    hardhit_match = re.search(r'Hard-Hit%:\s*([\d.]+)%', team_section)
    if hardhit_match:
        data['Hard-Hit%'] = hardhit_match.group(1) + '%'
    
    # 対左右投手
    vs_left_pitcher = re.search(r'対左投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', team_section)
    if vs_left_pitcher:
        data['vs_left_pitcher_avg'] = vs_left_pitcher.group(1)
        data['vs_left_pitcher_ops'] = vs_left_pitcher.group(2)
    
    vs_right_pitcher = re.search(r'対右投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', team_section)
    if vs_right_pitcher:
        data['vs_right_pitcher_avg'] = vs_right_pitcher.group(1)
        data['vs_right_pitcher_ops'] = vs_right_pitcher.group(2)
    
    # 過去の成績
    past5_match = re.search(r'過去5試合OPS:\s*([\d.]+)', team_section)
    if past5_match:
        data['past5_OPS'] = past5_match.group(1)
    
    past10_match = re.search(r'過去10試合OPS:\s*([\d.]+)', team_section)
    if past10_match:
        data['past10_OPS'] = past10_match.group(1)
    
    return data

def get_team_logo_url(team_name):
    """チーム名からロゴURLを生成"""
    # MLB公式APIのロゴURL形式
    team_logos = {
        'Athletics': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/133.svg',
        'Minnesota Twins': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/142.svg',
        'Texas Rangers': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/140.svg',
        'Kansas City Royals': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/118.svg',
        'Milwaukee Brewers': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/158.svg',
        'Chicago Cubs': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/112.svg',
        'Los Angeles Dodgers': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/119.svg',
        'Colorado Rockies': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/115.svg',
        'New York Mets': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/121.svg',
        'Washington Nationals': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/120.svg',
        'San Francisco Giants': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/137.svg',
        'San Diego Padres': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/135.svg',
        'Houston Astros': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/117.svg',
        'Baltimore Orioles': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/110.svg',
        'Boston Red Sox': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/111.svg',
        'New York Yankees': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/147.svg',
        'St. Louis Cardinals': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/138.svg',
        'Tampa Bay Rays': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/139.svg',
        'Seattle Mariners': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/136.svg',
        'Philadelphia Phillies': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/143.svg',
        'Cincinnati Reds': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/113.svg',
        'Miami Marlins': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/146.svg',
        'Detroit Tigers': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/116.svg',
        'Toronto Blue Jays': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/141.svg',
        'Arizona Diamondbacks': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/109.svg',
        'Pittsburgh Pirates': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/134.svg',
        'Cleveland Guardians': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/114.svg',
        'Atlanta Braves': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/144.svg',
        'Chicago White Sox': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/145.svg',
        'Los Angeles Angels': 'https://www.mlbstatic.com/team-logos/team-cap-on-light/108.svg',
    }
    
    return team_logos.get(team_name, 'https://www.mlbstatic.com/team-logos/league-on-light/1.svg')

def get_fatigue_class(fatigue_text):
    """疲労度に応じたCSSクラスを返す"""
    if '連投中' in fatigue_text:
        return 'warning'
    return ''

def get_ops_class(ops):
    """OPSに応じたCSSクラスを返す"""
    try:
        ops_val = float(ops)
        if ops_val >= 0.800:
            return 'good'
        elif ops_val <= 0.650:
            return 'warning'
    except:
        pass
    return ''

def create_team_stats(data):
    """チームの統計セクションを生成"""
    
    # 投手の利き腕を判定
    pitcher_hand = data.get('pitcher_hand', 'R')
    hand_color = '#ef4444' if pitcher_hand == 'R' else '#3b82f6'
    hand_text = '右' if pitcher_hand == 'R' else '左'
    
    # 先発投手セクション
    pitcher_name = data.get('pitcher_name', '未定')
    pitcher_record = data.get('pitcher_record', '')
    
    pitcher_html = f'''
    <div class="stat-section">
        <div class="section-header">
            <span class="section-title">先発投手</span>
            <span class="pitcher-name">{pitcher_name} {f'({pitcher_record})' if pitcher_record else ''}</span>
            {f'<span class="pitcher-badge" style="background-color: {hand_color}">{hand_text}</span>' if pitcher_name != '未定' else ''}
        </div>'''
    
    if pitcher_name != '未定':
        pitcher_html += f'''
        <div class="stat-row">
            <span class="stat-label">ERA / FIP / xFIP</span>
            <span class="stat-value">{data.get('ERA', '---')} / {data.get('FIP', '---')} / {data.get('xFIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">WHIP</span>
            <span class="stat-value">{data.get('WHIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">K-BB%</span>
            <span class="stat-value">{data.get('K-BB%', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">GB% / FB%</span>
            <span class="stat-value">{data.get('GB%', '---')} / {data.get('FB%', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">QS率</span>
            <span class="stat-value">{data.get('QS_rate', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">対左/右 OPS</span>
            <span class="stat-value">{data.get('vs_left_ops', '---')} / {data.get('vs_right_ops', '---')}</span>
        </div>'''
    
    pitcher_html += '''
    </div>
    '''
    
    # 中継ぎ陣セクション
    bullpen_html = f'''
    <div class="stat-section">
        <div class="section-header">
            <span class="section-title">中継ぎ ({data.get('bullpen_count', '?')}名)</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">ERA / FIP / xFIP</span>
            <span class="stat-value">{data.get('bullpen_ERA', '---')} / {data.get('bullpen_FIP', '---')} / {data.get('bullpen_xFIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">WHIP</span>
            <span class="stat-value">{data.get('bullpen_WHIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">K-BB%</span>
            <span class="stat-value">{data.get('bullpen_KBB', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">疲労度</span>
            <span class="stat-value {get_fatigue_class(data.get('fatigue', ''))}">{data.get('fatigue', '---')}</span>
        </div>
    </div>
    '''
    
    # 攻撃セクション
    batting_html = f'''
    <div class="stat-section">
        <div class="section-header">
            <span class="section-title">攻撃</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">AVG / OPS</span>
            <span class="stat-value">{data.get('AVG', '---')} / {data.get('OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">wOBA / xwOBA</span>
            <span class="stat-value">{data.get('wOBA', '---')} / {data.get('xwOBA', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">対左/右 OPS</span>
            <span class="stat-value">{data.get('vs_left_pitcher_ops', '---')} / {data.get('vs_right_pitcher_ops', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">過去5試合 OPS</span>
            <span class="stat-value {get_ops_class(data.get('past5_OPS', 0))}">{data.get('past5_OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">過去10試合 OPS</span>
            <span class="stat-value {get_ops_class(data.get('past10_OPS', 0))}">{data.get('past10_OPS', '---')}</span>
        </div>
    </div>
    '''
    
    return pitcher_html + bullpen_html + batting_html

def generate_summary(game_data):
    """試合の総括を生成（元のロジックを維持）"""
    away_data = game_data['away_data']
    home_data = game_data['home_data']
    away_name = game_data['away_team']
    home_name = game_data['home_team']
    
    # 先発投手が未定の場合
    if away_data.get('pitcher_name') == '未定' or home_data.get('pitcher_name') == '未定':
        return "先発投手が未定またはデータが不足しているため、詳細な予想は困難です。最新の情報を確認してください。"
    
    # 各種統計値を取得（デフォルト値付き）
    try:
        away_sp_xfip = float(away_data.get('xFIP', 99))
    except:
        away_sp_xfip = 99
    
    try:
        home_sp_xfip = float(home_data.get('xFIP', 99))
    except:
        home_sp_xfip = 99
    
    try:
        away_bp_fip = float(away_data.get('bullpen_FIP', 99))
    except:
        away_bp_fip = 99
    
    try:
        home_bp_fip = float(home_data.get('bullpen_FIP', 99))
    except:
        home_bp_fip = 99
    
    try:
        away_ops_10g = float(away_data.get('past10_OPS', 0))
    except:
        away_ops_10g = 0
    
    try:
        home_ops_10g = float(home_data.get('past10_OPS', 0))
    except:
        home_ops_10g = 0
    
    # スコア計算
    score = 0
    analysis_points = []
    
    # 先発投手の比較（xFIPが低い方が良い）
    if away_sp_xfip != 99 and home_sp_xfip != 99:
        xfip_diff = home_sp_xfip - away_sp_xfip
        if abs(xfip_diff) > 0.5:
            if xfip_diff > 0:
                score += 1.5
                analysis_points.append(f"先発投手では{away_name}の{away_data.get('pitcher_name', '')}（xFIP {away_sp_xfip:.2f}）が{home_name}の{home_data.get('pitcher_name', '')}（xFIP {home_sp_xfip:.2f}）を上回る")
            else:
                score -= 1.5
                analysis_points.append(f"先発投手では{home_name}の{home_data.get('pitcher_name', '')}（xFIP {home_sp_xfip:.2f}）が{away_name}の{away_data.get('pitcher_name', '')}（xFIP {away_sp_xfip:.2f}）を上回る")
    
    # ブルペンの比較（FIPが低い方が良い）
    if away_bp_fip != 99 and home_bp_fip != 99:
        bp_diff = home_bp_fip - away_bp_fip
        if abs(bp_diff) > 0.3:
            if bp_diff > 0:
                score += 1
                analysis_points.append(f"ブルペンは{away_name}（FIP {away_bp_fip:.2f}）が{home_name}（FIP {home_bp_fip:.2f}）より優秀")
            else:
                score -= 1
                analysis_points.append(f"ブルペンは{home_name}（FIP {home_bp_fip:.2f}）が{away_name}（FIP {away_bp_fip:.2f}）より優秀")
    
    # 打線の勢い比較（OPSが高い方が良い）
    if away_ops_10g > 0 and home_ops_10g > 0:
        ops_diff = away_ops_10g - home_ops_10g
        if abs(ops_diff) > 0.050:
            if ops_diff > 0:
                score += 1.2
                analysis_points.append(f"打線の勢いは{away_name}（過去10試合OPS {away_ops_10g:.3f}）が{home_name}（{home_ops_10g:.3f}）を大きく上回る")
            else:
                score -= 1.2
                analysis_points.append(f"打線の勢いは{home_name}（過去10試合OPS {home_ops_10g:.3f}）が{away_name}（{away_ops_10g:.3f}）を大きく上回る")
    
    # 疲労度の分析
    away_fatigue = away_data.get('fatigue', '')
    home_fatigue = home_data.get('fatigue', '')
    if '連投中' in away_fatigue and '連投中' not in home_fatigue:
        analysis_points.append(f"{away_name}のブルペンに疲労の懸念あり（{away_fatigue}）")
        score -= 0.5
    elif '連投中' in home_fatigue and '連投中' not in away_fatigue:
        analysis_points.append(f"{home_name}のブルペンに疲労の懸念あり（{home_fatigue}）")
        score += 0.5
    
    # 詳細な総括を生成
    summary_parts = []
    
    # 分析ポイントを追加
    if analysis_points:
        summary_parts.append("。".join(analysis_points) + "。")
    
    # 最終判定
    if score > 1.0:
        summary_parts.append(f"これらの要因を総合的に判断すると、{away_name}が有利と予想される。")
        if score > 2.5:
            summary_parts.append("特に投手力の差が大きく、試合の主導権を握る可能性が高い。")
    elif score < -1.0:
        summary_parts.append(f"これらの要因を総合的に判断すると、{home_name}が有利と予想される。")
        if score < -2.5:
            summary_parts.append("ホームアドバンテージも含め、優位性は明確だ。")
    else:
        summary_parts.append("両チームの戦力は拮抗しており、接戦が予想される。")
        summary_parts.append(f"ホームアドバンテージを考慮すると、わずかに{home_name}が有利かもしれない。")
    
    return " ".join(summary_parts)

def create_html_page(game_data):
    """1試合分のHTMLページを生成"""
    away_logo = get_team_logo_url(game_data['away_team'])
    home_logo = get_team_logo_url(game_data['home_team'])
    
    html = f'''
    <div class="page">
        <!-- ヘッダー部分 -->
        <div class="header-section">
            <div class="team-header">
                <img src="{away_logo}" alt="{game_data['away_team']}" class="team-logo">
                <h2 class="team-name">{game_data['away_team']}</h2>
            </div>
            
            <div class="vs-section">
                <div class="game-time">{game_data.get('time', '時刻不明')}</div>
                <div class="game-time-label">日本時間</div>
            </div>
            
            <div class="team-header">
                <img src="{home_logo}" alt="{game_data['home_team']}" class="team-logo">
                <h2 class="team-name">{game_data['home_team']}</h2>
            </div>
        </div>
        
        <!-- メインコンテンツ -->
        <div class="stats-container">
            <div class="team-stats">
                {create_team_stats(game_data['away_data'])}
            </div>
            
            <div class="team-stats">
                {create_team_stats(game_data['home_data'])}
            </div>
        </div>
        
        <!-- 総括 -->
        <div class="summary-box">
            <h3 class="summary-header">総括</h3>
            <p class="summary-content">{generate_summary(game_data)}</p>
        </div>
    </div>
    '''
    return html

def convert_to_html(input_file, output_file=None):
    """メイン変換処理"""
    # 出力ファイル名を決定
    if not output_file:
        input_path = Path(input_file)
        output_dir = Path("daily_reports/html")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{input_path.stem}.html"
    
    # レポートをパース
    games = parse_report(input_file)
    
    if not games:
        print("エラー: 試合データが見つかりませんでした")
        return False
    
    # HTMLスタイル
    css = '''
    <style>
        @media print {
            @page { 
                size: A4 portrait; 
                margin: 15mm; 
            }
            .page { 
                page-break-after: always;
                page-break-inside: avoid;
            }
            .page:last-child { 
                page-break-after: avoid; 
            }
        }
        
        body {
            font-family: 'Segoe UI', 'Yu Gothic', 'Meiryo', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: white;
            color: #333;
        }
        
        .page {
            background: white;
            max-width: 210mm;
            margin: 0 auto 30px;
            padding: 30px;
        }
        
        /* ヘッダー部分 */
        .header-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #333;
            margin-bottom: 25px;
        }
        
        .team-header {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .team-logo {
            width: 60px;
            height: 60px;
            object-fit: contain;
        }
        
        .team-name {
            font-size: 24px;
            font-weight: bold;
            margin: 0;
            color: #1f2937;
        }
        
        .vs-section {
            text-align: center;
            padding: 0 20px;
        }
        
        .game-time {
            font-size: 14px;
            color: #333;
            margin-bottom: 2px;
        }
        
        .game-time-label {
            font-size: 11px;
            color: #666;
        }
        
        /* 統計部分 */
        .stats-container {
            display: flex;
            gap: 40px;
            margin-bottom: 25px;
        }
        
        .team-stats {
            flex: 1;
        }
        
        .stat-section {
            margin-bottom: 20px;
        }
        
        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid #2563eb;
            margin-bottom: 10px;
        }
        
        .section-title {
            font-size: 14px;
            font-weight: bold;
            color: #2563eb;
        }
        
        .pitcher-name {
            font-size: 14px;
            font-weight: bold;
            color: #1f2937;
        }
        
        .pitcher-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #e5e7eb;
            font-size: 12px;
        }
        
        .stat-label {
            color: #6b7280;
        }
        
        .stat-value {
            color: #1f2937;
            font-weight: bold;
        }
        
        .stat-value.good {
            color: #059669;
        }
        
        .stat-value.warning {
            color: #dc2626;
        }
        
        /* 総括部分 */
        .summary-box {
            padding-top: 20px;
            border-top: 2px solid #333;
        }
        
        .summary-header {
            font-size: 16px;
            font-weight: bold;
            color: #1f2937;
            margin: 0 0 10px 0;
        }
        
        .summary-content {
            font-size: 13px;
            line-height: 1.6;
            color: #374151;
            margin: 0;
        }
        
        @media print {
            body {
                padding: 0;
            }
            .page {
                margin: 0;
            }
        }
    </style>
    '''
    
    # HTMLコンテンツ生成
    games_html = []
    for game_data in games:
        games_html.append(create_html_page(game_data))
    
    # 完全なHTML生成
    html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB試合レポート</title>
    {css}
</head>
<body>
    {''.join(games_html)}
</body>
</html>'''
    
    # ファイル保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML レポートを生成しました: {output_file}")
    print(f"   - {len(games)} 試合を処理")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python convert_to_html.py <input.txt> [output.html]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_to_html(input_file, output_file)