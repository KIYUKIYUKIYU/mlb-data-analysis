#!/usr/bin/env python3
"""
MLB Daily Report Generator with Japanese Names - Simplified Version
シンプル版 - 明日の試合を日本語でレポート
"""
import os
import sys
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import pytz
from pathlib import Path

class MLBReportJP:
    def __init__(self):
        # チーム名の日本語変換辞書
        self.team_names_jp = {
            "Arizona Diamondbacks": "ダイヤモンドバックス",
            "Atlanta Braves": "ブレーブス",
            "Baltimore Orioles": "オリオールズ",
            "Boston Red Sox": "レッドソックス",
            "Chicago Cubs": "カブス",
            "Chicago White Sox": "ホワイトソックス",
            "Cincinnati Reds": "レッズ",
            "Cleveland Guardians": "ガーディアンズ",
            "Colorado Rockies": "ロッキーズ",
            "Detroit Tigers": "タイガース",
            "Houston Astros": "アストロズ",
            "Kansas City Royals": "ロイヤルズ",
            "Los Angeles Angels": "エンゼルス",
            "Los Angeles Dodgers": "ドジャース",
            "Miami Marlins": "マーリンズ",
            "Milwaukee Brewers": "ブルワーズ",
            "Minnesota Twins": "ツインズ",
            "New York Mets": "メッツ",
            "New York Yankees": "ヤンキース",
            "Oakland Athletics": "アスレチックス",
            "Philadelphia Phillies": "フィリーズ",
            "Pittsburgh Pirates": "パイレーツ",
            "San Diego Padres": "パドレス",
            "San Francisco Giants": "ジャイアンツ",
            "Seattle Mariners": "マリナーズ",
            "St. Louis Cardinals": "カージナルス",
            "Tampa Bay Rays": "レイズ",
            "Texas Rangers": "レンジャーズ",
            "Toronto Blue Jays": "ブルージェイズ",
            "Washington Nationals": "ナショナルズ"
        }
        
        # 有名選手の日本語名
        self.player_names_jp = {
            "Shohei Ohtani": "大谷翔平",
            "Yoshinobu Yamamoto": "山本由伸",
            "Yu Darvish": "ダルビッシュ有",
            "Shota Imanaga": "今永昇太",
            "Masataka Yoshida": "吉田正尚",
            "Seiya Suzuki": "鈴木誠也"
        }
    
    def to_japanese_team(self, team_name):
        """チーム名を日本語に変換"""
        return self.team_names_jp.get(team_name, team_name)
    
    def to_japanese_player(self, player_name):
        """選手名を日本語に変換"""
        return self.player_names_jp.get(player_name, player_name)
    
    async def get_tomorrow_games(self):
        """明日の試合スケジュールを取得"""
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime('%Y-%m-%d')
        
        # MLB Stats APIから試合情報を取得
        url = f"https://statsapi.mlb.com/api/v1/schedule?date={date_str}&sportId=1"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('dates', [{}])[0].get('games', [])
                    else:
                        print(f"API エラー: {response.status}")
                        return []
            except Exception as e:
                print(f"エラー: {e}")
                return []
    
    def format_game_info(self, game):
        """試合情報をフォーマット"""
        home_team = game['teams']['home']['team']['name']
        away_team = game['teams']['away']['team']['name']
        
        home_team_jp = self.to_japanese_team(home_team)
        away_team_jp = self.to_japanese_team(away_team)
        
        game_time = game.get('gameDate', '')
        
        # 先発投手情報を取得
        home_pitcher = "未定"
        away_pitcher = "未定"
        
        if 'probablePitcher' in game['teams']['home']:
            pitcher_name = game['teams']['home']['probablePitcher']['fullName']
            home_pitcher = self.to_japanese_player(pitcher_name)
        
        if 'probablePitcher' in game['teams']['away']:
            pitcher_name = game['teams']['away']['probablePitcher']['fullName']
            away_pitcher = self.to_japanese_player(pitcher_name)
        
        return {
            'matchup': f"{away_team_jp} @ {home_team_jp}",
            'home_pitcher': home_pitcher,
            'away_pitcher': away_pitcher,
            'time': game_time
        }
    
    async def create_report(self):
        """明日の試合レポートを作成"""
        print("明日の試合情報を取得中...")
        games = await self.get_tomorrow_games()
        
        if not games:
            return "明日の試合情報が取得できませんでした。"
        
        # 日本時間の現在時刻
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        tomorrow = now_jst + timedelta(days=1)
        
        # レポート作成
        report_lines = [
            f"# 🏟️ MLB 明日の試合 - {tomorrow.strftime('%Y年%m月%d日')}",
            f"*作成時刻: {now_jst.strftime('%Y-%m-%d %H:%M:%S JST')}*",
            f"*試合数: {len(games)}試合*\n"
        ]
        
        # 各試合の情報
        for i, game in enumerate(games, 1):
            info = self.format_game_info(game)
            report_lines.append(f"## {i}. {info['matchup']}")
            report_lines.append(f"**先発予定:**")
            report_lines.append(f"- {info['away_pitcher']} vs {info['home_pitcher']}")
            report_lines.append("")  # 空行
        
        return "\n".join(report_lines)
    
    async def send_to_discord(self, webhook_url, message):
        """Discordに送信"""
        # 2000文字制限チェック
        if len(message) > 2000:
            message = message[:1997] + "..."
        
        async with aiohttp.ClientSession() as session:
            data = {"content": message}
            async with session.post(webhook_url, json=data) as response:
                if response.status == 204:
                    print("✅ Discordへの送信が完了しました！")
                    return True
                else:
                    print(f"❌ 送信エラー: {response.status}")
                    return False

async def main():
    # Discord Webhook URLの確認
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("エラー: DISCORD_WEBHOOK_URL が設定されていません")
        print("\n以下のコマンドで設定してください:")
        print("set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL")
        return
    
    # レポート作成
    reporter = MLBReportJP()
    report = await reporter.create_report()
    
    print("\n作成したレポート:")
    print("-" * 50)
    print(report)
    print("-" * 50)
    
    # Discordに送信
    print("\nDiscordに送信中...")
    await reporter.send_to_discord(webhook_url, report)

if __name__ == "__main__":
    # Windows環境の設定
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 実行
    asyncio.run(main())