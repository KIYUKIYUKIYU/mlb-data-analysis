#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB レポート HTML変換スクリプト
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
        'Yankees': '147', 'Red Sox': '111', 'Blue Jays': '141', 'Rays': '139', 'Orioles': '110',
        'White Sox': '145', 'Guardians': '114', 'Tigers': '116', 'Royals': '118', 'Twins': '142',
        'Astros': '117', 'Athletics': '133', 'Mariners': '136', 'Angels': '108', 'Rangers': '140',
        'Braves': '144', 'Marlins': '146', 'Mets': '121', 'Phillies': '143', 'Nationals': '120',
        'Brewers': '158', 'Cardinals': '138', 'Cubs': '112', 'Reds': '113', 'Pirates': '134',
        'Dodgers': '119', 'Diamondbacks': '109', 'Rockies': '115', 'Padres': '135', 'Giants': '137'
    }
    
    # MLB公式のロゴURL（高品質SVG）
    team_id = team_ids.get(team_name)
    if team_id:
        return f"https://www.mlbstatic.com/team-logos/{team_id}.svg"
    else:
        # フォールバック：ESPNのロゴ
        team_abbr = {
            'Yankees': 'nyy', 'Red Sox': 'bos', 'Blue Jays': 'tor', 'Rays': 'tb', 'Orioles': 'bal',
            'White Sox': 'cws', 'Guardians': 'cle', 'Tigers': 'det', 'Royals': 'kc', 'Twins': 'min',
            'Astros': 'hou', 'Athletics': 'oak', 'Mariners': 'sea', 'Angels': 'laa', 'Rangers': 'tex',
            'Braves': 'atl', 'Marlins': 'mia', 'Mets': 'nym', 'Phillies': 'phi', 'Nationals': 'wsh',
            'Brewers': 'mil', 'Cardinals': 'stl', 'Cubs': 'chc', 'Reds': 'cin', 'Pirates': 'pit',
            'Dodgers': 'lad', 'Diamondbacks': 'ari', 'Rockies': 'col', 'Padres': 'sd', 'Giants': 'sf'
        }
        abbr = team_abbr.get(team_name, 'mlb')
        return f"https://a.espncdn.com/i/teamlogos/mlb/500/{abbr}.png"

