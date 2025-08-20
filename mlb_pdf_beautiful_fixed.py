import os
import sys
from datetime import datetime, timedelta
import pytz
import pdfkit
from pathlib import Path
import requests

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 既存のモジュールをインポート（存在する場合）
try:
    from scripts.discord_report_with_table import DiscordReportWithTable
    discord_reporter = DiscordReportWithTable()
    USE_REAL_STATS = True
except:
    USE_REAL_STATS = False
    print("Note: Using dummy data. Real stats module not found.")

class MLBPDFPreview:
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
        
        # チームカラー定義（全30チーム）
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
        
        # チーム名と略称のマッピング
        self.team_mappings = {
            'New York Mets': ('NYM', '121'),
            'Philadelphia Phillies': ('PHI', '143'),
            'New York Yankees': ('NYY', '147'),
            'Boston Red Sox': ('BOS', '111'),
            'Los Angeles Dodgers': ('LAD', '119'),
            'Atlanta Braves': ('ATL', '144'),
            'Houston Astros': ('HOU', '117'),
            'San Diego Padres': ('SD', '135'),
            'Tampa Bay Rays': ('TB', '139'),
            'Baltimore Orioles': ('BAL', '110'),
            'Toronto Blue Jays': ('TOR', '141'),
            'Milwaukee Brewers': ('MIL', '158'),
            'Minnesota Twins': ('MIN', '142'),
            'Cleveland Guardians': ('CLE', '114'),
            'Chicago Cubs': ('CHC', '112'),
            'Chicago White Sox': ('CWS', '145'),
            'Detroit Tigers': ('DET', '116'),
            'Kansas City Royals': ('KC', '118'),
            'St. Louis Cardinals': ('STL', '138'),
            'Cincinnati Reds': ('CIN', '113'),
            'Pittsburgh Pirates': ('PIT', '134'),
            'Miami Marlins': ('MIA', '146'),
            'Washington Nationals': ('WSH', '120'),
            'Colorado Rockies': ('COL', '115'),
            'Arizona Diamondbacks': ('ARI', '109'),
            'Los Angeles Angels': ('LAA', '108'),
            'Oakland Athletics': ('OAK', '133'),
            'Seattle Mariners': ('SEA', '136'),
            'Texas Rangers': ('TEX', '140'),
            'San Francisco Giants': ('SF', '137')
        }
    
    def get_games_for_date(self, date):
        """指定日の試合データを取得（予定試合も含む）"""
        url = f"https://statsapi.mlb.com/api/v1/schedule?date={date}&sportId=1&hydrate=probablePitcher,team,linescore"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching games: {e}")
            return None
    
    def get_real_stats(self, game_data):
        """実際の統計データを取得（可能な場合）"""
        if USE_REAL_STATS:
            try:
                # discord_report_with_tableから統計を取得する処理
                # ここは実装によって異なる
                return None
            except:
                return None
        return None
    
    def generate_beautiful_html(self, game_data):
        """美しいデザインのHTMLを生成（試合前予想レポート）"""
        # 基本情報を取得
        away_team = game_data['teams']['away']['team']['name']
        home_team = game_data['teams']['home']['team']['name']
        
        # チーム略称とロゴIDを取得
        away_abbr, away_logo_id = self.team_mappings.get(away_team, ('???', '120'))
        home_abbr, home_logo_id = self.team_mappings.get(home_team, ('???', '120'))
        
        # 日時をフォーマット
        game_date = datetime.fromisoformat(game_data['gameDate'])
        jst = pytz.timezone('Asia/Tokyo')
        game_date_jst = game_date.astimezone(jst)
        
        # チームカラーを取得
        away_colors = self.team_colors.get(away_abbr, {'primary': '#000000', 'secondary': '#FFFFFF'})
        home_colors = self.team_colors.get(home_abbr, {'primary': '#000000', 'secondary': '#FFFFFF'})
        
        # 先発投手情報を取得（利用可能な場合）
        away_pitcher = "TBA"
        home_pitcher = "TBA"
        
        if 'probablePitcher' in game_data['teams']['away']:
            pitcher = game_data['teams']['away']['probablePitcher']
            away_pitcher = pitcher.get('fullName', 'TBA')
        
        if 'probablePitcher' in game_data['teams']['home']:
            pitcher = game_data['teams']['home']['probablePitcher']
            home_pitcher = pitcher.get('fullName', 'TBA')
        
        # CSSスタイルを生成
        team_colors_css = ""
        for abbr, colors in self.team_colors.items():
            team_colors_css += f"""
        .team-{abbr}-bg {{ background-color: {colors['primary']}; }}
        .team-{abbr}-text {{ color: {colors['secondary']}; }}"""
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB Matchup Analysis: {away_team} vs {home_team}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    <style>
        /* A4サイズ (210mm x 297mm) のアスペクト比を維持 */
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            #a4-page {{
                margin: 0;
                box-shadow: none;
                width: 210mm;
                height: 297mm;
            }}
        }}
        
        body {{
            font-family: 'Inter', 'Noto Sans JP', sans-serif;
            background-color: #e2e8f0;
        }}

        #a4-page {{
            width: 8.5in;
            min-height: 11in;
            background-color: white;
            margin: 2rem auto;
            padding: 2rem;
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            border-radius: 0.25rem;
            display: flex;
            flex-direction: column;
        }}

        {team_colors_css}
        
        .stat-bar-container {{
            display: flex;
            align-items: center;
            margin-bottom: 0.75rem;
            position: relative;
        }}

        .stat-bar {{
            height: 24px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            transition: width 0.5s ease-in-out;
            border-radius: 0.25rem;
        }}
        .stat-label {{
            width: 60px;
            text-align: center;
            font-weight: 600;
            font-size: 0.9rem;
            color: #4a5568;
        }}
        .stat-value {{
            position: absolute;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        .away-value {{ left: 5px; color: white; }}
        .home-value {{ right: 5px; color: white; }}
    </style>
</head>
<body class="bg-slate-200">

    <!-- A4 Page Container -->
    <div id="a4-page">
        <!-- Header Section -->
        <header class="text-center border-b-2 pb-4 mb-6 border-slate-200">
            <h1 class="text-3xl font-bold text-slate-800 tracking-wider">MLB MATCHUP ANALYSIS</h1>
            <p class="text-slate-500 mt-1">{game_date_jst.strftime('%Y.%m.%d %H:%M')} (日本時間)</p>
        </header>

        <!-- Main Content -->
        <main class="flex-grow">
            <!-- Team Headers -->
            <div class="grid grid-cols-2 gap-8 items-center mb-6">
                <div class="flex items-center gap-4">
                    <img src="https://www.mlbstatic.com/team-logos/{away_logo_id}.svg" alt="{away_team} Logo" class="h-20 w-20">
                    <div>
                        <h2 class="text-2xl font-bold text-slate-800">{away_team}</h2>
                        <p class="text-slate-500">Away Team</p>
                    </div>
                </div>
                <div class="flex items-center justify-end gap-4">
                     <div>
                        <h2 class="text-2xl font-bold text-slate-800 text-right">{home_team}</h2>
                        <p class="text-slate-500 text-right">Home Team</p>
                    </div>
                    <img src="https://www.mlbstatic.com/team-logos/{home_logo_id}.svg" alt="{home_team} Logo" class="h-20 w-20">
                </div>
            </div>

            <!-- Starting Pitcher Section -->
            <section class="mb-8">
                <h3 class="text-xl font-bold text-slate-700 mb-4 text-center border-t border-b py-2 bg-slate-50">先発投手 比較 (Starting Pitcher)</h3>
                <div class="grid grid-cols-2 gap-8">
                    <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                        <p class="text-lg font-bold">{away_pitcher}</p>
                        <p class="text-sm text-slate-500">シーズン成績確認中</p>
                    </div>
                    <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 text-right">
                        <p class="text-lg font-bold">{home_pitcher}</p>
                        <p class="text-sm text-slate-500">シーズン成績確認中</p>
                    </div>
                </div>
                
                <!-- Stat Comparison Graph -->
                <div class="mt-4 space-y-3">
                    <!-- ERA -->
                    <div class="stat-bar-container">
                        <div class="stat-bar team-{away_abbr}-bg" style="width: 45%;"><span class="stat-value away-value">--</span></div>
                        <div class="stat-label">ERA</div>
                        <div class="stat-bar team-{home_abbr}-bg" style="width: 45%;"><span class="stat-value home-value">--</span></div>
                    </div>
                    <!-- WHIP -->
                    <div class="stat-bar-container">
                        <div class="stat-bar team-{away_abbr}-bg" style="width: 45%;"><span class="stat-value away-value">--</span></div>
                        <div class="stat-label">WHIP</div>
                        <div class="stat-bar team-{home_abbr}-bg" style="width: 45%;"><span class="stat-value home-value">--</span></div>
                    </div>
                     <!-- K-BB% -->
                    <div class="stat-bar-container">
                        <div class="stat-bar team-{away_abbr}-bg" style="width: 45%;"><span class="stat-value away-value">--</span></div>
                        <div class="stat-label">K-BB%</div>
                        <div class="stat-bar team-{home_abbr}-bg" style="width: 45%;"><span class="stat-value home-value">--</span></div>
                    </div>
                </div>
                <p class="text-xs text-center text-slate-400 mt-2">試合前予想レポート - 統計データは随時更新されます</p>
            </section>
            
            <!-- Status Notice -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p class="text-blue-800 text-center">
                    <strong>試合ステータス:</strong> {game_data['status']['detailedState']}
                </p>
            </div>
        </main>

        <!-- Footer -->
        <footer class="text-center text-xs text-slate-400 mt-auto pt-4 border-t border-slate-200">
            <p>This is a pre-game matchup preview. Stats will be updated as available.</p>
        </footer>

    </div>

</body>
</html>
"""
        
        return html
    
    def generate_daily_reports(self):
        """当日の全試合の予想PDFを生成"""
        # 日本時間で本日の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        
        # 今日の試合を取得（予定も含む）
        target_date = now_jst.date()
        
        print(f"Fetching games for {target_date} (including scheduled games)...")
        
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
        
        print(f"Found {len(games)} games (all statuses)")
        
        # 最初の3試合を処理（テスト用）
        for i, game in enumerate(games[:3], 1):
            try:
                print(f"\nProcessing game {i}/3...")
                
                # チーム名とステータスを取得
                away_team_name = game['teams']['away']['team']['name']
                home_team_name = game['teams']['home']['team']['name']
                game_status = game['status']['detailedState']
                
                print(f"  {away_team_name} @ {home_team_name}")
                print(f"  Status: {game_status}")
                
                # HTMLを生成
                html = self.generate_beautiful_html(game)
                
                # ファイル名を生成
                away_abbr, _ = self.team_mappings.get(away_team_name, ('UNK', '120'))
                home_abbr, _ = self.team_mappings.get(home_team_name, ('UNK', '120'))
                filename = f"{away_abbr}_vs_{home_abbr}_preview.pdf"
                filepath = reports_dir / filename
                
                # PDFを生成
                pdfkit.from_string(html, str(filepath), configuration=self.config, options=self.options)
                
                print(f"  ✓ Generated: {filename}")
                generated_files.append(str(filepath))
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n✅ Generated {len(generated_files)} preview PDF reports")
        print(f"📁 Saved in: {reports_dir}")
        
        # 最初のPDFを開く
        if generated_files:
            print(f"\nOpening: {os.path.basename(generated_files[0])}")
            os.startfile(generated_files[0])
        
        return generated_files


if __name__ == "__main__":
    generator = MLBPDFPreview()
    pdf_files = generator.generate_daily_reports()