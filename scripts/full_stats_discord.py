 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Full Stats Discord System - 完全版統計Discord送信
全スタッツを含む完全なレポートを全試合分送信

実行: python -m scripts.full_stats_discord
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient
import time

class FullStatsDiscord:
    def __init__(self):
        self.client = MLBApiClient()
        self.discord_client = DiscordClient()
        self.jst = pytz.timezone('Asia/Tokyo')
        self.est = pytz.timezone('US/Eastern')
        self.pbp_cache = {}
        
    def get_complete_pitcher_stats(self, pitcher_id, season):
        """投手の完全統計を取得"""
        try:
            # 基本統計
            response = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=season&season={season}&group=pitching"
            )
            
            if not response or not response.get('stats'):
                return None
                
            season_stats = response['stats'][0].get('splits', [])
            if not season_stats:
                return None
                
            stats = season_stats[0]['stat']
            
            # FIP計算
            hr = stats.get('homeRuns', 0)
            bb = stats.get('baseOnBalls', 0)
            hbp = stats.get('hitByPitch', 0)
            k = stats.get('strikeOuts', 0)
            ip = float(stats.get('inningsPitched', '0'))
            
            fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / ip + 3.2 if ip > 0 else 0
            
            # K%, BB%計算
            batters_faced = stats.get('battersFaced', 0)
            k_pct = (k / batters_faced * 100) if batters_faced > 0 else 0
            bb_pct = (bb / batters_faced * 100) if batters_faced > 0 else 0
            
            # QS率計算
            qs_rate = self._calculate_qs_rate(pitcher_id, season)
            
            # GB%, FB%計算
            gb_fb = self._calculate_gb_fb_rate(pitcher_id, season)
            
            # 対左右成績（簡易版 - 時間短縮のため5試合のみ）
            vs_lr = self._get_vs_lr_quick(pitcher_id, season)
            
            # 前年度成績
            prev_response = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=season&season={season-1}&group=pitching"
            )
            
            prev_stats = None
            if prev_response and prev_response.get('stats'):
                prev_splits = prev_response['stats'][0].get('splits', [])
                if prev_splits:
                    prev = prev_splits[0]['stat']
                    prev_stats = {
                        'era': prev.get('era', 'N/A'),
                        'whip': prev.get('whip', 'N/A'),
                        'wins': prev.get('wins', 0),
                        'losses': prev.get('losses', 0),
                        'ip': prev.get('inningsPitched', '0')
                    }
            
            return {
                'current': {
                    'games': stats.get('gamesPlayed', 0),
                    'starts': stats.get('gamesStarted', 0),
                    'era': stats.get('era', 'N/A'),
                    'fip': f"{fip:.2f}" if fip > 0 else 'N/A',
                    'whip': stats.get('whip', 'N/A'),
                    'k_pct': f"{k_pct:.1f}%",
                    'bb_pct': f"{bb_pct:.1f}%",
                    'k_bb': f"{k_pct - bb_pct:.1f}%",
                    'wins': stats.get('wins', 0),
                    'losses': stats.get('losses', 0),
                    'ip': stats.get('inningsPitched', '0'),
                    'qs_rate': qs_rate,
                    'gb_pct': gb_fb['gb_pct'],
                    'fb_pct': gb_fb['fb_pct']
                },
                'vs_lr': vs_lr,
                'previous': prev_stats
            }
        except Exception as e:
            print(f"    エラー: {str(e)}")
            return None
            
    def _calculate_qs_rate(self, pitcher_id, season):
        """QS率を計算"""
        try:
            game_logs = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=gameLog&season={season}&group=pitching"
            )
            
            if not game_logs or not game_logs.get('stats'):
                return 'N/A'
                
            games = game_logs['stats'][0].get('splits', [])
            starts = [g for g in games if g['stat'].get('gamesStarted', 0) == 1]
            
            if not starts:
                return 'N/A'
                
            qs_count = sum(1 for g in starts 
                          if float(g['stat'].get('inningsPitched', '0')) >= 6.0 
                          and g['stat'].get('earnedRuns', 0) <= 3)
            
            return f"{(qs_count / len(starts) * 100):.1f}%"
        except:
            return 'N/A'
            
    def _calculate_gb_fb_rate(self, pitcher_id, season):
        """GB%, FB%を計算"""
        try:
            game_logs = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=gameLog&season={season}&group=pitching"
            )
            
            if not game_logs or not game_logs.get('stats'):
                return {'gb_pct': 'N/A', 'fb_pct': 'N/A'}
                
            total_gb = 0
            total_fb = 0
            total_outs = 0
            
            for game in game_logs['stats'][0].get('splits', []):
                stat = game['stat']
                gb = stat.get('groundOuts', 0)
                ao = stat.get('airOuts', 0)
                so = stat.get('strikeOuts', 0)
                
                field_outs = float(stat.get('inningsPitched', '0')) * 3 - so
                
                if field_outs > 0:
                    total_gb += gb
                    total_fb += ao
                    total_outs += field_outs
                    
            if total_outs > 0:
                gb_pct = f"{(total_gb / total_outs * 100):.1f}%"
                fb_pct = f"{(total_fb / total_outs * 100):.1f}%"
            else:
                gb_pct = fb_pct = 'N/A'
                
            return {'gb_pct': gb_pct, 'fb_pct': fb_pct}
        except:
            return {'gb_pct': 'N/A', 'fb_pct': 'N/A'}
            
    def _get_vs_lr_quick(self, pitcher_id, season):
        """対左右成績を取得（高速版 - 5試合のみ）"""
        try:
            game_logs = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=gameLog&season={season}&group=pitching"
            )
            
            if not game_logs or not game_logs.get('stats'):
                return {'vs_left': 'N/A', 'vs_right': 'N/A'}
                
            vs_left = {'pa': 0, 'ab': 0, 'h': 0}
            vs_right = {'pa': 0, 'ab': 0, 'h': 0}
            
            games = game_logs['stats'][0].get('splits', [])[:5]  # 5試合のみ
            
            for game in games:
                game_pk = game.get('game', {}).get('gamePk')
                if not game_pk:
                    continue
                    
                if game_pk in self.pbp_cache:
                    pbp = self.pbp_cache[game_pk]
                else:
                    pbp = self.client._make_request(f"game/{game_pk}/playByPlay")
                    if pbp:
                        self.pbp_cache[game_pk] = pbp
                    time.sleep(1)
                    
                if pbp and 'allPlays' in pbp:
                    for play in pbp['allPlays']:
                        matchup = play.get('matchup', {})
                        if matchup.get('pitcher', {}).get('id') != pitcher_id:
                            continue
                            
                        batter_side = matchup.get('batSide', {}).get('code')
                        event = play.get('result', {}).get('event', '')
                        
                        if not event:
                            continue
                            
                        stats = vs_left if batter_side == 'L' else vs_right
                        stats['pa'] += 1
                        
                        if event in ['Single', 'Double', 'Triple', 'Home Run']:
                            stats['ab'] += 1
                            stats['h'] += 1
                        elif event in ['Strikeout', 'Groundout', 'Flyout', 'Lineout', 
                                       'Pop Out', 'Grounded Into DP', 'Forceout']:
                            stats['ab'] += 1
                            
            left_avg = vs_left['h'] / vs_left['ab'] if vs_left['ab'] > 0 else 0
            right_avg = vs_right['h'] / vs_right['ab'] if vs_right['ab'] > 0 else 0
            
            return {
                'vs_left': f".{int(left_avg * 1000):03d}" if vs_left['ab'] > 0 else 'N/A',
                'vs_right': f".{int(right_avg * 1000):03d}" if vs_right['ab'] > 0 else 'N/A'
            }
        except:
            return {'vs_left': 'N/A', 'vs_right': 'N/A'}
            
    def format_full_game_report(self, game):
        """完全な試合レポートのフォーマット"""
        away_team = game['teams']['away']['team']['name']
        home_team = game['teams']['home']['team']['name']
        
        # 日本時間に変換
        game_time = datetime.fromisoformat(game['gameDate'].replace('Z', '+00:00'))
        jst_time = game_time.astimezone(self.jst)
        
        # 複数メッセージに分割
        messages = []
        
        # ヘッダーメッセージ
        header = f"**{away_team} @ {home_team}**\n"
        header += f"開始時刻: {jst_time.strftime('%m/%d %H:%M')} (日本時間)\n"
        header += "="*40 + "\n"
        messages.append(header)
        
        # 各チームの投手情報
        for team_type, team_name in [('away', away_team), ('home', home_team)]:
            pitcher = game['teams'][team_type].get('probablePitcher', {})
            
            if pitcher and pitcher.get('id'):
                pitcher_name = pitcher.get('fullName', '未定')
                pitcher_id = pitcher['id']
                
                print(f"    {pitcher_name}の統計を取得中...")
                stats = self.get_complete_pitcher_stats(pitcher_id, 2025)
                
                if stats and stats['current']:
                    current = stats['current']
                    vs_lr = stats['vs_lr']
                    
                    report = f"**{team_name} - {pitcher_name}**\n\n"
                    
                    # 2025年統計
                    report += f"**2025年成績** ({current['starts']}先発)\n"
                    report += f"ERA: {current['era']} | FIP: {current['fip']} | WHIP: {current['whip']}\n"
                    report += f"K%: {current['k_pct']} | BB%: {current['bb_pct']} | K-BB%: {current['k_bb']}\n"
                    report += f"GB%: {current['gb_pct']} | FB%: {current['fb_pct']} | QS率: {current['qs_rate']}\n"
                    report += f"対左: {vs_lr['vs_left']} | 対右: {vs_lr['vs_right']}\n"
                    report += f"{current['wins']}勝{current['losses']}敗 | {current['ip']}回\n"
                    
                    # 前年度成績
                    if stats['previous']:
                        prev = stats['previous']
                        report += f"\n**2024年成績** (参考)\n"
                        report += f"ERA: {prev['era']} | WHIP: {prev['whip']} | "
                        report += f"{prev['wins']}勝{prev['losses']}敗 | {prev['ip']}回\n"
                        
                    messages.append(report)
                else:
                    report = f"**{team_name} - {pitcher_name}**\n"
                    report += "2025年データなし\n"
                    messages.append(report)
            else:
                report = f"**{team_name} - 先発投手未定**\n"
                messages.append(report)
                
        return messages
        
    def run_full_discord_report(self):
        """完全版Discordレポートを実行"""
        print("MLB Full Stats Discord System - 全スタッツ版")
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
                    
        print(f"{len(games)}試合を検出。全試合を処理します。\n")
        
        # ヘッダーメッセージ
        header = f"**MLB 明日の試合予定 ({tomorrow_est})**\n"
        header += f"全{len(games)}試合 - 完全統計版\n"
        header += "="*50
        self.discord_client.send_text_message(header)
        time.sleep(2)
        
        # 各試合を処理
        for i, game in enumerate(games):
            print(f"\n試合 {i+1}/{len(games)} 処理中...")
            
            try:
                messages = self.format_full_game_report(game)
                
                # 各メッセージを送信
                for msg in messages:
                    self.discord_client.send_text_message(msg)
                    time.sleep(2)  # Discord制限対策
                    
                print(f"  ✓ 試合 {i+1} 完了")
                
            except Exception as e:
                print(f"  ✗ 試合 {i+1} エラー: {str(e)}")
                error_msg = f"試合 {i+1} の処理中にエラーが発生しました"
                self.discord_client.send_text_message(error_msg)
                
            # 試合間の待機
            time.sleep(3)
            
        # フッターメッセージ
        footer = "="*50 + "\n"
        footer += f"全{len(games)}試合の統計情報送信完了"
        self.discord_client.send_text_message(footer)
        
        print(f"\n処理完了！全{len(games)}試合を送信しました。")

if __name__ == "__main__":
    system = FullStatsDiscord()
    system.run_full_discord_report()