def parse_game_section(section_text):
    """試合セクションをパース（改良版）"""
    game_data = {
        'teams': {},
        'time': '',
        'date': ''
    }
    
    lines = section_text.strip().split('\n')
    
    # チーム名と開始時刻を抽出
    for line in lines:
        if ' @ ' in line or ' vs ' in line:
            teams = re.split(r' @ | vs ', line)
            if len(teams) >= 2:
                game_data['away_team'] = teams[0].strip().replace('**', '').strip()
                game_data['home_team'] = teams[1].strip().replace('**', '').strip()
        elif '開始時刻:' in line or '開始時間:' in line:
            time_match = re.search(r'(\d+/\d+ \d+:\d+)', line)
            if time_match:
                game_data['time'] = time_match.group(1)
    
    # 各チームのデータを抽出
    team_sections = re.split(r'【(.+?)】', section_text)
    
    for i in range(1, len(team_sections), 2):
        if i < len(team_sections):
            team_name = team_sections[i].strip()
            team_data = team_sections[i + 1] if i + 1 < len(team_sections) else ''
            
            # 投手データ
            pitcher_info = {}
            pitcher_match = re.search(r'(?:\*\*)?先発(?:\*\*)?[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)', team_data)
            
            if pitcher_match:
                pitcher_info['name'] = pitcher_match.group(1)
                pitcher_info['record'] = pitcher_match.group(2)
            elif '先発: 未定' in team_data or '先発投手 未定' in team_data:
                pitcher_info['name'] = '未定'
                pitcher_info['record'] = ''
            
            # 統計データを詳細に抽出
            stats = {}
            
            # 投手統計
            for pattern, key in [
                (r'ERA:\s*([\d.]+)', 'ERA'),
                (r'FIP:\s*([\d.]+)', 'FIP'),
                (r'xFIP:\s*([\d.]+)', 'xFIP'),
                (r'WHIP:\s*([\d.]+)', 'WHIP'),
                (r'K-BB%:\s*([\d.]+)%?', 'K-BB%'),
                (r'GB%:\s*([\d.]+)%?', 'GB%'),
                (r'FB%:\s*([\d.]+)%?', 'FB%'),
                (r'QS率:\s*([\d.]+)%?', 'QS率'),
                (r'SwStr%:\s*([\d.]+)%?', 'SwStr%'),
                (r'BABIP:\s*([\d.]+)', 'BABIP')
            ]:
                match = re.search(pattern, team_data)
                if match:
                    stats[key] = match.group(1)
            
            # 対左右成績
            vs_match = re.search(r'対左:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)\s*\|\s*対右:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', team_data)
            if vs_match:
                stats['対左OPS'] = vs_match.group(2)
                stats['対右OPS'] = vs_match.group(4)
            
            # ブルペン統計
            bp_match = re.search(r'中継ぎ陣\s*\((\d+)名\)', team_data)
            if bp_match:
                stats['bp_count'] = bp_match.group(1)
                
            # ブルペンのERA/FIP/xFIP（別の行にある場合）
            bp_stats_lines = team_data.split('\n')
            in_bullpen = False
            for line in bp_stats_lines:
                if '中継ぎ陣' in line:
                    in_bullpen = True
                elif in_bullpen and 'ERA:' in line:
                    bp_era_match = re.search(r'ERA:\s*([\d.]+)\s*\|\s*FIP:\s*([\d.]+)\s*\|\s*xFIP:\s*([\d.]+)', line)
                    if bp_era_match:
                        stats['bp_ERA'] = bp_era_match.group(1)
                        stats['bp_FIP'] = bp_era_match.group(2)
                        stats['bp_xFIP'] = bp_era_match.group(3)
                elif in_bullpen and 'WHIP:' in line:
                    bp_whip_match = re.search(r'WHIP:\s*([\d.]+)', line)
                    if bp_whip_match:
                        stats['bp_WHIP'] = bp_whip_match.group(1)
                elif in_bullpen and '疲労度:' in line:
                    stats['bp_fatigue'] = line.split('疲労度:')[1].strip()
                elif 'チーム打撃' in line or '攻撃' in line:
                    in_bullpen = False
            
            # チーム打撃データ
            for pattern, key in [
                (r'AVG:\s*([\d.]+)', 'AVG'),
                (r'OPS:\s*([\d.]+)', 'OPS'),
                (r'wOBA:\s*([\d.]+)', 'wOBA'),
                (r'xwOBA:\s*([\d.]+)', 'xwOBA'),
                (r'Barrel%:\s*([\d.]+)%?', 'Barrel%'),
                (r'Hard-Hit%:\s*([\d.]+)%?', 'Hard-Hit%')
            ]:
                match = re.search(pattern, team_data)
                if match:
                    stats[key] = match.group(1)
            
            # 過去試合OPS
            for days in [5, 10]:
                pattern = rf'過去{days}試合OPS:\s*([\d.]+)'
                match = re.search(pattern, team_data)
                if match:
                    stats[f'過去{days}試合OPS'] = match.group(1)
            
            # 対左右投手成績
            bat_vs_match = re.search(r'対左投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)\s*\|\s*対右投手:\s*([\d.]+)\s*\(OPS\s*([\d.]+)\)', team_data)
            if bat_vs_match:
                stats['bat_vs_L'] = bat_vs_match.group(2)
                stats['bat_vs_R'] = bat_vs_match.group(4)
            
            game_data['teams'][team_name] = {
                'pitcher': pitcher_info,
                'stats': stats,
                'logo': get_team_logo(team_name)
            }
    
    # 総括を生成
    if game_data.get('away_team') and game_data.get('home_team'):
        game_data['summary'] = generate_summary(game_data)
    
    return game_data

