#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Combined Stats Discord System - 投手・打者統合版
Discord送信用の統合システム

実行: python -m scripts.combined_stats_discord
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient
import time

class CombinedStatsDiscord:
    def __init__(self):
        self.client = MLBApiClient()
        self.discord_client = DiscordClient()
        self.jst = pytz.timezone('Asia/Tokyo')
        self.est = pytz.timezone('US/Eastern')
        
    def get_simple_pitcher_stats(self, pitcher_id):
        """投手の簡易統計（高速版）"""
        try:
            response = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=season&season=2025&group=pitching"
            )
            
            if not response or not response.get('stats'):
                return None
                
            season_stats = response['stats'][0].get('splits', [])
            if not season_stats:
                return None
                
            stats = season_stats[0]['stat']
            
            return {
                'era': stats.get('era', 'N/A'),
                'whip': stats.get('whip', 'N/A'),
                'wins': stats.get('wins', 0),
                'losses': stats.get('losses', 0),
                'so': stats.get('strikeOuts', 0),
                'ip': stats.get('inningsPitched', '0')
            }
        except:
            return None
            
    def format_game_report(self, game):
        """試合レポートのフォーマット"""
        away_team = game['teams']['away']['team']['name']
        home_team = game['teams']['home']['team']['name']
        
        # 日本時間に変換
        game_time = datetime.fromisoformat(game['gameDate'].replace('Z', '+00:00'))
        jst_time = game_time.astimezone(self.jst)
        
        report = f"**{away_team} @ {home_team}**\n"
        report += f"開始時刻: {jst_time.strftime('%m/%d %H:%M')} (日本時間)\n\n"
        
        # 投手情報
        for team_type, team_name in [('away', away_team), ('home', home_team)]:
            pitcher = game['teams'][team_type].get('probablePitcher', {})
            
            if pitcher and pitcher.get('id'):
                pitcher_name = pitcher.get('fullName', '未定')
                pitcher_id = pitcher['id']
                
                stats = self.get_simple_pitcher_stats(pitcher_id)
                
                if stats:
                    report += f"**{team_name} - {pitcher_name}**\n"
                    report += f"ERA: {stats['era']} | WHIP: {stats['whip']} | "
                    report += f"{stats['wins']}勝{stats['losses']}敗 | "
                    report += f"{stats['ip']}回 {stats['so']}K\n\n"
                else:
                    report += f"**{team_name} - {pitcher_name}**\n"
                    report += "2025年データなし\n\n"
            else:
                report += f"**{team_name} - 先発投手未定**\n\n"
                
        return report
        
    def run_discord_report(self, max_games=5):
        """Discordレポートを実行"""
        print("MLB Combined Stats - Discord送信")
        print("="*50)
        
        # 明日の試合を取得
        now_jst = datetime.now(self.jst)
        tomorrow_est = (now_jst - timedelta(hours=13) + timedelta(days=1)).date()
        
        print(f"明日({tomorrow_est})の試合を取得中...")
        
        schedule = self.client._make_request(
            f"schedule?sportId=1&date={tomorrow_est}&hydrate=probablePitcher"
        )
        
        if not schedule or not schedule.get('dates'):
            self.discord_client.send_text_message("明日の試合はありません")
            return
            
        games = []
        for date in schedule['dates']:
            for game in date.get('games', []):
                if game['status']['abstractGameState'] == 'Preview':
                    games.append(game)
                    
        print(f"{len(games)}試合を検出。最初の{min(max_games, len(games))}試合を処理します。\n")
        
        # ヘッダーメッセージ
        header = f"**MLB 明日の試合予定 ({tomorrow_est})**\n"
        header += f"全{len(games)}試合\n"
        header += "="*40
        self.discord_client.send_text_message(header)
        
        # 各試合を処理
        for i, game in enumerate(games[:max_games]):
            print(f"試合 {i+1}/{min(max_games, len(games))} 処理中...")
            
            report = self.format_game_report(game)
            self.discord_client.send_text_message(report)
            
            time.sleep(2)  # Discord制限対策
            
        # フッターメッセージ
        footer = "="*40 + "\n"
        footer += f"以上、{min(max_games, len(games))}試合の情報でした。"
        self.discord_client.send_text_message(footer)
        
        print("\nDiscord送信完了！")

if __name__ == "__main__":
    system = CombinedStatsDiscord()
    # 5試合まで送信（変更可能）
    system.run_discord_report(max_games=5)