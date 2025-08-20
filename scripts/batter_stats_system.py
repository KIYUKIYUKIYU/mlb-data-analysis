 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB Batter Stats System - 打者統計システム
打者の統計情報を取得してDiscordに送信

実行: python -m scripts.batter_stats_system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient
import time

class BatterStatsSystem:
    def __init__(self):
        self.client = MLBApiClient()
        self.discord_client = DiscordClient()
        self.jst = pytz.timezone('Asia/Tokyo')
        self.est = pytz.timezone('US/Eastern')
        
    def get_batter_stats(self, batter_id, season):
        """打者の統計を取得"""
        try:
            stats = {
                'current': self._get_season_stats(batter_id, season),
                'recent_5': self._get_recent_ops(batter_id, season, 5),
                'recent_10': self._get_recent_ops(batter_id, season, 10),
                'vs_left_right': self._get_vs_lr_stats_batter(batter_id, season)
            }
            return stats
        except Exception as e:
            print(f"    エラー: {str(e)}")
            return None
            
    def _get_season_stats(self, batter_id, season):
        """シーズン統計を取得"""
        try:
            response = self.client._make_request(
                f"people/{batter_id}/stats?stats=season&season={season}&group=hitting"
            )
            
            if not response or not response.get('stats'):
                return None
                
            season_stats = response['stats'][0].get('splits', [])
            if not season_stats:
                return None
                
            stats = season_stats[0]['stat']
            
            return {
                'games': stats.get('gamesPlayed', 0),
                'avg': stats.get('avg', '.000'),
                'obp': stats.get('obp', '.000'),
                'slg': stats.get('slg', '.000'),
                'ops': stats.get('ops', '.000'),
                'hr': stats.get('homeRuns', 0),
                'rbi': stats.get('rbi', 0),
                'sb': stats.get('stolenBases', 0),
                'hits': stats.get('hits', 0),
                'doubles': stats.get('doubles', 0),
                'triples': stats.get('triples', 0),
                'bb': stats.get('baseOnBalls', 0),
                'so': stats.get('strikeOuts', 0)
            }
        except:
            return None
            
    def _get_recent_ops(self, batter_id, season, games_count):
        """最近N試合のOPSを計算"""
        try:
            game_logs = self.client._make_request(
                f"people/{batter_id}/stats?stats=gameLog&season={season}&group=hitting"
            )
            
            if not game_logs or not game_logs.get('stats'):
                return 'N/A'
                
            games = game_logs['stats'][0].get('splits', [])[:games_count]
            
            if not games:
                return 'N/A'
                
            total_ab = 0
            total_h = 0
            total_bb = 0
            total_hbp = 0
            total_sf = 0
            total_tb = 0
            
            for game in games:
                stat = game['stat']
                ab = stat.get('atBats', 0)
                h = stat.get('hits', 0)
                bb = stat.get('baseOnBalls', 0)
                hbp = stat.get('hitByPitch', 0)
                sf = stat.get('sacFlies', 0)
                
                # 塁打数計算
                singles = h - stat.get('doubles', 0) - stat.get('triples', 0) - stat.get('homeRuns', 0)
                tb = singles + (2 * stat.get('doubles', 0)) + (3 * stat.get('triples', 0)) + (4 * stat.get('homeRuns', 0))
                
                total_ab += ab
                total_h += h
                total_bb += bb
                total_hbp += hbp
                total_sf += sf
                total_tb += tb
                
            # OPS計算
            pa = total_ab + total_bb + total_hbp + total_sf
            if pa > 0 and total_ab > 0:
                obp = (total_h + total_bb + total_hbp) / pa
                slg = total_tb / total_ab
                ops = obp + slg
                return f"{ops:.3f}"
            else:
                return 'N/A'
                
        except:
            return 'N/A'
            
    def _get_vs_lr_stats_batter(self, batter_id, season):
        """打者の対左右投手成績"""
        try:
            # 2025年はsplitsが使えないので簡易版
            return {
                'vs_left': 'N/A',
                'vs_right': 'N/A'
            }
        except:
            return {'vs_left': 'N/A', 'vs_right': 'N/A'}
            
    def format_lineup_report(self, team_name, lineup):
        """打線レポートのフォーマット"""
        report = f"**{team_name} - 予想打線**\n\n"
        
        for i, batter in enumerate(lineup[:9]):  # 1-9番打者
            if batter and batter.get('id'):
                batter_id = batter['id']
                batter_name = batter.get('fullName', 'Unknown')
                position = batter.get('position', '')
                
                stats = self.get_batter_stats(batter_id, 2025)
                
                if stats and stats['current']:
                    current = stats['current']
                    report += f"**{i+1}番 {position} {batter_name}**\n"
                    report += f"AVG: {current['avg']} | OPS: {current['ops']} | "
                    report += f"HR: {current['hr']} | RBI: {current['rbi']}\n"
                    report += f"最近5試合OPS: {stats['recent_5']} | "
                    report += f"最近10試合OPS: {stats['recent_10']}\n\n"
                else:
                    report += f"**{i+1}番 {position} {batter_name}**\n"
                    report += "2025年データなし\n\n"
                    
        return report
        
    def get_tomorrow_games_with_lineups(self):
        """明日の試合と予想打線を取得"""
        now_jst = datetime.now(self.jst)
        tomorrow_est = (now_jst - timedelta(hours=13) + timedelta(days=1)).date()
        
        schedule = self.client._make_request(
            f"schedule?sportId=1&date={tomorrow_est}&hydrate=probablePitcher,lineups"
        )
        
        if not schedule or not schedule.get('dates'):
            return []
            
        games = []
        for date in schedule['dates']:
            for game in date.get('games', []):
                if game['status']['abstractGameState'] == 'Preview':
                    games.append(game)
                    
        return games
        
    def run_quick_discord_report(self):
        """Discordへクイックレポート送信"""
        print("MLB Stats System - Discord送信用クイックレポート")
        print("="*50)
        
        games = self.get_tomorrow_games_with_lineups()
        if not games:
            self.discord_client.send_text_message("明日の試合はありません")
            return
            
        # 最初の3試合のみ処理（時間短縮）
        for i, game in enumerate(games[:3]):
            print(f"\n試合 {i+1}/3 処理中...")
            
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            
            report = f"**{away_team} @ {home_team}**\n"
            report += f"開始時刻: {game['gameDate']}\n\n"
            
            # 投手情報（簡易版）
            away_pitcher = game['teams']['away'].get('probablePitcher', {})
            home_pitcher = game['teams']['home'].get('probablePitcher', {})
            
            if away_pitcher:
                report += f"先発投手: {away_pitcher.get('fullName', '未定')}\n"
            if home_pitcher:
                report += f"先発投手: {home_pitcher.get('fullName', '未定')}\n"
                
            report += "\n" + "="*40 + "\n"
            
            # Discord送信
            self.discord_client.send_text_message(report)
            time.sleep(2)
            
        print("\nDiscord送信完了！")

if __name__ == "__main__":
    system = BatterStatsSystem()
    system.run_quick_discord_report()