def generate_summary(game_data):
    """試合の総括を生成"""
    away_team = game_data.get('away_team')
    home_team = game_data.get('home_team')
    
    if not away_team or not home_team:
        return "データ不足のため分析できません。"
    
    away_data = game_data['teams'].get(away_team, {})
    home_data = game_data['teams'].get(home_team, {})
    
    away_stats = away_data.get('stats', {})
    home_stats = home_data.get('stats', {})
    
    # スコア計算（簡易版）
    score_factors = []
    
    # 先発投手の比較
    try:
        away_xfip = float(away_stats.get('xFIP', 99))
        home_xfip = float(home_stats.get('xFIP', 99))
        if away_xfip < home_xfip - 0.5:
            score_factors.append(f"先発投手では{away_team}が優位")
        elif home_xfip < away_xfip - 0.5:
            score_factors.append(f"先発投手では{home_team}が優位")
    except:
        pass
    
    # ブルペンの比較
    try:
        away_bp_fip = float(away_stats.get('bp_FIP', 99))
        home_bp_fip = float(home_stats.get('bp_FIP', 99))
        if away_bp_fip < home_bp_fip - 0.3:
            score_factors.append(f"ブルペンは{away_team}が質で上回る")
        elif home_bp_fip < away_bp_fip - 0.3:
            score_factors.append(f"ブルペンは{home_team}が質で上回る")
    except:
        pass
    
    # 打線の勢いを比較
    try:
        away_ops = float(away_stats.get('過去10試合OPS', 0))
        home_ops = float(home_stats.get('過去10試合OPS', 0))
        if away_ops > home_ops + 0.05:
            score_factors.append(f"{away_team}打線が好調（OPS {away_ops:.3f}）")
        elif home_ops > away_ops + 0.05:
            score_factors.append(f"{home_team}打線が好調（OPS {home_ops:.3f}）")
    except:
        pass
    
    # 疲労度チェック
    if '連投中' in str(away_stats.get('bp_fatigue', '')):
        score_factors.append(f"{away_team}のブルペンに疲労が見られる")
    if '連投中' in str(home_stats.get('bp_fatigue', '')):
        score_factors.append(f"{home_team}のブルペンに疲労が見られる")
    
    if score_factors:
        summary = "。".join(score_factors) + "。"
    else:
        summary = "両チームが拮抗しており、接戦が予想される。"
    
    # ホームアドバンテージを追加
    summary += f"ホームの{home_team}にわずかながらアドバンテージがある。"
    
    return summary

def create_team_section_improved(team_data, title='先発投手'):
    """改良版チームセクションのHTML生成"""
    pitcher = team_data.get('pitcher', {})
    stats = team_data.get('stats', {})
    
    html = ''
    
    # 先発投手セクション
    if pitcher.get('name') and pitcher.get('name') != '未定':
        html += f'''
        <div class="stats-category">
            <h3 class="stats-title">先発投手</h3>
            <div class="stat-row">
                <span class="stat-label">ERA / FIP / xFIP</span>
                <span class="stat-value">{stats.get('ERA', '---')} / {stats.get('FIP', '---')} / {stats.get('xFIP', '---')}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">WHIP</span>
                <span class="stat-value">{stats.get('WHIP', '---')}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">K-BB%</span>
                <span class="stat-value">{stats.get('K-BB%', '---')}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">GB% / FB%</span>
                <span class="stat-value">{stats.get('GB%', '---')}% / {stats.get('FB%', '---')}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">QS率</span>
                <span class="stat-value">{stats.get('QS率', '---')}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">対左/右 OPS</span>
                <span class="stat-value">{stats.get('対左OPS', '---')} / {stats.get('対右OPS', '---')}</span>
            </div>
        </div>
        '''
    
    # 中継ぎ陣セクション
    html += f'''
    <div class="stats-category">
        <h3 class="stats-title">中継ぎ陣 ({stats.get('bp_count', '?')}名)</h3>
        <div class="stat-row">
            <span class="stat-label">ERA / FIP / xFIP</span>
            <span class="stat-value">{stats.get('bp_ERA', '---')} / {stats.get('bp_FIP', '---')} / {stats.get('bp_xFIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">WHIP</span>
            <span class="stat-value">{stats.get('bp_WHIP', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">K-BB%</span>
            <span class="stat-value">{stats.get('bp_K-BB%', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">疲労度</span>
            <span class="stat-value {'fatigue-warning' if '連投中' in str(stats.get('bp_fatigue', '')) else ''}">{stats.get('bp_fatigue', '---')}</span>
        </div>
    </div>
    '''
    
    # 攻撃セクション
    html += f'''
    <div class="stats-category">
        <h3 class="stats-title">攻撃</h3>
        <div class="stat-row">
            <span class="stat-label">AVG / OPS</span>
            <span class="stat-value">{stats.get('AVG', '---')} / {stats.get('OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">wOBA / xwOBA</span>
            <span class="stat-value">{stats.get('wOBA', '---')} / {stats.get('xwOBA', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">対左/右 OPS</span>
            <span class="stat-value">{stats.get('bat_vs_L', '---')} / {stats.get('bat_vs_R', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">過去5試合 OPS</span>
            <span class="stat-value {'highlight' if stats.get('過去5試合OPS') and float(stats.get('過去5試合OPS', 0)) >= 0.8 else ''}">{stats.get('過去5試合OPS', '---')}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">過去10試合 OPS</span>
            <span class="stat-value {'highlight' if stats.get('過去10試合OPS') and float(stats.get('過去10試合OPS', 0)) >= 0.8 else ''}">{stats.get('過去10試合OPS', '---')}</span>
        </div>
    </div>
    '''
    
    return html

