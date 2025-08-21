#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB試合レポートをHTMLに変換するスクリプト（完全版）
総括機能強化版
"""

import re
import sys
from pathlib import Path
from datetime import datetime

def parse_report(file_path):
    """レポートをパースして試合データを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    games = []
    
    # 試合ごとに分割（**Team @ Team**形式）
    game_pattern = r'\*\*([^*]+) @ ([^*]+)\*\*'
    matches = list(re.finditer(game_pattern, content))
    
    print(f"見つかった試合数: {len(matches)}")
    
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
            'away_data': parse_team_data(game_section, away_team),
            'home_data': parse_team_data(game_section, home_team)
        }
        
        # 時刻
        time_match = re.search(r'開始時刻: (\d+/\d+ \d+:\d+)', game_section)
        if time_match:
            game_data['time'] = time_match.group(1)
        
        # デバッグ出力
        print(f"試合 {i+1}: {away_team} @ {home_team}")
        print(f"  Away先発: {game_data['away_data'].get('pitcher_name', '未定')}")
        print(f"  Home先発: {game_data['home_data'].get('pitcher_name', '未定')}")
        
        games.append(game_data)
    
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
        data['pitcher_name'] = pitcher_match.group(1)
        data['pitcher_record'] = pitcher_match.group(2)
        data['pitcher_hand'] = 'R'  # デフォルト右投げ
    elif '先発**: 未定' in team_section or '先発' in team_section and '未定' in team_section:
        data['pitcher_name'] = '未定'
        data['pitcher_record'] = ''
    
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

