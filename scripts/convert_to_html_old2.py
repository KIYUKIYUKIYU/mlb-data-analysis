#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBレポートをHTMLに変換するスクリプト（完全修正版）
- 15試合対応
- データ欠損に強い
- 1試合1ページレイアウト
"""

import re
import os
from pathlib import Path
from datetime import datetime

def parse_report(file_path):
    """レポートをパースして試合データを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # セクションごとに分割
    sections = content.split('=' * 60)
    
    games = []
    
    # 各セクションを処理
    for i in range(len(sections)):
        section = sections[i]
        
        # 試合情報を探す（複数のパターンに対応）
        patterns = [
            r'([A-Za-z\s.]+?)\s*@\s*([A-Za-z\s.]+)',
            r'(.+?)\s*@\s*(.+?)\n'
        ]
        
        match = None
        for pattern in patterns:
            match = re.search(pattern, section)
            if match:
                break
        
        if not match:
            continue
        
        away_team = match.group(1).strip()
        home_team = match.group(2).strip()
        
        # 開始時刻を探す
        time_match = re.search(r'開始時刻:\s*(\d+/\d+\s+\d+:\d+)', section)
        start_time = time_match.group(1) if time_match else ''
        
        # チームデータを収集
        game_content = section
        if i + 1 < len(sections):
            next_section = sections[i + 1]
            # 次のセクションに新しい試合情報がなければ含める
            if not re.search(r'([A-Za-z\s.]+?)\s*@\s*([A-Za-z\s.]+)', next_section):
                game_content += next_section
        
        # away_dataとhome_dataを作成
        away_data = parse_team_data(game_content, away_team, is_away=True)
        home_data = parse_team_data(game_content, home_team, is_away=False)
        
        # ゲームデータを作成
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
    """チームデータをパース"""
    data = {
        'team': team_name,
        'pitcher': {},
        'bullpen': {},
        'batting': {}
    }
    
    # チームセクションを探す
    team_sections = re.split(r'【(.+?)】', content)
    
    for j in range(1, len(team_sections), 2):
        if j >= len(team_sections):
            break
        
        section_team = team_sections[j]
        section_content = team_sections[j+1] if j+1 < len(team_sections) else ""
        
        # このセクションが対象チームか確認
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
            
            # ERA, FIP等の統計
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
        
        # OPSは別途処理（過去試合OPSと区別するため）
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
        
        break  # 該当チームのデータを見つけたら終了
    
    return data

def safe_get(data, *keys, default='---'):
    """安全にネストされたデータを取得"""
    try:
        result = data
        for key in keys:
            result = result[key]
        return result if result else default
    except (KeyError, TypeError):
        return default

def create_team_stats(team_data):
    """チーム統計のHTML生成"""
    pitcher = team_data.get('pitcher', {})
    bullpen = team_data.get('bullpen', {})
    batting = team_data.get('batting', {})
    
    # 投手の利き腕表示
    pitcher_hand = f"({pitcher.get('hand', '')})" if pitcher.get('hand') else ''
    
    html = f"""
    <div class="team-stats">
        <h3>{team_data.get('team', 'Unknown Team')}</h3>
        
        <div class="stat-section">
            <h4>先発投手</h4>
            <div class="pitcher-name">
                {pitcher.get('name', '未定')} {pitcher_hand}
                ({pitcher.get('wins', '0')}勝{pitcher.get('losses', '0')}敗)
            </div>
            <div class="stat-grid">
                <div class="stat-row">
                    <span class="stat-label">ERA / FIP / xFIP</span>
                    <span class="stat-value">
                        <strong>{pitcher.get('era', '---')} / {pitcher.get('fip', '---')} / {pitcher.get('xfip', '---')}</strong>
                    </span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">WHIP</span>
                    <span class="stat-value"><strong>{pitcher.get('whip', '---')}</strong></span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">K-BB%</span>
                    <span class="stat-value"><strong>{pitcher.get('k_bb', '---')}</strong>%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">対左/右 OPS</span>
                    <span class="stat-value">
                        <strong>{pitcher.get('vs_left_ops', '---')} / {pitcher.get('vs_right_ops', '---')}</strong>
                    </span>
                </div>
            </div>
        </div>
        
        <div class="stat-section">
            <h4>中継ぎ陣 ({bullpen.get('count', '?')}名)</h4>
            <div class="stat-grid">
                <div class="stat-row">
                    <span class="stat-label">ERA / FIP / xFIP</span>
                    <span class="stat-value">
                        <strong>{bullpen.get('era', '---')} / {bullpen.get('fip', '---')} / {bullpen.get('xfip', '---')}</strong>
                    </span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">WHIP</span>
                    <span class="stat-value"><strong>{bullpen.get('whip', '---')}</strong></span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">K-BB%</span>
                    <span class="stat-value"><strong>{bullpen.get('k_bb', '---')}</strong>%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">疲労度</span>
                    <span class="stat-value"><strong>{bullpen.get('fatigue', '---')}</strong></span>
                </div>
            </div>
        </div>
        
        <div class="stat-section">
            <h4>攻撃</h4>
            <div class="stat-grid">
                <div class="stat-row">
                    <span class="stat-label">AVG / OPS</span>
                    <span class="stat-value">
                        <strong>{batting.get('avg', '---')} / {batting.get('ops', '---')}</strong>
                    </span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">wOBA / xwOBA</span>
                    <span class="stat-value">
                        <strong>{batting.get('woba', '---')} / {batting.get('xwoba', '---')}</strong>
                    </span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">対左/右 OPS</span>
                    <span class="stat-value">
                        <strong>{batting.get('vs_left_ops', '---')} / {batting.get('vs_right_ops', '---')}</strong>
                    </span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">過去5試合 OPS</span>
                    <span class="stat-value"><strong>{batting.get('ops_5', '---')}</strong></span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">過去10試合 OPS</span>
                    <span class="stat-value"><strong>{batting.get('ops_10', '---')}</strong></span>
                </div>
            </div>
        </div>
    </div>
    """
    return html