def create_html_page(game_data):
    """1試合分のHTMLページを生成"""
    away_team = game_data.get('away_team', 'Away')
    home_team = game_data.get('home_team', 'Home')
    
    away_data = game_data['teams'].get(away_team, {})
    home_data = game_data['teams'].get(home_team, {})
    
    # 投手の利き腕を取得
    away_pitcher = away_data.get('pitcher', {})
    home_pitcher = home_data.get('pitcher', {})
    
    # 利き腕の表示（右=赤、左=青）
    def get_hand_badge(pitcher_name):
        if not pitcher_name or pitcher_name == '未定':
            return ''
        # デフォルトは右投げ（実際のデータから取得する必要がある）
        hand = 'R'
        if hand == 'L':
            return '<span class="badge-left">左</span>'
        else:
            return '<span class="badge-right">右</span>'
    
    html = f'''
    <div class="page">
        <!-- ヘッダー -->
        <div class="header-top">
            <div class="team-header">
                <img src="{away_data.get('logo', '')}" alt="{away_team}" class="team-logo-img">
                <h2 class="team-name">{away_team}</h2>
                <div class="pitcher-name">{away_pitcher.get('name', '未定')} {away_pitcher.get('record', '')}</div>
                {get_hand_badge(away_pitcher.get('name'))}
            </div>
            
            <div class="game-info">
                <div class="date-time">{game_data.get('time', '')}</div>
                <div class="time-label">日本時間</div>
            </div>
            
            <div class="team-header">
                <img src="{home_data.get('logo', '')}" alt="{home_team}" class="team-logo-img">
                <h2 class="team-name">{home_team}</h2>
                <div class="pitcher-name">{home_pitcher.get('name', '未定')} {home_pitcher.get('record', '')}</div>
                {get_hand_badge(home_pitcher.get('name'))}
            </div>
        </div>
        
        <!-- メインコンテンツ -->
        <div class="main-content">
            <div class="team-column">
                {create_team_section_improved(away_data, '先発投手')}
            </div>
            
            <div class="team-column">
                {create_team_section_improved(home_data, '先発投手')}
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
    
    # 試合セクションを分割
    game_sections = re.split(r'={40,}', content)
    games_html = []
    
    for section in game_sections:
        if '@' in section or ' vs ' in section:
            game_data = parse_game_section(section)
            if game_data.get('away_team') and game_data.get('home_team'):
                games_html.append(create_html_page(game_data))
    
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
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin: 5px 0;
        }}
        
        .pitcher-name {{
            font-size: 16px;
            color: #555;
            margin: 5px 0;
        }}
        
        .badge-right {{
            display: inline-block;
            background: #ef4444;
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 5px;
        }}
        
        .badge-left {{
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 5px;
        }}
        
        .date-time {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .time-label {{
            font-size: 14px;
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
            margin-bottom: 25px;
        }}
        
        .stats-title {{
            font-size: 16px;
            font-weight: bold;
            color: #1e3a8a;
            padding-bottom: 8px;
            margin-bottom: 10px;
            border-bottom: 2px solid #93c5fd;
        }}
        
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
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
            font-size: 15px;
        }}
        
        .summary-section {{
            margin-top: auto;
            padding-top: 20px;
            border-top: 3px solid #333;
        }}
        
        .summary-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .summary-text {{
            font-size: 14px;
            line-height: 1.8;
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
    
    print(f"✅ HTML レポートを生成しました: {output_file}")
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