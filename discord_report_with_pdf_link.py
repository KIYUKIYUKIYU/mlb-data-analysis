import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import time

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient
from scripts.pitcher_stats import PitcherStatsAnalyzer
from scripts.team_stats import TeamStatsAnalyzer
from scripts.bullpen_stats import BullpenStatsAnalyzer
from scripts.table_generator import create_stats_table
from mlb_pdf_generator_enhanced import MLBPdfGenerator
from google_drive_pdf_uploader import GoogleDrivePDFUploader

class DiscordReportWithPDFLink:
    """PDFリンク付きDiscordレポート送信クラス"""
    
    def __init__(self):
        self.api_client = MLBApiClient()
        self.discord_client = DiscordClient(os.environ.get('DISCORD_WEBHOOK_URL'))
        self.pitcher_analyzer = PitcherStatsAnalyzer()
        self.team_analyzer = TeamStatsAnalyzer()
        self.bullpen_analyzer = BullpenStatsAnalyzer()
        self.pdf_generator = MLBPdfGenerator()
        
        # Google Drive アップローダーを初期化
        try:
            self.drive_uploader = GoogleDrivePDFUploader()
            self.drive_enabled = True
            print("Google Drive integration enabled")
        except Exception as e:
            print(f"Google Drive integration disabled: {e}")
            self.drive_enabled = False
    
    async def send_game_report_with_pdf_link(self, game_data, game_pk):
        """試合レポートをPDFリンク付きで送信"""
        try:
            # チーム情報取得
            away_team = game_data['teams']['away']['team']['name']
            home_team = game_data['teams']['home']['team']['name']
            away_score = game_data['teams']['away']['score']
            home_score = game_data['teams']['home']['score']
            
            # 先発投手情報
            away_pitcher_id = None
            home_pitcher_id = None
            
            # ゲーム詳細データを取得
            game_detail = self.api_client.get_game_data(game_pk)
            
            if game_detail and 'liveData' in game_detail:
                boxscore = game_detail['liveData']['boxscore']
                if 'teams' in boxscore:
                    away_pitcher_id = boxscore['teams']['away']['pitchers'][0] if boxscore['teams']['away']['pitchers'] else None
                    home_pitcher_id = boxscore['teams']['home']['pitchers'][0] if boxscore['teams']['home']['pitchers'] else None
            
            # 統計データを収集
            stats_data = await self._collect_stats_data(
                away_team, home_team, 
                away_pitcher_id, home_pitcher_id,
                game_detail
            )
            
            # PDFを生成
            pdf_path = None
            pdf_link = None
            
            if self.drive_enabled:
                try:
                    # PDFレポートデータを生成
                    report_data = self.pdf_generator.generate_game_report(game_pk)
                    
                    if report_data:
                        # 一時PDFファイルを生成
                        temp_pdf_path = f"temp_{report_data['away_abbr']}_vs_{report_data['home_abbr']}.pdf"
                        
                        if self.pdf_generator.generate_pdf(report_data, temp_pdf_path):
                            # Google Driveにアップロード
                            pdf_link = self.drive_uploader.upload_pdf(
                                temp_pdf_path,
                                f"{report_data['away_abbr']}_vs_{report_data['home_abbr']}_{datetime.now().strftime('%Y%m%d')}.pdf"
                            )
                            
                            # 一時ファイルを削除
                            if os.path.exists(temp_pdf_path):
                                os.remove(temp_pdf_path)
                            
                            print(f"PDF uploaded: {pdf_link}")
                
                except Exception as e:
                    print(f"PDF generation/upload failed: {e}")
            
            # Discord メッセージを作成
            message = self._create_discord_message(
                away_team, home_team, 
                away_score, home_score,
                stats_data,
                pdf_link
            )
            
            # テーブル画像を生成
            table_path = f"temp_table_{game_pk}.png"
            create_stats_table(stats_data, table_path)
            
            # Discordに送信
            await self._send_to_discord(message, table_path)
            
            # 一時ファイルを削除
            if os.path.exists(table_path):
                os.remove(table_path)
            
        except Exception as e:
            print(f"Error sending game report: {e}")
    
    def _create_discord_message(self, away_team, home_team, away_score, home_score, stats_data, pdf_link=None):
        """Discordメッセージを作成"""
        # 勝敗を判定
        if away_score > home_score:
            result = f"**{away_team}** {away_score} - {home_score} {home_team}"
        else:
            result = f"{away_team} {away_score} - {home_score} **{home_team}**"
        
        # 基本メッセージ
        message = f"""
🏟️ **試合結果**
{result}

📊 **試合詳細統計**
"""
        
        # 先発投手情報を追加（簡略版）
        if 'away_pitcher' in stats_data and stats_data['away_pitcher']:
            ap = stats_data['away_pitcher']
            message += f"\n**{away_team} 先発**: {ap['name']} ({ap['wins']}-{ap['losses']}, ERA {ap['era']:.2f})"
        
        if 'home_pitcher' in stats_data and stats_data['home_pitcher']:
            hp = stats_data['home_pitcher']
            message += f"\n**{home_team} 先発**: {hp['name']} ({hp['wins']}-{hp['losses']}, ERA {hp['era']:.2f})"
        
        # PDFリンクを追加
        if pdf_link:
            message += f"\n\n📄 **詳細レポート（PDF）**: [クリックして表示]({pdf_link})"
        
        return message
    
    async def _collect_stats_data(self, away_team, home_team, away_pitcher_id, home_pitcher_id, game_detail):
        """統計データを収集"""
        stats_data = {
            'away_team': away_team,
            'home_team': home_team
        }
        
        # 先発投手統計
        if away_pitcher_id:
            stats_data['away_pitcher'] = self.pitcher_analyzer.get_pitcher_stats(away_pitcher_id)
        if home_pitcher_id:
            stats_data['home_pitcher'] = self.pitcher_analyzer.get_pitcher_stats(home_pitcher_id)
        
        # チーム打撃統計
        stats_data['away_batting'] = self.team_analyzer.get_team_batting_stats(away_team)
        stats_data['home_batting'] = self.team_analyzer.get_team_batting_stats(home_team)
        
        # 最近のOPS
        stats_data['away_recent_ops'] = self.team_analyzer.get_recent_team_ops(away_team)
        stats_data['home_recent_ops'] = self.team_analyzer.get_recent_team_ops(home_team)
        
        # 中継ぎ陣統計
        stats_data['away_bullpen'] = self.bullpen_analyzer.get_bullpen_stats(away_team)
        stats_data['home_bullpen'] = self.bullpen_analyzer.get_bullpen_stats(home_team)
        
        return stats_data
    
    async def _send_to_discord(self, message, table_path):
        """Discordに送信"""
        async with aiohttp.ClientSession() as session:
            # フォームデータを作成
            data = aiohttp.FormData()
            
            # メッセージ内容
            data.add_field('payload_json',
                          f'{{"content": "{message}"}}',
                          content_type='application/json')
            
            # テーブル画像
            if os.path.exists(table_path):
                with open(table_path, 'rb') as f:
                    data.add_field('file',
                                  f,
                                  filename='stats_table.png',
                                  content_type='image/png')
            
            # 送信
            webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
            async with session.post(webhook_url, data=data) as response:
                if response.status not in [200, 204]:
                    print(f"Failed to send to Discord: {response.status}")
                    print(await response.text())
    
    async def send_all_games_report(self):
        """全試合のレポートを送信"""
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
            return
        
        games = games_data['dates'][0]['games']
        finished_games = [g for g in games if g['status']['abstractGameState'] == 'Final']
        
        print(f"Found {len(finished_games)} finished games")
        
        # 各試合のレポートを送信
        for i, game in enumerate(finished_games):
            print(f"\nProcessing game {i+1}/{len(finished_games)}...")
            
            await self.send_game_report_with_pdf_link(game, game['gamePk'])
            
            # レート制限対策
            if i < len(finished_games) - 1:
                await asyncio.sleep(3)
        
        print("\nAll reports sent successfully!")


async def main():
    """メイン実行関数"""
    reporter = DiscordReportWithPDFLink()
    await reporter.send_all_games_report()


if __name__ == "__main__":
    # Discord Webhook URLが設定されているか確認
    if not os.environ.get('DISCORD_WEBHOOK_URL'):
        print("Error: DISCORD_WEBHOOK_URL environment variable not set")
        print("Please set it using: set DISCORD_WEBHOOK_URL=your_webhook_url")
        sys.exit(1)
    
    # 実行
    asyncio.run(main())