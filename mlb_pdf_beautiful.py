import os
import sys
from datetime import datetime, timedelta
import pytz
import pdfkit
from pathlib import Path
import requests

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 既存のモジュールをインポート（利用可能な場合）
try:
    from scripts.discord_report_with_table import get_pitcher_stats, get_team_stats, get_bullpen_stats
    USE_DETAILED_STATS = True
except:
    USE_DETAILED_STATS = False

class MLBPDFBeautiful:
    def __init__(self):
        self.wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        self.config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        
        # PDFオプション
        self.options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'enable-local-file-access': None,
            'no-outline': None
        }
        
        # チームカラー定義（MLBの公式カラー）
        self.team_colors = {
            'NYM': {'primary': '#002D72', 'secondary': '#FF5910'},
            'PHI': {'primary': '#E81828', 'secondary': '#003087'},
            'NYY': {'primary': '#003087', 'secondary': '#E4002C'},
            'BOS': {'primary': '#BD3039', 'secondary': '#0C2340'},
            'LAD': {'primary': '#005A9C', 'secondary': '#EF3E42'},
            'ATL': {'primary': '#CE1141', 'secondary': '#13274F'},
            'HOU': {'primary': '#002D62', 'secondary': '#EB6E1F'},
            'SD': {'primary': '#2F241D', 'secondary': '#FFC425'},
            'TB': {'primary': '#092C5C', 'secondary': '#8FBCE6'},
            'BAL': {'primary': '#DF4601', 'secondary': '#000000'},
            'TOR': {'primary': '#134A8E', 'secondary': '#E8291C'},
            'MIL': {'primary': '#0A2351', 'secondary': '#B6922E'},
            'MIN': {'primary': '#002B5C', 'secondary': '#D31145'},
            'CLE': {'primary': '#00385D', 'secondary': '#E50022'},
            'CHC': {'primary': '#0E3386', 'secondary': '#CC3433'},
            'CWS': {'primary': '#27251F', 'secondary': '#C4CED4'},
            'DET': {'primary': '#0C2340', 'secondary': '#FA4616'},
            'KC': {'primary': '#004687', 'secondary': '#BD9B60'},
            'STL': {'primary': '#C41E3A', 'secondary': '#0C2340'},
            'CIN': {'primary': '#C6011F', 'secondary': '#000000'},
            'PIT': {'primary': '#FDB827', 'secondary': '#27251F'},
            'MIA': {'primary': '#00A3E0', 'secondary': '#EF3340'},
            'WSH': {'primary': '#AB0003', 'secondary': '#14225A'},
            'COL': {'primary': '#33006F', 'secondary': '#C4CED4'},
            'ARI': {'primary': '#A71930', 'secondary': '#E3D4AD'},
            'LAA': {'primary': '#BA0021', 'secondary': '#003263'},
            'OAK': {'primary': '#003831', 'secondary': '#EFB21E'},
            'SEA': {'primary': '#0C2C56', 'secondary': '#005C5C'},
            'TEX': {'primary': '#003278', 'secondary': '#C0111F'},
            'SF': {'primary': '#FD5A1E', 'secondary': '#27251F'}
        }
        
        # チーム略称マッピング
        self.team_abbr = {
            'New York Mets': 'NYM', 'Philadelphia Phillies': 'PHI',
            'New York Yankees': 'NYY', 'Boston Red Sox': 'BOS',
            'Los Angeles Dodgers': 'LAD', 'Atlanta Braves': 'ATL',
            'Houston Astros': 'HOU', 'San Diego Padres': 'SD',
            'Tampa Bay Rays': 'TB', 'Baltimore Orioles': 'BAL',
            'Toronto Blue Jays': 'TOR', 'Milwaukee Brewers': 'MIL',
            'Minnesota Twins': 'MIN', 'Cleveland Guardians': 'CLE',
            'Chicago Cubs': 'CHC', 'Chicago White Sox': 'CWS',
            'Detroit Tigers': 'DET', 'Kansas City Royals': 'KC',
            'St. Louis Cardinals': 'STL', 'Cincinnati Reds': 'CIN',
            'Pittsburgh Pirates': 'PIT', 'Miami Marlins': 'MIA',
            'Washington Nationals': 'WSH', 'Colorado Rockies': 'COL',
            'Arizona Diamondbacks': 'ARI', 'Los Angeles Angels': 'LAA',
            'Oakland Athletics': 'OAK', 'Seattle Mariners': 'SEA',
            'Texas Rangers': 'TEX', 'San Francisco Giants': 'SF'
        }
        
        # チームロゴID
        self.team_logo_ids = {
            'NYM': '121', 'PHI': '143', 'NYY': '147', 'BOS': '111',
            'LAD': '119', 'ATL': '144', 'HOU': '117', 'SD': '135',
            'TB': '139', 'BAL': '110', 'TOR': '141', 'MIL': '158',
            'MIN': '142', 'CLE': '114', 'CHC': '112', 'CWS': '145',
            'DET': '116', 'KC': '118', 'STL': '138', 'CIN': '113',
            'PIT': '134', 'MIA': '146', 'WSH': '120', 'COL': '115',
            'ARI': '109', 'LAA': '108', 'OAK': '133', 'SEA': '136',
            'TEX': '140', 'SF': '137'
        }
    
    def get_games_for_date(self, date):
        """指定日の試合データを取得"""
        url = f"https://statsapi.mlb.com/api/v1/schedule?date={date}&sportId=1&hydrate=probablePitcher,team,linescore"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching games: {e}")
            return None
    
    def generate_beautiful_html(self, game_data):
        """美しいデザインのHTMLを生成"""
        # 基本情報を取得
        away_team = game_data['teams']['away']['team']['name']
        home_team = game_data['teams']['home']['team']['name']
        away_abbr = self.team_abbr.get(away_team, away_team[:3].upper())
        home_abbr = self.team_abbr.get(home_team, home_team[:3].upper())
        
        # スコア
        away_score = game_data['teams']['away'].get('score', 0)
        home_score = game_data['teams']['home'].get('score', 0)
        
        # 日時をフォーマット
        game_date = datetime.fromisoformat(game_data['gameDate'])
        jst = pytz.timezone('Asia/Tokyo')
        game_date_jst = game_date.astimezone(jst)
        
        # チームカラーを取得
        away_colors = self.team_colors.get(away_abbr, {'primary': '#000000', 'secondary': '#FFFFFF'})
        home_colors = self.team_colors.get(home_abbr, {'primary': '#000000', 'secondary': '#FFFFFF'})
        
        # ロゴURLを生成
        away_logo_id = self.team_logo_ids.get(away_abbr, '120')
        home_logo_id = self.team_logo_ids.get(home_abbr, '120')
        
        # ダミーデータ（実際のAPIから取得できない場合）
        dummy_pitcher_stats = {
            'name': 'TBA',
            'wins': 0,
            'losses': 0,
            'era': '0.00',
            'whip': '0.00',
            'k_bb_percent': '0.0'
        }
        
        # CSSスタイルを生成
        team_colors_css = ""
        for abbr, colors in self.team_colors.items():
            team_colors_css += f"""
        .team-{abbr}-bg {{ background-color: {colors['primary']}; }}
        .team-{abbr}-text {{ color: {colors['secondary']}; }}
            """
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB Matchup Analysis: {away_team} vs {home_team}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', Arial, sans-serif;
            background-color: #e2e8f0;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}

        #a4-page {{
            width: 210mm;
            min-height: 297mm;
            background-color: white;
            margin: 0 auto;
            padding: 2rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}

        {team_colors_css}
        
        .stat-bar-container {{
            display: flex;
            align-items: center;
            margin-bottom: 0.75rem;
            position: relative;
            height: 30px;
        }}

        .stat-bar {{
            height: 24px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 0.25rem;
            position: absolute;
        }}
        
        .stat-bar.away {{
            left: 0;
            background-color: {away_colors['primary']};
        }}
        
        .stat-bar.home {{
            right: 0;
            background-color: {home_colors['primary']};
        }}
        
        .stat-label {{
            width: 100%;
            text-align: center;
            font-weight: 600;
            font-size: 0.9rem;
            color: #4a5568;
            z-index: 10;
            position: relative;
        }}
        
        .stat-value {{
            position: absolute;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
        }}
        
        .away-value {{ left: 5px; }}
        .home-value {{ right: 5px; }}
        
        header {{
            text-align: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        h1 {{
            font-size: 1.875rem;
            font-weight: bold;
            color: #1a202c;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }}
        
        .date {{
            color: #718096;
            font-size: 0.875rem;
        }}
        
        .team-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            gap: 2rem;
        }}
        
        .team-info {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .team-info.home {{
            flex-direction: row-reverse;
        }}
        
        .team-logo {{
            width: 80px;
            height: 80px;
            object-fit: contain;
        }}
        
        .team-name {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #1a202c;
        }}
        
        .team-type {{
            color: #718096;
            font-size: 0.875rem;
        }}
        
        .section {{
            margin-bottom: 2rem;
        }}
        
        .section-title {{
            font-size: 1.25rem;
            font-weight: bold;
            color: #2d3748;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
            padding: 0.5rem 0;
            background-color: #f7fafc;
            margin-bottom: 1rem;
        }}
        
        .pitcher-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 1rem;
        }}
        
        .pitcher-card {{
            background-color: #f7fafc;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #e2e8f0;
        }}
        
        .pitcher-name {{
            font-size: 1.125rem;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }}
        
        .pitcher-record {{
            font-size: 0.875rem;
            color: #718096;
        }}
        
        .stats-comparison {{
            margin-top: 1rem;
        }}
        
        .note {{
            text-align: center;
            font-size: 0.75rem;
            color: #a0aec0;
            margin-top: 0.5rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        td {{
            padding: 0.5rem;
            font-size: 0.875rem;
            color: #4a5568;
        }}
        
        td:last-child {{
            text-align: right;
            font-weight: 600;
        }}
        
        .bullpen-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}
        
        .bullpen-section h3 {{
            font-size: 1.125rem;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 0.25rem;
        }}
        
        .footer {{
            text-align: center;
            font-size: 0.75rem;
            color: #a0aec0;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #e2e8f0;
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

        <!-- Main Content -->
        <main>
            <!-- Team Headers -->
            <div class="team-header">
                <div class="team-info">
                    <img src="https://www.mlbstatic.com/team-logos/{away_logo_id}.svg" 
                         alt="{away_team} Logo" 
                         class="team-logo"
                         onerror="this.style.display='none'">
                    <div>
                        <h2 class="team-name">{away_team}</h2>
                        <p class="team-type">Away Team</p>
                    </div>
                </div>
                <div class="team-info home">
                    <img src="https://www.mlbstatic.com/team-logos/{home_logo_id}.svg" 
                         alt="{home_team} Logo" 
                         class="team-logo"
                         onerror="this.style.display='none'">
                    <div style="text-align: right;">
                        <h2 class="team-name">{home_team}</h2>
                        <p class="team-type">Home Team</p>
                    </div>
                </div>
            </div>

            <!-- Starting Pitcher Section -->
            <section class="section">
                <h3 class="section-title">先発投手 比較 (Starting Pitcher)</h3>
                <div class="pitcher-grid">
                    <div class="pitcher-card">
                        <p class="pitcher-name">TBA</p>
                        <p class="pitcher-record">0勝 0敗</p>
                    </div>
                    <div class="pitcher-card" style="text-align: right;">
                        <p class="pitcher-name">TBA</p>
                        <p class="pitcher-record">0勝 0敗</p>
                    </div>
                </div>
                
                <!-- Stat Comparison Graph -->
                <div class="stats-comparison">
                    <!-- ERA -->
                    <div class="stat-bar-container">
                        <div class="stat-bar away" style="width: 45%;">
                            <span class="stat-value away-value">3.50</span>
                        </div>
                        <div class="stat-label">ERA</div>
                        <div class="stat-bar home" style="width: 45%;">
                            <span class="stat-value home-value">3.50</span>
                        </div>
                    </div>
                    <!-- WHIP -->
                    <div class="stat-bar-container">
                        <div class="stat-bar away" style="width: 45%;">
                            <span class="stat-value away-value">1.20</span>
                        </div>
                        <div class="stat-label">WHIP</div>
                        <div class="stat-bar home" style="width: 45%;">
                            <span class="stat-value home-value">1.20</span>
                        </div>
                    </div>
                    <!-- K-BB% -->
                    <div class="stat-bar-container">
                        <div class="stat-bar away" style="width: 45%;">
                            <span class="stat-value away-value">15.0%</span>
                        </div>
                        <div class="stat-label">K-BB%</div>
                        <div class="stat-bar home" style="width: 45%;">
                            <span class="stat-value home-value">15.0%</span>
                        </div>
                    </div>
                </div>
                <p class="note">ERA, WHIPは数値が低いほど優れています。</p>
            </section>
            
            <!-- Bullpen & Batting Section -->
            <section>
                <div class="bullpen-grid">
                    <!-- Away Bullpen -->
                    <div class="bullpen-section">
                        <h3>中継ぎ陣 (Bullpen)</h3>
                        <table>
                            <tr>
                                <td>ERA</td>
                                <td>3.50</td>
                            </tr>
                            <tr>
                                <td>WHIP</td>
                                <td>1.30</td>
                            </tr>
                            <tr>
                                <td>投手人数</td>
                                <td>7名</td>
                            </tr>
                        </table>
                    </div>
                    <!-- Home Bullpen -->
                    <div class="bullpen-section">
                        <h3 style="text-align: right;">中継ぎ陣 (Bullpen)</h3>
                        <table>
                            <tr>
                                <td>ERA</td>
                                <td>3.50</td>
                            </tr>
                            <tr>
                                <td>WHIP</td>
                                <td>1.30</td>
                            </tr>
                            <tr>
                                <td>投手人数</td>
                                <td>7名</td>
                            </tr>
                        </table>
                    </div>
                </div>

                <!-- Team Batting -->
                <div class="section" style="margin-top: 2rem;">
                    <h3 class="section-title">チーム打撃 比較 (Team Batting)</h3>
                    <div class="bullpen-grid">
                        <div>
                            <table>
                                <tr>
                                    <td>チーム打率 (AVG)</td>
                                    <td>.250</td>
                                </tr>
                                <tr>
                                    <td>OPS</td>
                                    <td>.750</td>
                                </tr>
                                <tr>
                                    <td>本塁打 (HR)</td>
                                    <td>100</td>
                                </tr>
                                <tr>
                                    <td>総得点 (Runs)</td>
                                    <td>400</td>
                                </tr>
                            </table>
                        </div>
                        <div>
                            <table>
                                <tr>
                                    <td>チーム打率 (AVG)</td>
                                    <td>.250</td>
                                </tr>
                                <tr>
                                    <td>OPS</td>
                                    <td>.750</td>
                                </tr>
                                <tr>
                                    <td>本塁打 (HR)</td>
                                    <td>100</td>
                                </tr>
                                <tr>
                                    <td>総得点 (Runs)</td>
                                    <td>400</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Recent Form -->
                <div class="section">
                    <h3 class="section-title">最近の打撃調子 (Recent OPS)</h3>
                    <div class="stats-comparison">
                        <!-- Last 5 games -->
                        <div class="stat-bar-container">
                            <div class="stat-bar away" style="width: 45%;">
                                <span class="stat-value away-value">0.750</span>
                            </div>
                            <div class="stat-label">Last 5</div>
                            <div class="stat-bar home" style="width: 45%;">
                                <span class="stat-value home-value">0.750</span>
                            </div>
                        </div>
                        <!-- Last 10 games -->
                        <div class="stat-bar-container">
                            <div class="stat-bar away" style="width: 45%;">
                                <span class="stat-value away-value">0.750</span>
                            </div>
                            <div class="stat-label">Last 10</div>
                            <div class="stat-bar home" style="width: 45%;">
                                <span class="stat-value home-value">0.750</span>
                            </div>
                        </div>
                    </div>
                    <p class="note">OPSは数値が高いほど優れています。</p>
                </div>
            </section>
        </main>

        <!-- Footer -->
        <footer class="footer">
            <p>This is a data-driven matchup preview. All stats are for illustrative purposes.</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html
    
    def generate_daily_reports(self):
        """当日の全試合のPDFを生成"""
        # 日本時間で本日の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        
        # アメリカの試合日を計算
        if now_jst.hour >= 21:
            target_date = now_jst.date()
        else:
            target_date = (now_jst - timedelta(days=1)).date()
        
        print(f"Fetching games for {target_date}...")
        
        # 試合データを取得
        games_data = self.get_games_for_date(target_date)
        
        if not games_data or 'dates' not in games_data or not games_data['dates']:
            print("No games found")
            return []
        
        # レポート保存ディレクトリ
        reports_dir = Path('reports') / target_date.strftime('%Y%m%d')
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        games = games_data['dates'][0]['games']
        finished_games = [g for g in games if g['status']['abstractGameState'] == 'Final']
        
        print(f"Found {len(finished_games)} finished games")
        
        # 最初の1試合だけ処理（テスト用）
        for i, game in enumerate(finished_games[:1], 1):
            try:
                print(f"\nProcessing game {i}/1 (test mode)...")
                
                # チーム名を取得
                away_team_name = game['teams']['away']['team']['name']
                home_team_name = game['teams']['home']['team']['name']
                print(f"  {away_team_name} @ {home_team_name}")
                
                # HTMLを生成
                html = self.generate_beautiful_html(game)
                
                # ファイル名を生成
                away = self.team_abbr.get(away_team_name, away_team_name[:3].upper())
                home = self.team_abbr.get(home_team_name, home_team_name[:3].upper())
                filename = f"{away}_vs_{home}_beautiful.pdf"
                filepath = reports_dir / filename
                
                # PDFを生成
                pdfkit.from_string(html, str(filepath), configuration=self.config, options=self.options)
                
                print(f"  ✓ Generated: {filename}")
                generated_files.append(str(filepath))
                
                # 自動的に開く
                os.startfile(str(filepath))
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n✅ Generated {len(generated_files)} beautiful PDF reports")
        print(f"📁 Saved in: {reports_dir}")
        return generated_files


if __name__ == "__main__":
    generator = MLBPDFBeautiful()
    pdf_files = generator.generate_daily_reports()