def create_team_section(data, title):
    """チームセクションのHTML生成"""
    pitcher_name = data.get('pitcher_name', '未定')
    pitcher_record = data.get('pitcher_record', '')
    pitcher_hand = data.get('pitcher_hand', 'R')
    hand_color = '#dc3545' if pitcher_hand == 'R' else '#007bff'
    hand_text = '右投' if pitcher_hand == 'R' else '左投'
    
    html = f'''
    <div class="stats-category">
        <h3 class="stats-title">{title}</h3>
        <div class="pitcher-info">
            <span class="pitcher-name">{pitcher_name}</span>
            {f'<span class="pitcher-record">({pitcher_record})</span>' if pitcher_record else ''}
            {f'<span class="pitcher-hand" style="background-color: {hand_color}">{hand_text}</span>' if pitcher_name != '未定' else ''}
        </div>'''
    
    # 先発投手が未定でない場合のみ投手統計を表示
    if pitcher_name != '未定':
        html += f'''
        <div class="stat-row">
            <span class="stat-label">ERA / FIP / xFIP</span>
            <span class="stat-value">{data.get('ERA', '---')} / {data.get('FIP', '---')} / {data.get('xFIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">WHIP / QS率</span>
            <span class="stat-value">{data.get('WHIP', '---')} / {data.get('QS_rate', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">K-BB% / SwStr%</span>
            <span class="stat-value">{data.get('K-BB%', '---')} / {data.get('SwStr%', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">GB% / FB% / BABIP</span>
            <span class="stat-value">{data.get('GB%', '---')} / {data.get('FB%', '---')} / {data.get('BABIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">対左打者</span>
            <span class="stat-value">{data.get('vs_left_avg', '---')} (OPS {data.get('vs_left_ops', '---')})</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">対右打者</span>
            <span class="stat-value">{data.get('vs_right_avg', '---')} (OPS {data.get('vs_right_ops', '---')})</span>
        </div>'''
    
    html += f'''
    </div>
    
    <div class="stats-category">
        <h3 class="stats-title">中継ぎ陣 ({data.get('bullpen_count', '?')}名)</h3>
        <div class="stat-row">
            <span class="stat-label">ERA / FIP / xFIP</span>
            <span class="stat-value">{data.get('bullpen_ERA', '---')} / {data.get('bullpen_FIP', '---')} / {data.get('bullpen_xFIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">WHIP / K-BB%</span>
            <span class="stat-value">{data.get('bullpen_WHIP', '---')} / {data.get('bullpen_KBB', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">疲労度</span>
            <span class="stat-value {get_fatigue_class(data.get('fatigue', ''))}">{data.get('fatigue', '---')}</span>
        </div>
    </div>
    
    <div class="stats-category">
        <h3 class="stats-title">攻撃</h3>
        <div class="stat-row">
            <span class="stat-label">AVG / OPS</span>
            <span class="stat-value">{data.get('AVG', '---')} / {data.get('OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">得点 / 本塁打</span>
            <span class="stat-value">{data.get('runs', '---')} / {data.get('homeruns', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">wOBA / xwOBA</span>
            <span class="stat-value">{data.get('wOBA', '---')} / {data.get('xwOBA', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Barrel% / Hard-Hit%</span>
            <span class="stat-value">{data.get('Barrel%', '---')} / {data.get('Hard-Hit%', '---')}</span>
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
    return html

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

def generate_summary(game_data):
    """試合の総括を生成（詳細版）"""
    away_data = game_data['away_data']
    home_data = game_data['home_data']
    away_name = game_data['away_team']
    home_name = game_data['home_team']
    
    # 先発投手が未定の場合
    if away_data.get('pitcher_name') == '未定' or home_data.get('pitcher_name') == '未定':
        return "先発投手が未定またはデータが不足しているため、詳細な予想は困難です。"
    
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
    
    # 先発投手の比較（xFIPが低い方が良い）
    if away_sp_xfip < home_sp_xfip:
        score += 1.5
    if home_sp_xfip < away_sp_xfip:
        score -= 1.5
    
    # ブルペンの比較（FIPが低い方が良い）
    if away_bp_fip < home_bp_fip:
        score += 1
    if home_bp_fip < away_bp_fip:
        score -= 1
    
    # 打線の勢い比較（OPSが高い方が良い）
    if away_ops_10g > home_ops_10g:
        score += 1.2
    if home_ops_10g > away_ops_10g:
        score -= 1.2
    
    # 結果の生成
    # 実際の値が取得できているか確認
    if away_sp_xfip == 99 or home_sp_xfip == 99:
        # データが不完全な場合は簡易版
        return generate_simple_summary(game_data)
    
    if score > 1.0:
        return f"先発投手(xFIP: {away_sp_xfip:.2f} vs {home_sp_xfip:.2f})、ブルペン(FIP: {away_bp_fip:.2f} vs {home_bp_fip:.2f})、そして打線の勢い(過去10試合OPS: {away_ops_10g:.3f} vs {home_ops_10g:.3f})を総合的に判断し、{away_name}が有利と予想します。"
    elif score < -1.0:
        return f"先発投手(xFIP: {away_sp_xfip:.2f} vs {home_sp_xfip:.2f})、ブルペン(FIP: {away_bp_fip:.2f} vs {home_bp_fip:.2f})、そして打線の勢い(過去10試合OPS: {away_ops_10g:.3f} vs {home_ops_10g:.3f})を総合的に判断し、{home_name}が有利と予想します。"
    else:
        return f"先発投手、ブルペン、打撃の各要素が拮抗しており、非常に接戦が予想されます。ホームアドバンテージを考慮すると、わずかに{home_name}が有利かもしれません。"

def generate_simple_summary(game_data):
    """シンプルな総括（データ不足時のフォールバック）"""
    away = game_data['away_data']
    home = game_data['home_data']
    away_name = game_data['away_team']
    home_name = game_data['home_team']
    
    summary = []
    
    # ERA比較
    try:
        if away.get('ERA') and home.get('ERA'):
            away_era = float(away['ERA'])
            home_era = float(home['ERA'])
            if abs(away_era - home_era) > 1.0:
                better_team = away_name if away_era < home_era else home_name
                summary.append(f"{better_team}の先発投手が優位")
    except:
        pass
    
    # 打撃の調子
    try:
        if away.get('past10_OPS') and home.get('past10_OPS'):
            away_ops = float(away['past10_OPS'])
            home_ops = float(home['past10_OPS'])
            if away_ops > 0.800:
                summary.append(f"{away_name}の打線が好調")
            if home_ops > 0.800:
                summary.append(f"{home_name}の打線が好調")
    except:
        pass
    
    # デフォルトの総括
    if not summary:
        summary.append("両チームが拮抗しており、接戦が予想される")
        summary.append(f"ホームの{home_name}にわずかながらアドバンテージがある")
    
    return '。'.join(summary) + '。'

def create_html_page(game_data):
    """1試合分のHTMLページを生成"""
    away_logo = get_team_logo_url(game_data['away_team'])
    home_logo = get_team_logo_url(game_data['home_team'])
    
    html = f'''
    <div class="page">
        <!-- ヘッダー -->
        <div class="header-top">
            <div class="team-header">
                <img src="{away_logo}" alt="{game_data['away_team']}" class="team-logo-img">
                <h2 class="team-name">{game_data['away_team']}</h2>
                <div class="pitcher-name">{game_data['away_data'].get('pitcher_name', '未定')} {game_data['away_data'].get('pitcher_record', '')}</div>
            </div>
            
            <div class="vs-section">
                <div class="game-time">{game_data.get('time', '時刻不明')}</div>
                <div class="vs-text">VS</div>
            </div>
            
            <div class="team-header">
                <img src="{home_logo}" alt="{game_data['home_team']}" class="team-logo-img">
                <h2 class="team-name">{game_data['home_team']}</h2>
                <div class="pitcher-name">{game_data['home_data'].get('pitcher_name', '未定')} {game_data['home_data'].get('pitcher_record', '')}</div>
            </div>
        </div>
        
        <!-- メインコンテンツ -->
        <div class="main-content">
            <div class="team-column">
                {create_team_section(game_data['away_data'], '先発投手')}
            </div>
            
            <div class="team-column">
                {create_team_section(game_data['home_data'], '先発投手')}
            </div>
        </div>
        
        <!-- 総括 -->
        <div class="summary-section">
            <h3 class="summary-title">総括</h3>
            <p class="summary-text">{generate_summary(game_data)}</p>
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
    
    # HTML生成
    css = '''
    <style>
        @media print {
            @page { size: A4 portrait; margin: 10mm; }
            .page { page-break-after: always; }
            .page:last-child { page-break-after: avoid; }
        }
        
        body {
            font-family: 'Segoe UI', 'Noto Sans JP', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .page {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            min-height: 277mm;
            max-width: 210mm;
            margin-left: auto;
            margin-right: auto;
        }
        
        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .team-header {
            text-align: center;
            flex: 1;
        }
        
        .team-logo-img {
            width: 60px;
            height: 60px;
            margin-bottom: 10px;
        }
        
        .team-name {
            color: white;
            font-size: 18px;
            margin: 5px 0;
        }
        
        .pitcher-name {
            color: white;
            font-size: 14px;
            opacity: 0.9;
        }
        
        .vs-section {
            text-align: center;
            padding: 0 20px;
        }
        
        .game-time {
            color: white;
            font-size: 12px;
            margin-bottom: 10px;
        }
        
        .vs-text {
            color: white;
            font-size: 28px;
            font-weight: bold;
        }
        
        .main-content {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .team-column {
            flex: 1;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .stats-category {
            margin-bottom: 15px;
        }
        
        .stats-title {
            font-size: 14px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 4px;
        }
        
        .pitcher-info {
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .pitcher-hand {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            color: white;
            font-size: 11px;
            font-weight: bold;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            border-bottom: 1px solid #dee2e6;
            font-size: 12px;
        }
        
        .stat-label {
            color: #666;
        }
        
        .stat-value {
            font-weight: bold;
            color: #333;
        }
        
        .stat-value.good {
            color: #28a745;
        }
        
        .stat-value.warning {
            color: #dc3545;
        }
        
        .summary-section {
            padding: 15px;
            background: #e9ecef;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .summary-title {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        
        .summary-text {
            color: #666;
            line-height: 1.5;
            font-size: 13px;
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