#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB レポート HTML変換スクリプト（修正版）
テキストレポートを美しいHTML形式（A4サイズ1試合1ページ）に変換
"""

import re
import sys
import os
from datetime import datetime
from pathlib import Path

def get_team_logo(team_name):
    """チーム名からロゴURLを取得（MLB公式API）"""
    # チーム名とチームIDのマッピング
    team_ids = {
        'Yankees': '147', 'New York Yankees': '147',
        'Red Sox': '111', 'Boston Red Sox': '111',
        'Blue Jays': '141', 'Toronto Blue Jays': '141',
        'Rays': '139', 'Tampa Bay Rays': '139',
        'Orioles': '110', 'Baltimore Orioles': '110',
        'White Sox': '145', 'Chicago White Sox': '145',
        'Guardians': '114', 'Cleveland Guardians': '114',
        'Tigers': '116', 'Detroit Tigers': '116',
        'Royals': '118', 'Kansas City Royals': '118',
        'Twins': '142', 'Minnesota Twins': '142',
        'Astros': '117', 'Houston Astros': '117',
        'Athletics': '133', 'Oakland Athletics': '133',
        'Mariners': '136', 'Seattle Mariners': '136',
        'Angels': '108', 'Los Angeles Angels': '108',
        'Rangers': '140', 'Texas Rangers': '140',
        'Braves': '144', 'Atlanta Braves': '144',
        'Marlins': '146', 'Miami Marlins': '146',
        'Mets': '121', 'New York Mets': '121',
        'Phillies': '143', 'Philadelphia Phillies': '143',
        'Nationals': '120', 'Washington Nationals': '120',
        'Brewers': '158', 'Milwaukee Brewers': '158',
        'Cardinals': '138', 'St. Louis Cardinals': '138',
        'Cubs': '112', 'Chicago Cubs': '112',
        'Reds': '113', 'Cincinnati Reds': '113',
        'Pirates': '134', 'Pittsburgh Pirates': '134',
        'Dodgers': '119', 'Los Angeles Dodgers': '119',
        'Diamondbacks': '109', 'Arizona Diamondbacks': '109',
        'Rockies': '115', 'Colorado Rockies': '115',
        'Padres': '135', 'San Diego Padres': '135',
        'Giants': '137', 'San Francisco Giants': '137'
    }
    
    # MLB公式のロゴURL（高品質SVG）
    team_id = team_ids.get(team_name)
    if team_id:
        return f"https://www.mlbstatic.com/team-logos/{team_id}.svg"
    else:
        # フォールバック：ESPNのロゴ
        team_abbr = {
            'Yankees': 'nyy', 'New York Yankees': 'nyy',
            'Red Sox': 'bos', 'Boston Red Sox': 'bos',
            'Blue Jays': 'tor', 'Toronto Blue Jays': 'tor',
            'Rays': 'tb', 'Tampa Bay Rays': 'tb',
            'Orioles': 'bal', 'Baltimore Orioles': 'bal',
            'White Sox': 'cws', 'Chicago White Sox': 'cws',
            'Guardians': 'cle', 'Cleveland Guardians': 'cle',
            'Tigers': 'det', 'Detroit Tigers': 'det',
            'Royals': 'kc', 'Kansas City Royals': 'kc',
            'Twins': 'min', 'Minnesota Twins': 'min',
            'Astros': 'hou', 'Houston Astros': 'hou',
            'Athletics': 'oak', 'Oakland Athletics': 'oak',
            'Mariners': 'sea', 'Seattle Mariners': 'sea',
            'Angels': 'laa', 'Los Angeles Angels': 'laa',
            'Rangers': 'tex', 'Texas Rangers': 'tex',
            'Braves': 'atl', 'Atlanta Braves': 'atl',
            'Marlins': 'mia', 'Miami Marlins': 'mia',
            'Mets': 'nym', 'New York Mets': 'nym',
            'Phillies': 'phi', 'Philadelphia Phillies': 'phi',
            'Nationals': 'wsh', 'Washington Nationals': 'wsh',
            'Brewers': 'mil', 'Milwaukee Brewers': 'mil',
            'Cardinals': 'stl', 'St. Louis Cardinals': 'stl',
            'Cubs': 'chc', 'Chicago Cubs': 'chc',
            'Reds': 'cin', 'Cincinnati Reds': 'cin',
            'Pirates': 'pit', 'Pittsburgh Pirates': 'pit',
            'Dodgers': 'lad', 'Los Angeles Dodgers': 'lad',
            'Diamondbacks': 'ari', 'Arizona Diamondbacks': 'ari',
            'Rockies': 'col', 'Colorado Rockies': 'col',
            'Padres': 'sd', 'San Diego Padres': 'sd',
            'Giants': 'sf', 'San Francisco Giants': 'sf'
        }
        abbr = team_abbr.get(team_name, 'mlb')
        return f"https://a.espncdn.com/i/teamlogos/mlb/500/{abbr}.png"

def parse_team_data(section):
    """チームセクションからデータを抽出"""
    data = {}
    
    # 先発投手
    pitcher_match = re.search(r'\*\*先発\*\*[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)', section)
    if pitcher_match:
        data['pitcher_name'] = pitcher_match.group(1)
        data['pitcher_record'] = pitcher_match.group(2)
    elif '先発**: 未定' in section or '先発: 未定' in section or '先発\*\*: 未定' in section:
        data['pitcher_name'] = '未定'
        data['pitcher_record'] = ''
    
    # 投手統計
    patterns = {
        'ERA': r'ERA:\s*([\d.]+)',
        'FIP': r'FIP:\s*([\d.]+)',
        'xFIP': r'xFIP:\s*([\d.]+)',
        'WHIP': r'WHIP:\s*([\d.]+)',
        'K-BB%': r'K-BB%:\s*([\d.]+)%?',
        'GB%': r'GB%:\s*([\d.]+)%?',
        'FB%': r'FB%:\s*([\d.]+)%?',
        'QS率': r'QS率:\s*([\d.]+)%?',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, section)
        if match:
            data[key] = match.group(1)
    
    # 対左右成績
    vs_match = re.search(r'対左:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', section)
    if vs_match:
        data['対左AVG'] = vs_match.group(1)
        data['対左OPS'] = vs_match.group(2)
    
    vs_match = re.search(r'対右:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', section)
    if vs_match:
        data['対右AVG'] = vs_match.group(1)
        data['対右OPS'] = vs_match.group(2)
    
    # ブルペン統計
    bp_match = re.search(r'\*\*中継ぎ陣\*\*\s*\((\d+)名\)', section)
    if bp_match:
        data['bp_count'] = bp_match.group(1)
    
    # ブルペンのERA等（中継ぎ陣の後の行）
    bp_era_match = re.search(r'中継ぎ陣.*?\nERA:\s*([\d.]+)\s*\|\s*FIP:\s*([\d.]+)\s*\|\s*xFIP:\s*([\d.]+)', section, re.DOTALL)
    if bp_era_match:
        data['bp_ERA'] = bp_era_match.group(1)
        data['bp_FIP'] = bp_era_match.group(2)
        data['bp_xFIP'] = bp_era_match.group(3)
    
    # 疲労度
    fatigue_match = re.search(r'疲労度:\s*(.+)', section)
    if fatigue_match:
        data['bp_fatigue'] = fatigue_match.group(1).strip()
    
    # チーム打撃
    batting_patterns = {
        'AVG': r'AVG:\s*([\d.]+)',
        'OPS': r'OPS:\s*([\d.]+)',
        'wOBA': r'wOBA:\s*([\d.]+)',
        'xwOBA': r'xwOBA:\s*([\d.]+)',
        'Barrel%': r'Barrel%:\s*([\d.]+)%?',
        'Hard-Hit%': r'Hard-Hit%:\s*([\d.]+)%?',
    }
    
    for key, pattern in batting_patterns.items():
        match = re.search(pattern, section)
        if match:
            data[key] = match.group(1)
    
    # 過去試合OPS
    for days in [5, 10]:
        pattern = rf'過去{days}試合OPS:\s*([\d.]+)'
        match = re.search(pattern, section)
        if match:
            data[f'過去{days}試合OPS'] = match.group(1)
    
    # 対左右投手
    vs_pitcher_match = re.search(r'対左投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', section)
    if vs_pitcher_match:
        data['対左投手OPS'] = vs_pitcher_match.group(2)
    
    vs_pitcher_match = re.search(r'対右投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', section)
    if vs_pitcher_match:
        data['対右投手OPS'] = vs_pitcher_match.group(2)
    
    return data

def parse_game(content, match, next_match=None):
    """1試合分のデータを抽出"""
    away_team = match.group(1).strip()
    home_team = match.group(2).strip()
    
    # この試合のデータ範囲を特定
    start = match.start()
    if next_match:
        end = next_match.start()
    else:
        end = len(content)
    
    game_section = content[start:end]
    
    game_data = {
        'away_team': away_team,
        'home_team': home_team,
        'away_data': {},
        'home_data': {},
        'time': '',
        'summary': ''
    }
    
    # 時刻
    time_match = re.search(r'開始時刻:\s*(\d+/\d+ \d+:\d+)', game_section)
    if time_match:
        game_data['time'] = time_match.group(1)
    
    # 各チームのデータを抽出
    # 【チーム名】形式で区切られている
    sections = re.split(r'【([^】]+)】', game_section)
    
    for i in range(1, len(sections), 2):
        if i < len(sections):
            team_name = sections[i].strip()
            team_content = sections[i + 1] if i + 1 < len(sections) else ''
            
            team_data = parse_team_data(team_content)
            team_data['logo'] = get_team_logo(team_name)
            
            if team_name == away_team:
                game_data['away_data'] = team_data
            elif team_name == home_team:
                game_data['home_data'] = team_data
    
    # 総括を生成
    game_data['summary'] = generate_summary(game_data)
    
    return game_data

def generate_summary(game_data):
    """試合の総括を生成"""
    away_team = game_data.get('away_team')
    home_team = game_data.get('home_team')
    away_data = game_data.get('away_data', {})
    home_data = game_data.get('home_data', {})
    
    if not away_data or not home_data:
        return "データ不足のため分析できません。"
    
    factors = []
    
    # 先発投手の比較
    try:
        away_xfip = float(away_data.get('xFIP', 99))
        home_xfip = float(home_data.get('xFIP', 99))
        
        if away_xfip < 99 and home_xfip < 99:
            if away_xfip < home_xfip - 0.5:
                factors.append(f"先発投手では{away_team}が優位（xFIP {away_xfip:.2f} vs {home_xfip:.2f}）")
            elif home_xfip < away_xfip - 0.5:
                factors.append(f"先発投手では{home_team}が優位（xFIP {home_xfip:.2f} vs {away_xfip:.2f}）")
    except:
        pass
    
    # 打線の比較
    try:
        away_ops = float(away_data.get('過去10試合OPS', 0))
        home_ops = float(home_data.get('過去10試合OPS', 0))
        
        if away_ops > 0 and home_ops > 0:
            if away_ops > home_ops + 0.05:
                factors.append(f"{away_team}打線が好調（過去10試合OPS {away_ops:.3f}）")
            elif home_ops > away_ops + 0.05:
                factors.append(f"{home_team}打線が好調（過去10試合OPS {home_ops:.3f}）")
    except:
        pass
    
    if factors:
        summary = "。".join(factors) + "。"
    else:
        summary = "両チームが拮抗しており、接戦が予想される。"
    
    summary += f"ホームの{home_team}にわずかながらアドバンテージがある。"
    
    return summary

def create_html_page(game_data):
    """1試合分のHTMLページを生成"""
    away_team = game_data.get('away_team', 'Away')
    home_team = game_data.get('home_team', 'Home')
    away_data = game_data.get('away_data', {})
    home_data = game_data.get('home_data', {})
    
    # 先発投手名と成績
    away_pitcher = away_data.get('pitcher_name', '未定')
    away_record = away_data.get('pitcher_record', '')
    home_pitcher = home_data.get('pitcher_name', '未定')
    home_record = home_data.get('pitcher_record', '')
    
    html = f'''
    <div class="page">
        <!-- ヘッダー -->
        <div class="header-top">
            <div class="team-header">
                <img src="{away_data.get('logo', '')}" alt="{away_team}" class="team-logo-img">
                <h2 class="team-name">{away_team}</h2>
                <div class="pitcher-name">{away_pitcher} {away_record}</div>
            </div>
            
            <div class="game-info">
                <div class="date-time">{game_data.get('time', '').split()[0]}</div>
                <div class="date-time">{game_data.get('time', '').split()[1] if len(game_data.get('time', '').split()) > 1 else ''}</div>
                <div class="time-label">日本時間</div>
            </div>
            
            <div class="team-header">
                <img src="{home_data.get('logo', '')}" alt="{home_team}" class="team-logo-img">
                <h2 class="team-name">{home_team}</h2>
                <div class="pitcher-name">{home_pitcher} {home_record}</div>
            </div>
        </div>
        
        <!-- メインコンテンツ -->
        <div class="main-content">
            <div class="team-column">
                {create_team_section(away_data, away_pitcher != '未定')}
            </div>
            
            <div class="team-column">
                {create_team_section(home_data, home_pitcher != '未定')}
            </div>
        </div>
        
        <!-- 総括 -->
        <div class="summary-section">
            <h3 class="summary-title">総括</h3>
            <p class="summary-text">{game_data.get('summary', '分析中...')}</p>
        </div>
    </div>
    '''
    
    return html

def create_team_section(team_data, has_pitcher=True):
    """チームセクションのHTML生成"""
    html = ''
    
    # 先発投手セクション
    if has_pitcher and team_data.get('pitcher_name') and team_data.get('pitcher_name') != '未定':
        html += f'''
        <div class="stats-category">
            <h3 class="stats-title">先発投手</h3>
            <div class="stat-row">
                <span class="stat-label">ERA / FIP / xFIP</span>
                <span class="stat-value">{team_data.get('ERA', '---')} / {team_data.get('FIP', '---')} / {team_data.get('xFIP', '---')}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">WHIP</span>
                <span class="stat-value">{team_data.get('WHIP', '---')}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">K-BB%</span>
                <span class="stat-value">{team_data.get('K-BB%', '---')}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">GB% / FB%</span>
                <span class="stat-value">{team_data.get('GB%', '---')}% / {team_data.get('FB%', '---')}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">QS率</span>
                <span class="stat-value">{team_data.get('QS率', '---')}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">対左/右 OPS</span>
                <span class="stat-value">{team_data.get('対左OPS', '---')} / {team_data.get('対右OPS', '---')}</span>
            </div>
        </div>
        '''
    
    # 中継ぎ陣セクション
    html += f'''
    <div class="stats-category">
        <h3 class="stats-title">中継ぎ陣 ({team_data.get('bp_count', '?')}名)</h3>
        <div class="stat-row">
            <span class="stat-label">ERA / FIP / xFIP</span>
            <span class="stat-value">{team_data.get('bp_ERA', '---')} / {team_data.get('bp_FIP', '---')} / {team_data.get('bp_xFIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">疲労度</span>
            <span class="stat-value {'fatigue-warning' if '連投中' in str(team_data.get('bp_fatigue', '')) else ''}">{team_data.get('bp_fatigue', '---')}</span>
        </div>
    </div>
    '''
    
    # 攻撃セクション
    html += f'''
    <div class="stats-category">
        <h3 class="stats-title">攻撃</h3>
        <div class="stat-row">
            <span class="stat-label">AVG / OPS</span>
            <span class="stat-value">{team_data.get('AVG', '---')} / {team_data.get('OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">wOBA / xwOBA</span>
            <span class="stat-value">{team_data.get('wOBA', '---')} / {team_data.get('xwOBA', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">対左/右 OPS</span>
            <span class="stat-value">{team_data.get('対左投手OPS', '---')} / {team_data.get('対右投手OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">過去5試合 OPS</span>
            <span class="stat-value">{team_data.get('過去5試合OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">過去10試合 OPS</span>
            <span class="stat-value">{team_data.get('過去10試合OPS', '---')}</span>
        </div>
    </div>
    '''
    
    return html

def convert_to_html(text_file, output_file=None):
    """メイン変換関数"""
    # ファイル読み込み
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 出力ファイル名の決定
    if not output_file:
        base_name = Path(text_file).stem
        output_file = f"daily_reports/html/{base_name}.html"
    
    # 出力ディレクトリ作成
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    # 試合を抽出
    game_pattern = r'\*\*([^*]+) @ ([^*]+)\*\*'
    matches = list(re.finditer(game_pattern, content))
    
    games_html = []
    for i, match in enumerate(matches):
        next_match = matches[i + 1] if i + 1 < len(matches) else None
        game_data = parse_game(content, match, next_match)
        games_html.append(create_html_page(game_data))
        
        # デバッグ出力
        print(f"処理: {game_data['away_team']} @ {game_data['home_team']}")
    
    # 完全なHTML文書を生成
    html_document = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB レポート</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .page {{
            width: 210mm;
            min-height: 297mm;
            padding: 15mm 20mm;
            margin: 10mm auto;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            page-break-after: always;
            display: flex;
            flex-direction: column;
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #e0e0e0;
        }}
        
        .team-header {{
            flex: 1;
            text-align: center;
        }}
        
        .game-info {{
            flex: 0.5;
            text-align: center;
        }}
        
        .team-logo-img {{
            width: 60px;
            height: 60px;
            object-fit: contain;
            margin-bottom: 8px;
        }}
        
        .team-name {{
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin: 5px 0;
        }}
        
        .pitcher-name {{
            font-size: 14px;
            color: #555;
            margin: 5px 0;
        }}
        
        .date-time {{
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .time-label {{
            font-size: 12px;
            color: #666;
        }}
        
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            flex-grow: 1;
            margin: 20px 0;
        }}
        
        .team-column {{
            padding: 0 10px;
        }}
        
        .stats-category {{
            margin-bottom: 20px;
        }}
        
        .stats-title {{
            font-size: 14px;
            font-weight: bold;
            color: #1e3a8a;
            padding-bottom: 6px;
            margin-bottom: 8px;
            border-bottom: 2px solid #93c5fd;
        }}
        
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 12px;
        }}
        
        .stat-label {{
            color: #666;
        }}
        
        .stat-value {{
            font-weight: bold;
            color: #2c3e50;
            font-family: 'Courier New', monospace;
        }}
        
        .stat-value.highlight {{
            color: #ef4444;
            font-size: 13px;
        }}
        
        .summary-section {{
            margin-top: auto;
            padding-top: 15px;
            border-top: 3px solid #333;
        }}
        
        .summary-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        
        .summary-text {{
            font-size: 13px;
            line-height: 1.6;
            color: #444;
        }}
        
        .fatigue-warning {{
            color: #ef4444;
            font-weight: bold;
        }}
        
        @media print {{
            .page {{
                margin: 0;
                box-shadow: none;
                page-break-after: always;
            }}
            
            body {{
                background: white;
            }}
        }}
    </style>
</head>
<body>
    {''.join(games_html)}
</body>
</html>'''
    
    # HTMLファイル書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_document)
    
    print(f"\n✅ HTML レポートを生成しました: {output_file}")
    print(f"   - {len(games_html)} 試合を処理")
    
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python convert_to_html.py <input.txt> [output.html]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"エラー: ファイルが見つかりません: {input_file}")
        sys.exit(1)
    
    convert_to_html(input_file, output_file)