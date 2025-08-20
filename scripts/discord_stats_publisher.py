"""
Discord向けMLB統計データ配信スクリプト
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from discord_webhook import DiscordWebhook, DiscordEmbed
from src.mlb_api_client import MLBApiClient
from dotenv import load_dotenv

load_dotenv()

class DiscordStatsPublisher:
    def __init__(self):
        self.client = MLBApiClient()
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URLが設定されていません")
    
    def load_team_data(self, team_id):
        """チームの全データを読み込む"""
        data = {}
        
        # 基本統計
        stats_files = list(Path("data/processed").glob(f"team_analysis_{team_id}_*.json"))
        if stats_files:
            with open(max(stats_files, key=lambda x: x.stat().st_mtime), 'r', encoding='utf-8') as f:
                data['stats'] = json.load(f)
        
        # 直近OPS
        ops5_files = list(Path("data/processed/recent_ops").glob(f"team_{team_id}_last5games_*.json"))
        if ops5_files:
            with open(max(ops5_files, key=lambda x: x.stat().st_mtime), 'r', encoding='utf-8') as f:
                data['ops5'] = json.load(f)
                
        ops10_files = list(Path("data/processed/recent_ops").glob(f"team_{team_id}_last10games_*.json"))
        if ops10_files:
            with open(max(ops10_files, key=lambda x: x.stat().st_mtime), 'r', encoding='utf-8') as f:
                data['ops10'] = json.load(f)
        
        # 率統計
        rates_files = list(Path("data/processed/accurate_rates").glob(f"team_{team_id}_rates_*.json"))
        if rates_files:
            with open(max(rates_files, key=lambda x: x.stat().st_mtime), 'r', encoding='utf-8') as f:
                data['rates'] = json.load(f)
        
        return data
    
    def format_game_message(self, game, away_data, home_data):
        """1試合分のメッセージをフォーマット"""
        away_name = game['teams']['away']['team']['name']
        home_name = game['teams']['home']['team']['name']
        
        # 日本時間に変換
        game_time = datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
        japan_time = game_time + timedelta(hours=9)
        
        # 基本情報セクション
        message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
### ⚾ **{away_name} vs {home_name}**
🏟️ {game.get('venue', {}).get('name', 'Unknown')} | 🕔 日本時間 {japan_time.strftime('%H:%M')} 開始
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

"""
        
        # 先発投手情報（未定の場合が多い）
        away_sp = game['teams']['away'].get('probablePitcher', {})
        home_sp = game['teams']['home'].get('probablePitcher', {})
        
        message += "**▼ 🆚 先発投手**\n```ansi\n"
        if away_sp.get('fullName'):
            message += f"[2;34m{away_name}[0m: {away_sp.get('fullName', '未定')}\n"
        else:
            message += f"[2;34m{away_name}[0m: 未定\n"
            
        if home_sp.get('fullName'):
            message += f"[2;31m{home_name}[0m: {home_sp.get('fullName', '未定')}\n"
        else:
            message += f"[2;31m{home_name}[0m: 未定\n"
        message += "```\n\n"
        
        # 中継ぎ陣
        away_bullpen_era = away_data.get('stats', {}).get('pitching', {}).get('bullpenAggregate', {}).get('era', 'N/A')
        home_bullpen_era = home_data.get('stats', {}).get('pitching', {}).get('bullpenAggregate', {}).get('era', 'N/A')
        
        message += "**▼ ⚾ 中継ぎ陣**\n```ansi\n"
        message += f"[2;34m{away_name}[0m: 防御率 {away_bullpen_era}\n"
        message += f"[2;31m{home_name}[0m: 防御率 {home_bullpen_era}\n"
        message += "```\n\n"
        
        # チーム打撃
        away_batting = away_data.get('stats', {}).get('batting', {})
        home_batting = home_data.get('stats', {}).get('batting', {})
        
        away_ops5 = away_data.get('ops5', {}).get('team_average_ops', 'N/A')
        away_ops10 = away_data.get('ops10', {}).get('team_average_ops', 'N/A')
        home_ops5 = home_data.get('ops5', {}).get('team_average_ops', 'N/A')
        home_ops10 = home_data.get('ops10', {}).get('team_average_ops', 'N/A')
        
        message += "**▼ 🏏 チーム打撃**\n```ansi\n"
        message += f"[2;34m{away_name}[0m: OPS {away_batting.get('ops', 'N/A')} | AVG: {away_batting.get('avg', 'N/A')}\n"
        message += f"  Last 5: {self.format_ops(away_ops5)} | Last 10: {self.format_ops(away_ops10)}\n"
        message += f"[2;31m{home_name}[0m: OPS {home_batting.get('ops', 'N/A')} | AVG: {home_batting.get('avg', 'N/A')}\n"
        message += f"  Last 5: {self.format_ops(home_ops5)} | Last 10: {self.format_ops(home_ops10)}\n"
        message += "```\n\n"
        
        # 比較表を追加
        message += self.create_comparison_table(away_name, home_name, away_data, home_data)
        
        return message
    
    def format_ops(self, value):
        """OPS値のフォーマット"""
        if value == 'N/A' or value is None:
            return 'N/A'
        return f"{value:.3f}"
    
    def create_comparison_table(self, away_name, home_name, away_data, home_data):
        """比較表の作成"""
        table = "**▼ 📊 スタッツ比較**\n```\n"
        table += f"{'指標':<12} | {away_name[:15]:<15} | {home_name[:15]:<15}\n"
        table += "-" * 50 + "\n"
        
        # 打撃統計
        away_batting = away_data.get('stats', {}).get('batting', {})
        home_batting = home_data.get('stats', {}).get('batting', {})
        
        stats_to_compare = [
            ('打率', away_batting.get('avg', 'N/A'), home_batting.get('avg', 'N/A')),
            ('OPS', away_batting.get('ops', 'N/A'), home_batting.get('ops', 'N/A')),
            ('得点', away_batting.get('runs', 'N/A'), home_batting.get('runs', 'N/A')),
            ('本塁打', away_batting.get('home_runs', 'N/A'), home_batting.get('home_runs', 'N/A')),
        ]
        
        # 投手統計
        away_pitching = away_data.get('stats', {}).get('pitching', {}).get('bullpenAggregate', {})
        home_pitching = home_data.get('stats', {}).get('pitching', {}).get('bullpenAggregate', {})
        
        stats_to_compare.extend([
            ('防御率', away_pitching.get('era', 'N/A'), home_pitching.get('era', 'N/A')),
            ('WHIP', away_pitching.get('whip', 'N/A'), home_pitching.get('whip', 'N/A')),
        ])
        
        for stat_name, away_val, home_val in stats_to_compare:
            table += f"{stat_name:<12} | {str(away_val):<15} | {str(home_val):<15}\n"
        
        table += "```\n"
        return table
    
    def send_game_stats(self, game, away_data, home_data):
        """1試合分の統計をDiscordに送信"""
        message = self.format_game_message(game, away_data, home_data)
        
        webhook = DiscordWebhook(url=self.webhook_url, content=message)
        response = webhook.execute()
        
        if response.status_code == 200:
            print(f"✅ 送信成功: {game['teams']['away']['team']['name']} vs {game['teams']['home']['team']['name']}")
        else:
            print(f"❌ 送信失敗: {response.status_code}")
    
    def publish_all_games(self):
        """全試合の統計を配信"""
        # 日付を取得
        jst_now = datetime.now()
        et_now = jst_now - timedelta(hours=13)
        
        if jst_now.hour < 13:
            date_str = et_now.strftime('%Y-%m-%d')
        else:
            date_str = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"対象日付: {date_str} (ET)")
        
        # 試合情報を取得
        games = self.client._make_request(f"schedule?sportId=1&date={date_str}")
        
        if not games or 'dates' not in games or not games['dates']:
            print("試合がありません")
            return
        
        game_list = games['dates'][0]['games']
        print(f"{len(game_list)}試合を配信します\n")
        
        # ヘッダーメッセージ
        header = f"# 📅 **MLB {date_str} 全試合統計**\n総試合数: {len(game_list)}\n\n"
        webhook = DiscordWebhook(url=self.webhook_url, content=header)
        webhook.execute()
        
        # 各試合を配信
        for i, game in enumerate(game_list, 1):
            print(f"[{i}/{len(game_list)}] 処理中...")
            
            away_id = game['teams']['away']['team']['id']
            home_id = game['teams']['home']['team']['id']
            
            # データ読み込み
            away_data = self.load_team_data(away_id)
            home_data = self.load_team_data(home_id)
            
            # データがない場合はスキップ
            if not away_data.get('stats') or not home_data.get('stats'):
                print(f"  ⚠️ データ不足のためスキップ")
                continue
            
            # 統計を送信
            self.send_game_stats(game, away_data, home_data)
            
            # レート制限対策（1秒待機）
            import time
            time.sleep(1)
        
        print("\n✅ 全試合の配信が完了しました！")

def main():
    """メイン実行関数"""
    try:
        publisher = DiscordStatsPublisher()
        publisher.publish_all_games()
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    main()