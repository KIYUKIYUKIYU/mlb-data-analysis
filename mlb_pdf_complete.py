import os
import sys
from datetime import datetime, timedelta
import pytz
import pdfkit
from pathlib import Path
import requests
import time

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 既存のdiscord_report_with_tableから必要な部分をインポート
try:
    from src.mlb_api_client import MLBApiClient
    api_client = MLBApiClient()
except:
    api_client = None

class MLBPDFComplete:
    def __init__(self):
        self.wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        self.config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        
        # PDFオプション（重要：local file accessを有効に）
        self.options = {
            'page-size': 'A4',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'enable-local-file-access': '',
            'no-outline': None,
            'print-media-type': None,
            'dpi': 300
        }
        
        # チームマッピング（完全版）
        self.team_mappings = {
            'Baltimore Orioles': {'abbr': 'BAL', 'logo_id': '110', 'color': '#DF4601'},
            'New York Yankees': {'abbr': 'NYY', 'logo_id': '147', 'color': '#003087'},
            'Detroit Tigers': {'abbr': 'DET', 'logo_id': '116', 'color': '#0C2340'},
            'Tampa Bay Rays': {'abbr': 'TB', 'logo_id': '139', 'color': '#092C5C'},
            'Milwaukee Brewers': {'abbr': 'MIL', 'logo_id': '158', 'color': '#0A2351'},
            'Minnesota Twins': {'abbr': 'MIN', 'logo_id': '142', 'color': '#002B5C'},
            'Boston Red Sox': {'abbr': 'BOS', 'logo_id': '111', 'color': '#BD3039'},
            'Toronto Blue Jays': {'abbr': 'TOR', 'logo_id': '141', 'color': '#134A8E'},
            'Chicago White Sox': {'abbr': 'CWS', 'logo_id': '145', 'color': '#27251F'},
            'Kansas City Royals': {'abbr': 'KC', 'logo_id': '118', 'color': '#004687'},
            'Houston Astros': {'abbr': 'HOU', 'logo_id': '117', 'color': '#002D62'},
            'Texas Rangers': {'abbr': 'TEX', 'logo_id': '140', 'color': '#003278'},
            'Oakland Athletics': {'abbr': 'OAK', 'logo_id': '133', 'color': '#003831'},
            'Seattle Mariners': {'abbr': 'SEA', 'logo_id': '136', 'color': '#0C2C56'},
            'Los Angeles Angels': {'abbr': 'LAA', 'logo_id': '108', 'color': '#BA0021'},
            'New York Mets': {'abbr': 'NYM', 'logo_id': '121', 'color': '#002D72'},
            'Philadelphia Phillies': {'abbr': 'PHI', 'logo_id': '143', 'color': '#E81828'},
            'Washington Nationals': {'abbr': 'WSH', 'logo_id': '120', 'color': '#AB0003'},
            'Miami Marlins': {'abbr': 'MIA', 'logo_id': '146', 'color': '#00A3E0'},
            'Atlanta Braves': {'abbr': 'ATL', 'logo_id': '144', 'color': '#CE1141'},
            'Chicago Cubs': {'abbr': 'CHC', 'logo_id': '112', 'color': '#0E3386'},
            'Cincinnati Reds': {'abbr': 'CIN', 'logo_id': '113', 'color': '#C6011F'},
            'Pittsburgh Pirates': {'abbr': 'PIT', 'logo_id': '134', 'color': '#FDB827'},
            'St. Louis Cardinals': {'abbr': 'STL', 'logo_id': '138', 'color': '#C41E3A'},
            'Arizona Diamondbacks': {'abbr': 'ARI', 'logo_id': '109', 'color': '#A71930'},
            'Colorado Rockies': {'abbr': 'COL', 'logo_id': '115', 'color': '#33006F'},
            'Los Angeles Dodgers': {'abbr': 'LAD', 'logo_id': '119', 'color': '#005A9C'},
            'San Diego Padres': {'abbr': 'SD', 'logo_id': '135', 'color': '#2F241D'},
            'San Francisco Giants': {'abbr': 'SF', 'logo_id': '137', 'color': '#FD5A1E'},
            'Cleveland Guardians': {'abbr': 'CLE', 'logo_id': '114', 'color': '#00385D'}
        }
    
    def get_games_for_date(self, date):
        """指定日の試合データを取得"""
        url = f"https://statsapi.mlb.com/api/v1/schedule?date={date}&sportId=1&hydrate=probablePitcher,person,team,stats,flags,linescore,decisions"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching games: {e}")
            return None
    
    def get_pitcher_season_stats(self, pitcher_id):
        """投手のシーズン統計を取得"""
        if not pitcher_id:
            return None
            
        url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=season&season=2025&group=pitching"
        try:
            response = requests.get(url)
            data = response.json()
            
            if 'stats' in data and data['stats']:
                for stat_group in data['stats']:
                    if stat_group.get('group', {}).get('displayName') == 'pitching':
                        if 'splits' in stat_group and stat_group['splits']:
                            stats = stat_group['splits'][0].get('stat', {})
                            return {
                                'wins': stats.get('wins', 0),
                                'losses': stats.get('losses', 0),
                                'era': stats.get('era', '0.00'),
                                'whip': stats.get('whip', '0.00'),
                                'strikeouts': stats.get('strikeOuts', 0),
                                'walks': stats.get('baseOnBalls', 0),
                                'innings': stats.get('inningsPitched', '0.0'),
                                'k9': stats.get('strikeoutsPer9Inn', '0.0'),
                                'bb9': stats.get('walksPer9Inn', '0.0')
                            }
        except Exception as e:
            print(f"Error fetching pitcher stats: {e}")
        
        return None
    
    def calculate_k_bb_percent(self, stats):
        """K-BB%を計算"""
        if not stats:
            return 0.0
        
        try:
            k9 = float(stats.get('k9', 0))
            bb9 = float(stats.get('bb9', 0))
            # K-BB%の簡易計算（K/9 - BB/9）
            return round(k9 - bb9, 1)
        except:
            return 0.0
    
    def calculate_bar_widths(self, val1, val2, inverse=False):
        """バーグラフの幅を計算"""
        try:
            val1 = float(val1) if val1 else 0
            val2 = float(val2) if val2 else 0
            
            # 両方0の場合
            if val1 == 0 and val2 == 0:
                return "45%", "45%"
            
            # inverseの場合（低い方が良い指標）
            if inverse:
                # 値を反転（大きい値を小さく見せる）
                if val1 == 0:
                    val1 = 10  # 0の場合は大きな値として扱う
                if val2 == 0:
                    val2 = 10
                
                # 比率を反転
                total = (1/val1) + (1/val2)
                width1 = ((1/val1) / total) * 90
                width2 = ((1/val2) / total) * 90
            else:
                # 通常の場合（高い方が良い指標）
                total = val1 + val2
                if total == 0:
                    return "45%", "45%"
                width1 = (val1 / total) * 90
                width2 = (val2 / total) * 90
            
            # 最小幅を確保
            width1 = max(width1, 20)
            width2 = max(width2, 20)
            
            return f"{width1:.0f}%", f"{width2:.0f}%"
            
        except Exception as e:
            print(f"Error calculating widths: {e}")
            return "45%", "45%"
    
    def generate_complete_html(self, game_data):
        """完全なHTMLを生成（実データ付き）"""
        # 基本情報を取得
        away_team = game_data['teams']['away']['team']['name']
        home_team = game_data['teams']['home']['team']['name']
        
        # チーム情報を取得
        away_info = self.team_mappings.get(away_team, {'abbr': 'UNK', 'logo_id': '120', 'color': '#000000'})
        home_info = self.team_mappings.get(home_team, {'abbr': 'UNK', 'logo_id': '120', 'color': '#000000'})
        
        # 日時をフォーマット
        game_date = datetime.fromisoformat(game_data['gameDate'])
        jst = pytz.timezone('Asia/Tokyo')
        game_date_jst = game_date.astimezone(jst)
        
        # 先発投手情報を取得
        away_pitcher_name = "TBA"
        home_pitcher_name = "TBA"
        away_pitcher_id = None
        home_pitcher_id = None
        
        if 'probablePitcher' in game_data['teams']['away']:
            pitcher = game_data['teams']['away']['probablePitcher']
            away_pitcher_name = pitcher.get('fullName', 'TBA')
            away_pitcher_id = pitcher.get('id')
        
        if 'probablePitcher' in game_data['teams']['home']:
            pitcher = game_data['teams']['home']['probablePitcher']
            home_pitcher_name = pitcher.get('fullName', 'TBA')
            home_pitcher_id = pitcher.get('id')
        
        # 投手の統計を取得
        away_pitcher_stats = self.get_pitcher_season_stats(away_pitcher_id) if away_pitcher_id else None
        home_pitcher_stats = self.get_pitcher_season_stats(home_pitcher_id) if home_pitcher_id else None
        
        # デフォルト値
        away_stats = away_pitcher_stats or {'wins': 0, 'losses': 0, 'era': '-.--', 'whip': '-.--', 'k9': 0, 'bb9': 0}
        home_stats = home_pitcher_stats or {'wins': 0, 'losses': 0, 'era': '-.--', 'whip': '-.--', 'k9': 0, 'bb9': 0}
        
        # K-BB%を計算
        away_k_bb = self.calculate_k_bb_percent(away_stats)
        home_k_bb = self.calculate_k_bb_percent(home_stats)
        
        # バーグラフの幅を計算
        era_width_away, era_width_home = self.calculate_bar_widths(away_stats['era'], home_stats['era'], inverse=True)
        whip_width_away, whip_width_home = self.calculate_bar_widths(away_stats['whip'], home_stats['whip'], inverse=True)
        kbb_width_away, kbb_width_home = self.calculate_bar_widths(away_k_bb, home_k_bb, inverse=False)
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB Matchup Analysis: {away_team} vs {home_team}</title>
    <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial', 'Helvetica', sans-serif;
            background-color: #e2e8f0;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            margin: 0;
            padding: 0;
        }}

        #a4-page {{
            width: 210mm;
            height: 297mm;
            background-color: white;
            margin: 0 auto;
            padding: 20mm;
            position: relative;
        }}

        /* ヘッダー */
        header {{
            text-align: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        
        h1 {{
            font-size: 28px;
            font-weight: bold;
            color: #1a202c;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }}
        
        .date {{
            color: #718096;
            font-size: 14px;
        }}
        
        /* チームヘッダー */
        .team-header {{
            display: table;
            width: 100%;
            margin-bottom: 30px;
        }}
        
        .team-info {{
            display: table-cell;
            width: 50%;
            vertical-align: middle;
        }}
        
        .team-info.away {{
            text-align: left;
        }}
        
        .team-info.home {{
            text-align: right;
        }}
        
        .team-content {{
            display: inline-block;
            vertical-align: middle;
        }}
        
        .team-logo {{
            width: 80px;
            height: 80px;
            display: inline-block;
            vertical-align: middle;
            margin: 0 15px;
        }}
        
        .team-details {{
            display: inline-block;
            vertical-align: middle;
        }}
        
        .team-name {{
            font-size: 22px;
            font-weight: bold;
            color: #1a202c;
            margin-bottom: 5px;
        }}
        
        .team-type {{
            color: #718096;
            font-size: 14px;
        }}
        
        /* セクション */
        .section {{
            margin-bottom: 30px;
        }}
        
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2d3748;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
            padding: 10px 0;
            background-color: #f7fafc;
            margin-bottom: 20px;
        }}
        
        /* 投手カード */
        .pitcher-grid {{
            display: table;
            width: 100%;
            margin-bottom: 20px;
        }}
        
        .pitcher-card {{
            display: table-cell;
            width: 50%;
            background-color: #f7fafc;
            padding: 15px;
            border: 1px solid #e2e8f0;
        }}
        
        .pitcher-card.away {{
            border-radius: 8px 0 0 8px;
        }}
        
        .pitcher-card.home {{
            border-radius: 0 8px 8px 0;
            text-align: right;
        }}
        
        .pitcher-name {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .pitcher-record {{
            font-size: 14px;
            color: #718096;
        }}
        
        /* 統計バー */
        .stat-bar-container {{
            position: relative;
            height: 30px;
            margin-bottom: 12px;
            background-color: #f7fafc;
            border-radius: 4px;
        }}
        
        .stat-bar {{
            position: absolute;
            height: 24px;
            top: 3px;
            color: white;
            display: flex;
            align-items: center;
            font-size: 12px;
            font-weight: bold;
            border-radius: 3px;
        }}
        
        .stat-bar.away {{
            left: 3px;
            background-color: {away_info['color']};
            justify-content: flex-start;
            padding-left: 8px;
        }}
        
        .stat-bar.home {{
            right: 3px;
            background-color: {home_info['color']};
            justify-content: flex-end;
            padding-right: 8px;
        }}
        
        .stat-label {{
            position: absolute;
            width: 100%;
            text-align: center;
            font-weight: 600;
            font-size: 14px;
            color: #4a5568;
            line-height: 30px;
        }}
        
        /* テーブル */
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        td {{
            padding: 8px;
            font-size: 14px;
            color: #4a5568;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        td:last-child {{
            text-align: right;
            font-weight: 600;
        }}
        
        /* グリッド */
        .grid-2 {{
            display: table;
            width: 100%;
        }}
        
        .grid-cell {{
            display: table-cell;
            width: 50%;
            padding: 0 10px;
        }}
        
        .grid-cell:first-child {{
            padding-left: 0;
        }}
        
        .grid-cell:last-child {{
            padding-right: 0;
        }}
        
        /* フッター */
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #a0aec0;
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
        }}
        
        /* ステータスボックス */
        .status-box {{
            background-color: #edf2f7;
            border: 1px solid #cbd5e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 25px;
            text-align: center;
        }}
        
        .status-box strong {{
            color: #2d3748;
        }}
        
        /* 中継ぎセクションタイトル */
        .bullpen-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 12px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 8px;
        }}
        
        /* 注釈 */
        .note {{
            text-align: center;
            font-size: 11px;
            color: #a0aec0;
            margin-top: 8px;
        }}
    </style>
