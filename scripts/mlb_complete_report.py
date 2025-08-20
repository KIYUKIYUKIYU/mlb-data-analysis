import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import time
import json

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.mlb_api_client import MLBApiClient
from scripts.complete_stats_formatter import CompleteStatsFormatter

class MLBCompleteReport:
    """MLB完全レポートシステム - 明日の試合予想版"""
    
    def __init__(self):
        self.api_client = MLBApiClient()
        self.formatter = CompleteStatsFormatter()
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """キャッシュファイルのパスを取得"""
        return self.cache_dir / f"{key}.json"
    
    def _load_cache(self, key: str) -> dict:
        """キャッシュを読み込み"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def _save_cache(self, key: str, data: dict):
        """キャッシュを保存"""
        try:
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def _get_team_id_mapping(self) -> dict:
        """チーム名からIDへのマッピング"""
        return {
            'Baltimore Orioles': 110,
            'Boston Red Sox': 111,
            'New York Yankees': 147,
            'Tampa Bay Rays': 139,
            'Toronto Blue Jays': 141,
            'Chicago White Sox': 145,
            'Cleveland Guardians': 114,
            'Detroit Tigers': 116,
            'Kansas City Royals': 118,
            'Minnesota Twins': 142,
            'Houston Astros': 117,
            'Los Angeles Angels': 108,
            'Oakland Athletics': 133,
            'Seattle Mariners': 136,
            'Texas Rangers': 140,
            'Atlanta Braves': 144,
            'Miami Marlins': 146,
            'New York Mets': 121,
            'Philadelphia Phillies': 143,
            'Washington Nationals': 120,
            'Chicago Cubs': 112,
            'Cincinnati Reds': 113,
            'Milwaukee Brewers': 158,
            'Pittsburgh Pirates': 134,
            'St. Louis Cardinals': 138,
            'Arizona Diamondbacks': 109,
            'Colorado Rockies': 115,
            'Los Angeles Dodgers': 119,
            'San Diego Padres': 135,
            'San Francisco Giants': 137
        }
    
    def get_games_for_date(self, date) -> dict:
        """指定日の試合データを取得"""
        # キャッシュキー
        cache_key = f"games_{date}"
        
        # キャッシュ確認
        cached_data = self._load_cache(cache_key)
        if cached_data:
            print(f"Using cached data for {date}")
            return cached_data
        
        # API呼び出し
        endpoint = f"schedule?sportId=1&date={date}&hydrate=probablePitcher,team"
        try:
            data = self.api_client._make_request(endpoint)
            if data:
                self._save_cache(cache_key, data)
            return data
        except Exception as e:
            print(f"Error fetching games: {e}")
            return None
    
    def get_team_stats(self, team_id: int) -> dict:
        """チームの基本統計を取得"""
        # TODO: 実際のAPIから取得
        return {
            'batting_avg': '250',
            'ops': '750', 
            'runs': 400,
            'home_runs': 100
        }
    
    def get_recent_team_ops(self, team_id: int) -> dict:
        """チームの最近のOPSを取得"""
        # TODO: 実際の計算ロジックを実装
        return {
            'last_5_ops': 0.750,
            'last_10_ops': 0.730
        }
    
    def get_bullpen_stats(self, team_id: int) -> dict:
        """中継ぎ陣の統計を取得"""
        # TODO: 実際の集計ロジックを実装
        return {
            'era': 3.50,
            'fip': 3.75,
            'whip': 1.25,
            'reliever_count': 7,
            'closer_name': None
        }
    
    async def process_game(self, game_data: dict) -> str:
        """1試合を処理して完全フォーマットのテキストを返す"""
        try:
            # チーム情報
            away_team = game_data['teams']['away']['team']['name']
            home_team = game_data['teams']['home']['team']['name']
            
            # チームIDを取得
            team_id_map = self._get_team_id_mapping()
            away_team_id = team_id_map.get(away_team, 0)
            home_team_id = team_id_map.get(home_team, 0)
            
            # 日時をフォーマット
            game_date = datetime.fromisoformat(game_data['gameDate'].replace('Z', '+00:00'))
            jst = pytz.timezone('Asia/Tokyo')
            game_date_jst = game_date.astimezone(jst)
            start_time = game_date_jst.strftime('%m/%d %H:%M')
            
            # 先発投手情報
            away_pitcher_id = None
            away_pitcher_name = 'TBA'
            if 'probablePitcher' in game_data['teams']['away']:
                pitcher = game_data['teams']['away']['probablePitcher']
                away_pitcher_id = pitcher['id']
                away_pitcher_name = pitcher['fullName']
            
            home_pitcher_id = None
            home_pitcher_name = 'TBA'
            if 'probablePitcher' in game_data['teams']['home']:
                pitcher = game_data['teams']['home']['probablePitcher']
                home_pitcher_id = pitcher['id']
                home_pitcher_name = pitcher['fullName']
            
            print(f"  {away_team} @ {home_team}")
            print(f"  Pitchers: {away_pitcher_name} vs {home_pitcher_name}")
            
            # 各種統計を取得
            away_team_stats = self.get_team_stats(away_team_id)
            home_team_stats = self.get_team_stats(home_team_id)
            
            away_recent_ops = self.get_recent_team_ops(away_team_id)
            home_recent_ops = self.get_recent_team_ops(home_team_id)
            
            away_bullpen = self.get_bullpen_stats(away_team_id)
            home_bullpen = self.get_bullpen_stats(home_team_id)
            
            # データを整形
            away_data = {
                'team_name': away_team,
                'team_id': away_team_id,
                'pitcher_id': away_pitcher_id,
                'pitcher_name': away_pitcher_name,
                'bullpen': away_bullpen,
                'batting': away_team_stats,
                'recent_ops': away_recent_ops
            }
            
            home_data = {
                'team_name': home_team,
                'team_id': home_team_id,
                'pitcher_id': home_pitcher_id,
                'pitcher_name': home_pitcher_name,
                'bullpen': home_bullpen,
                'batting': home_team_stats,
                'recent_ops': home_recent_ops
            }
            
            game_info = {
                'start_time': start_time
            }
            
            # フォーマット
            return self.formatter.format_game_report(away_data, home_data, game_info)
            
        except Exception as e:
            print(f"Error processing game: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def send_to_discord(self, message: str):
        """Discordに送信"""
        webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        if not webhook_url or webhook_url == 'dummy':
            # コンソールに出力
            print("\n" + "="*60)
            print(message)
            print("="*60 + "\n")
            return
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook_url, json={'content': message}) as response:
                    if response.status not in [200, 204]:
                        print(f"Discord送信エラー: {response.status}")
            except Exception as e:
                print(f"Discord送信エラー: {e}")
                print("\n" + "="*60)
                print(message)
                print("="*60 + "\n")
    
    async def run_daily_report(self):
        """明日の試合予想レポートを実行"""
        # 日本時間で日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        
        # 明日の日本時間に行われる試合 = 今日のアメリカ時間の試合
        # 日本が約13-14時間進んでいるので、アメリカの「今日」の試合が日本の「明日」に行われる
        est = pytz.timezone('US/Eastern')
        now_est = now_jst.astimezone(est)
        target_date = now_est.date()  # アメリカの今日 = 日本の明日の試合
        
        tomorrow_jst = now_jst + timedelta(days=1)
        
        print(f"\n{'='*60}")
        print(f"MLB Preview Report - 明日の試合予想")
        print(f"対象日: {tomorrow_jst.strftime('%Y年%m月%d日')} (日本時間)")
        print(f"US Date: {target_date}")
        print(f"現在時刻: {now_jst.strftime('%Y-%m-%d %H:%M')} JST")
        print(f"{'='*60}\n")
        
        # 試合データを取得
        games_data = self.get_games_for_date(target_date)
        
        if not games_data or 'dates' not in games_data or not games_data['dates']:
            print("No games found for this date.")
            return
        
        games = games_data['dates'][0]['games']
        print(f"Found {len(games)} games scheduled for tomorrow\n")
        
        # 全試合を処理
        for i, game in enumerate(games, 1):
            print(f"\nProcessing game {i}/{len(games)}...")
            
            # レポートを生成
            report = await self.process_game(game)
            
            if report:
                # Discord送信またはコンソール出力
                await self.send_to_discord(report)
                
                # 連続送信の制限対策
                if i < len(games):
                    await asyncio.sleep(2)
            
            # API制限対策
            time.sleep(1)
        
        print(f"\n{'='*60}")
        print(f"Completed: {len(games)} games processed")
        print(f"{'='*60}")


async def main():
    """メイン実行関数"""
    reporter = MLBCompleteReport()
    await reporter.run_daily_report()


if __name__ == "__main__":
    # Discord Webhook URLの確認
    if not os.environ.get('DISCORD_WEBHOOK_URL'):
        print("Warning: DISCORD_WEBHOOK_URL not set. Output will be displayed in console only.")
        os.environ['DISCORD_WEBHOOK_URL'] = 'dummy'
    
    # 実行
    asyncio.run(main())