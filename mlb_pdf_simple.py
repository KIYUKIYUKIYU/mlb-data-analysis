import os
import sys
from datetime import datetime, timedelta
import pytz
import pdfkit
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mlb_api_client import MLBApiClient

class MLBPDFGenerator:
    def __init__(self):
        self.api_client = MLBApiClient()
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
            'no-outline': None
        }
        
    def generate_game_html(self, game_data):
        """試合データからHTMLを生成"""
        # 基本情報を取得
        away_team = game_data['teams']['away']['team']['name']
        home_team = game_data['teams']['home']['team']['name']
        away_score = game_data['teams']['away'].get('score', 0)
        home_score = game_data['teams']['home'].get('score', 0)
        
        # 日時をフォーマット
        game_date = datetime.fromisoformat(game_data['gameDate'])
        jst = pytz.timezone('Asia/Tokyo')
        game_date_jst = game_date.astimezone(jst)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{away_team} vs {home_team}</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .date {{
                    text-align: center;
                    color: #666;
                    margin-bottom: 30px;
                }}
                .score {{
                    text-align: center;
                    font-size: 36px;
                    margin: 30px 0;
                    font-weight: bold;
                }}
                .team {{
                    display: inline-block;
                    padding: 0 20px;
                }}
                .winner {{
                    color: #0066cc;
                }}
                .info-section {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }}
                .info-section h3 {{
                    margin-top: 0;
                    color: #333;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 10px 0;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f0f0f0;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>MLB Game Report</h1>
                <div class="date">{game_date_jst.strftime('%Y年%m月%d日 %H:%M')} (日本時間)</div>
                
                <div class="score">
                    <span class="team {'winner' if away_score > home_score else ''}">{away_team} {away_score}</span>
                    -
                    <span class="team {'winner' if home_score > away_score else ''}">{home_score} {home_team}</span>
                </div>
                
                <div class="info-section">
                    <h3>Game Information</h3>
                    <table>
                        <tr>
                            <th>Status</th>
                            <td>{game_data['status']['detailedState']}</td>
                        </tr>
                        <tr>
                            <th>Venue</th>
                            <td>{game_data.get('venue', {}).get('name', 'N/A')}</td>
                        </tr>
                    </table>
                </div>
                
                <div class="info-section">
                    <h3>Team Statistics</h3>
                    <table>
                        <tr>
                            <th>Team</th>
                            <th>Hits</th>
                            <th>Runs</th>
                            <th>Errors</th>
                        </tr>
                        <tr>
                            <td>{away_team}</td>
                            <td>{game_data['teams']['away'].get('hits', 'N/A')}</td>
                            <td>{game_data['teams']['away'].get('score', 'N/A')}</td>
                            <td>{game_data['teams']['away'].get('errors', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td>{home_team}</td>
                            <td>{game_data['teams']['home'].get('hits', 'N/A')}</td>
                            <td>{game_data['teams']['home'].get('score', 'N/A')}</td>
                            <td>{game_data['teams']['home'].get('errors', 'N/A')}</td>
                        </tr>
                    </table>
                </div>
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
        games_data = self.api_client.get_games_for_date(target_date)
        
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
        
        for i, game in enumerate(finished_games, 1):
            try:
                print(f"\nProcessing game {i}/{len(finished_games)}...")
                
                # HTMLを生成
                html = self.generate_game_html(game)
                
                # ファイル名を生成
                away = game['teams']['away']['team']['abbreviation']
                home = game['teams']['home']['team']['abbreviation']
                filename = f"{away}_vs_{home}.pdf"
                filepath = reports_dir / filename
                
                # PDFを生成
                pdfkit.from_string(html, str(filepath), configuration=self.config, options=self.options)
                
                print(f"  Generated: {filename}")
                generated_files.append(str(filepath))
                
            except Exception as e:
                print(f"  Error: {e}")
                continue
        
        print(f"\nGenerated {len(generated_files)} PDF reports")
        return generated_files


if __name__ == "__main__":
    generator = MLBPDFGenerator()
    pdf_files = generator.generate_daily_reports()
    
    if pdf_files:
        print("\nGenerated PDFs:")
        for pdf in pdf_files:
            print(f"  - {pdf}")