</head>
<body>
    <div id="a4-page">
        <!-- Header Section -->
        <header>
            <h1>MLB MATCHUP ANALYSIS</h1>
            <p class="date">{game_date_jst.strftime('%Y.%m.%d %H:%M')} (日本時間)</p>
        </header>

        <!-- Team Headers -->
        <div class="team-header">
            <div class="team-info away">
                <div class="team-content">
                    <img src="https://www.mlbstatic.com/team-logos/{away_info['logo_id']}.svg" 
                         alt="{away_team}" 
                         class="team-logo">
                    <div class="team-details">
                        <div class="team-name">{away_team}</div>
                        <div class="team-type">Away Team</div>
                    </div>
                </div>
            </div>
            <div class="team-info home">
                <div class="team-content">
                    <div class="team-details">
                        <div class="team-name">{home_team}</div>
                        <div class="team-type">Home Team</div>
                    </div>
                    <img src="https://www.mlbstatic.com/team-logos/{home_info['logo_id']}.svg" 
                         alt="{home_team}" 
                         class="team-logo">
                </div>
            </div>
        </div>

        <!-- Starting Pitcher Section -->
        <section class="section">
            <h3 class="section-title">先発投手 比較 (Starting Pitcher)</h3>
            <div class="pitcher-grid">
                <div class="pitcher-card away">
                    <p class="pitcher-name">{away_pitcher_name}</p>
                    <p class="pitcher-record">{away_stats['wins']}勝 {away_stats['losses']}敗</p>
                </div>
                <div class="pitcher-card home">
                    <p class="pitcher-name">{home_pitcher_name}</p>
                    <p class="pitcher-record">{home_stats['wins']}勝 {home_stats['losses']}敗</p>
                </div>
            </div>
            
            <!-- Stat Comparison Graph -->
            <div class="stats-comparison">
                <!-- ERA -->
                <div class="stat-bar-container">
                    <div class="stat-bar away" style="width: {era_width_away};">
                        {away_stats['era']}
                    </div>
                    <div class="stat-label">ERA</div>
                    <div class="stat-bar home" style="width: {era_width_home};">
                        {home_stats['era']}
                    </div>
                </div>
                
                <!-- WHIP -->
                <div class="stat-bar-container">
                    <div class="stat-bar away" style="width: {whip_width_away};">
                        {away_stats['whip']}
                    </div>
                    <div class="stat-label">WHIP</div>
                    <div class="stat-bar home" style="width: {whip_width_home};">
                        {home_stats['whip']}
                    </div>
                </div>
                
                <!-- K-BB% -->
                <div class="stat-bar-container">
                    <div class="stat-bar away" style="width: {kbb_width_away};">
                        {away_k_bb:.1f}%
                    </div>
                    <div class="stat-label">K-BB%</div>
                    <div class="stat-bar home" style="width: {kbb_width_home};">
                        {home_k_bb:.1f}%
                    </div>
                </div>
            </div>
            <p class="note">ERA, WHIPは数値が低いほど優れています。K-BB%は高いほど優れています。</p>
        </section>
        
        <!-- Status Box -->
        <div class="status-box">
            <strong>試合ステータス:</strong> {game_data['status']['detailedState']}
        </div>
        
        <!-- Bullpen & Batting Section -->
        <section class="section">
            <div class="grid-2">
                <!-- Away Bullpen -->
                <div class="grid-cell">
                    <h3 class="bullpen-title">中継ぎ陣 (Bullpen)</h3>
                    <table>
                        <tr>
                            <td>ERA</td>
                            <td>-.--</td>
                        </tr>
                        <tr>
                            <td>WHIP</td>
                            <td>-.--</td>
                        </tr>
                        <tr>
                            <td>投手人数</td>
                            <td>データ取得中</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Home Bullpen -->
                <div class="grid-cell">
                    <h3 class="bullpen-title" style="text-align: right;">中継ぎ陣 (Bullpen)</h3>
                    <table>
                        <tr>
                            <td>ERA</td>
                            <td>-.--</td>
                        </tr>
                        <tr>
                            <td>WHIP</td>
                            <td>-.--</td>
                        </tr>
                        <tr>
                            <td>投手人数</td>
                            <td>データ取得中</td>
                        </tr>
                    </table>
                </div>
            </div>
        </section>

        <!-- Team Batting -->
        <section class="section">
            <h3 class="section-title">チーム打撃 比較 (Team Batting)</h3>
            <div class="grid-2">
                <div class="grid-cell">
                    <table>
                        <tr>
                            <td>チーム打率 (AVG)</td>
                            <td>.---</td>
                        </tr>
                        <tr>
                            <td>OPS</td>
                            <td>.---</td>
                        </tr>
                        <tr>
                            <td>本塁打 (HR)</td>
                            <td>--</td>
                        </tr>
                        <tr>
                            <td>総得点 (Runs)</td>
                            <td>---</td>
                        </tr>
                    </table>
                </div>
                <div class="grid-cell">
                    <table>
                        <tr>
                            <td>チーム打率 (AVG)</td>
                            <td>.---</td>
                        </tr>
                        <tr>
                            <td>OPS</td>
                            <td>.---</td>
                        </tr>
                        <tr>
                            <td>本塁打 (HR)</td>
                            <td>--</td>
                        </tr>
                        <tr>
                            <td>総得点 (Runs)</td>
                            <td>---</td>
                        </tr>
                    </table>
                </div>
            </div>
        </section>

        <!-- Recent Form -->
        <section class="section">
            <h3 class="section-title">最近の打撃調子 (Recent OPS)</h3>
            <div class="stats-comparison">
                <!-- Last 5 games -->
                <div class="stat-bar-container">
                    <div class="stat-bar away" style="width: 45%;">
                        .---
                    </div>
                    <div class="stat-label">Last 5</div>
                    <div class="stat-bar home" style="width: 45%;">
                        .---
                    </div>
                </div>
                
                <!-- Last 10 games -->
                <div class="stat-bar-container">
                    <div class="stat-bar away" style="width: 45%;">
                        .---
                    </div>
                    <div class="stat-label">Last 10</div>
                    <div class="stat-bar home" style="width: 45%;">
                        .---
                    </div>
                </div>
            </div>
            <p class="note">OPSは数値が高いほど優れています。</p>
        </section>

        <!-- Footer -->
        <footer class="footer">
            <p>This is a pre-game matchup preview. Stats will be updated as available.</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html
    
    def generate_reports_for_today(self):
        """今日の試合の予想PDFを生成"""
        # 日本時間で本日の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        target_date = now_jst.date()
        
        print(f"\n{'='*60}")
        print(f"MLB PDF Report Generator - {target_date}")
        print(f"{'='*60}\n")
        
        print(f"Fetching games for {target_date}...")
        
        # 試合データを取得
        games_data = self.get_games_for_date(target_date)
        
        if not games_data or 'dates' not in games_data or not games_data['dates']:
            print("No games found for today.")
            return []
        
        # レポート保存ディレクトリ
        reports_dir = Path('reports') / target_date.strftime('%Y%m%d')
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        games = games_data['dates'][0]['games']
        
        print(f"Found {len(games)} games scheduled for today\n")
        
        # すべての試合を処理（最大15試合）
        for i, game in enumerate(games[:15], 1):
            try:
                # チーム名とステータスを取得
                away_team_name = game['teams']['away']['team']['name']
                home_team_name = game['teams']['home']['team']['name']
                game_status = game['status']['detailedState']
                
                print(f"Game {i}/{min(len(games), 15)}: {away_team_name} @ {home_team_name}")
                print(f"  Status: {game_status}")
                
                # HTMLを生成
                print("  Generating HTML...")
                html = self.generate_complete_html(game)
                
                # ファイル名を生成
                away_info = self.team_mappings.get(away_team_name, {'abbr': 'UNK'})
                home_info = self.team_mappings.get(home_team_name, {'abbr': 'UNK'})
                filename = f"{away_info['abbr']}_vs_{home_info['abbr']}_matchup.pdf"
                filepath = reports_dir / filename
                
                # PDFを生成
                print("  Converting to PDF...")
                pdfkit.from_string(html, str(filepath), configuration=self.config, options=self.options)
                
                print(f"  ✓ Success: {filename}\n")
                generated_files.append(str(filepath))
                
                # API制限対策
                time.sleep(1)
                
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                continue
        
        print(f"{'='*60}")
        print(f"✅ Generated {len(generated_files)} PDF reports")
        print(f"📁 Saved in: {reports_dir}")
        print(f"{'='*60}\n")
        
        # 最初のPDFを開く
        if generated_files:
            print(f"Opening: {os.path.basename(generated_files[0])}")
            os.startfile(generated_files[0])
        
        return generated_files


if __name__ == "__main__":
    generator = MLBPDFComplete()
    pdf_files = generator.generate_reports_for_today()