def create_html_page(game_data):
    """1試合分のHTMLページを生成"""
    html = f"""
    <div class="game-page">
        <div class="game-header">
            <h2>{game_data['away_team']} @ {game_data['home_team']}</h2>
            <div class="start-time">開始時刻: {game_data.get('start_time', '未定')} (日本時間)</div>
        </div>
        
        <div class="teams-container">
            <div class="team-column away-team">
                {create_team_stats(game_data['away_data'])}
            </div>
            
            <div class="vs-divider">
                <div class="vs-text">VS</div>
            </div>
            
            <div class="team-column home-team">
                {create_team_stats(game_data['home_data'])}
            </div>
        </div>
        
        <div class="game-footer">
            <h3>総括</h3>
            <p>両チームが拮抗しており、接戦が予想される。ホームの{game_data['home_team']}にわずかながらアドバンテージがある。</p>
        </div>
    </div>
    """
    return html

def create_css():
    """CSSスタイルシートを生成"""
    return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Helvetica Neue', Arial, 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .report-header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
        }
        
        .report-header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        
        .game-page {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            page-break-after: always;
        }
        
        .game-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }
        
        .game-header h2 {
            color: #333;
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .start-time {
            color: #666;
            font-size: 1.1em;
        }
        
        .teams-container {
            display: flex;
            justify-content: space-between;
            align-items: stretch;
            margin-bottom: 30px;
            gap: 20px;
        }
        
        .team-column {
            flex: 1;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
        }
        
        .away-team {
            border: 2px solid #4a90e2;
        }
        
        .home-team {
            border: 2px solid #e74c3c;
        }
        
        .vs-divider {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 60px;
        }
        
        .vs-text {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 10px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 1.2em;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .team-stats h3 {
            color: #333;
            font-size: 1.4em;
            margin-bottom: 20px;
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 10px;
        }
        
        .stat-section {
            margin-bottom: 25px;
        }
        
        .stat-section h4 {
            color: #667eea;
            font-size: 1.1em;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .pitcher-name {
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .stat-grid {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            background: white;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .stat-row:hover {
            background: #f0f0f0;
            transform: translateX(5px);
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .stat-value {
            color: #333;
            font-size: 1em;
        }
        
        .stat-value strong {
            color: #667eea;
            font-weight: bold;
        }
        
        .game-footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
            border: 2px solid #ddd;
        }
        
        .game-footer h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .game-footer p {
            color: #666;
            line-height: 1.6;
        }
        
        @media print {
            body {
                background: white;
            }
            
            .game-page {
                box-shadow: none;
                border: 1px solid #ddd;
            }
        }
        
        @media (max-width: 768px) {
            .teams-container {
                flex-direction: column;
            }
            
            .vs-divider {
                width: 100%;
                height: 60px;
            }
        }
    </style>
    """

def convert_to_html(input_file, output_file=None):
    """メイン変換処理"""
    # 出力ファイル名を決定
    if output_file is None:
        base_name = Path(input_file).stem
        output_dir = Path("daily_reports/html")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{base_name}.html"
    
    # レポートをパース
    games = parse_report(input_file)
    
    print(f"見つかった試合数: {len(games)}")
    
    if not games:
        print("エラー: 試合データが見つかりませんでした")
        return
    
    # 日付を取得
    date_match = re.search(r'(\d+月\d+日)', str(input_file))
    date_str = date_match.group(1) if date_match else datetime.now().strftime('%m月%d日')
    
    # HTML生成
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MLB試合予想レポート - {date_str}</title>
        {create_css()}
    </head>
    <body>
        <div class="container">
            <div class="report-header">
                <h1>⚾ MLB試合予想レポート</h1>
                <p>{date_str} - 全{len(games)}試合</p>
            </div>
    """
    
    # 各試合のHTMLを追加
    for i, game in enumerate(games):
        html_content += create_html_page(game)
        if i < len(games) - 1:
            html_content += '<div style="page-break-after: always;"></div>'
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # ファイルに保存
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