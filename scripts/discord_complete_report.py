#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB Discord Complete Report - 完全版Discord配信
1試合の全情報を1メッセージで送信

実行: python -m scripts.discord_complete_report
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient
import time

class DiscordCompleteReport:
    def __init__(self):
        self.client = MLBApiClient()
        self.discord_client = DiscordClient()
        self.jst = pytz.timezone('Asia/Tokyo')
        self.est = pytz.timezone('US/Eastern')
        self.pbp_cache = {}
        
    def get_complete_pitcher_stats(self, pitcher_id, pitcher_name, season):
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
            
            # 対左右成績（簡易版）
            vs_lr = self._get_vs_lr_quick(pitcher_id, season)
            
            return {
                'name': pitcher_name,
                'games': stats.get('gamesPlayed', 0),
                'starts': stats.get('gamesStarted', 0),
                'wins': stats.get('wins', 0),
                'losses': stats.get('losses', 0),
                'era': stats.get('era', 'N/A'),
                'fip': f"{fip:.2f}" if fip > 0 else 'N/A',
                'whip': stats.get('whip', 'N/A'),
                'k_pct': f"{k_pct:.1f}%",
                'bb_pct': f"{bb_pct:.1f}%",
                'k_bb': f"{k_pct - bb_pct:.1f}%",
                'ip': stats.get('inningsPitched', '0'),
                'so': stats.get('strikeOuts', 0),
                'qs_rate': qs_rate,
                'gb_pct': gb_fb['gb_pct'],
                'fb_pct': gb_fb['fb_pct'],
                'vs_left': vs_lr['vs_left'],
                'vs_right': vs_lr['vs_right']
            }
        except Exception as e:
            print(f"    エラー: {str(e)}")
            return None
            
    def get_batter_stats(self, batter_id, batter_name, position, season):
        """打者の統計を取得"""
        try:
            # 基本統計
            response = self.client._make_request(
                f"people/{batter_id}/stats?stats=season&season={season}&group=hitting"
            )
            
            if not response or not response.get('stats'):
                return None
                
            season_stats = response['stats'][0].get('splits', [])
            if not season_stats:
                return None
                
            stats = season_stats[0]['stat']
            
            # 出場試合が少ない選手はスキップ
            if stats.get('atBats', 0) < 50:
                return None
            
            # 過去5試合/10試合のOPS
            recent_5_ops = self._get_recent_ops(batter_id, season, 5)
            recent_10_ops = self._get_recent_ops(batter_id, season, 10)
            
            return {
                'name': batter_name,
                'position': position,
                'games': stats.get('gamesPlayed', 0),
                'avg': stats.get('avg', '.000'),
                'obp': stats.get('obp', '.000'),
                'slg': stats.get('slg', '.000'),
                'ops': stats.get('ops', '.000'),
                'hr': stats.get('homeRuns', 0),
                'rbi': stats.get('rbi', 0),
                'sb': stats.get('stolenBases', 0),
                'recent_5_ops': recent_5_ops,
                'recent_10_ops': recent_10_ops,
                'vs_left': 'N/A',  # 2025年はsplitsデータなし
                'vs_right': 'N/A'
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
        """対左右成績を取得（5試合のみ）"""
        try:
            game_logs = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=gameLog&season={season}&group=pitching"
            )
            
            if not game_logs or not game_logs.get('stats'):
                return {'vs_left': 'N/A', 'vs_right': 'N/A'}
                
            vs_left = {'pa': 0, 'ab': 0, 'h': 0}
            vs_right = {'pa': 0, 'ab': 0, 'h': 0}
            
            games = game_logs['stats'][0].get('splits', [])[:5]
            
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
            
    def get_team_batting_stats(self, team_id, season):
        """チームの打撃統計を取得"""
        try:
            # チームのシーズン統計
            response = self.client._make_request(
                f"teams/{team_id}/stats?season={season}&stats=season&group=hitting"
            )
            
            if not response or not response.get('stats'):
                return None
                
            # シーズン統計を探す（最初のstatsを使用）
            if response['stats'] and response['stats'][0].get('splits'):
                stats = response['stats'][0]['splits'][0]['stat']
            else:
                return None
            
            # 過去5試合/10試合のチームOPS
            recent_5_ops = self._get_team_recent_ops(team_id, season, 5)
            recent_10_ops = self._get_team_recent_ops(team_id, season, 10)
            
            return {
                'games': stats.get('gamesPlayed', 0),
                'avg': stats.get('avg', '.000'),
                'obp': stats.get('obp', '.000'),
                'slg': stats.get('slg', '.000'),
                'ops': stats.get('ops', '.000'),
                'runs': stats.get('runs', 0),
                'hits': stats.get('hits', 0),
                'doubles': stats.get('doubles', 0),
                'triples': stats.get('triples', 0),
                'hr': stats.get('homeRuns', 0),
                'rbi': stats.get('rbi', 0),
                'sb': stats.get('stolenBases', 0),
                'bb': stats.get('baseOnBalls', 0),
                'so': stats.get('strikeOuts', 0),
                'recent_5_ops': recent_5_ops,
                'recent_10_ops': recent_10_ops
            }
        except Exception as e:
            print(f"    チーム打撃統計エラー: {str(e)}")
            return None
            
    def _get_team_recent_ops(self, team_id, season, games_count):
        """チームの最近N試合のOPSを計算"""
        try:
            # 過去30日間の全試合を取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            schedule = self.client._make_request(
                f"schedule?sportId=1&startDate={start_date.strftime('%Y-%m-%d')}&endDate={end_date.strftime('%Y-%m-%d')}"
            )
            
            if not schedule or not schedule.get('dates'):
                return 'N/A'
                
            # 終了した試合を新しい順に取得
            completed_games = []
            for date in reversed(schedule.get('dates', [])):
                for game in date.get('games', []):
                    # 指定チームが関わる試合か確認
                    if (game['teams']['away']['team']['id'] == team_id or 
                        game['teams']['home']['team']['id'] == team_id):
                        
                        if game['status']['abstractGameState'] == 'Final':
                            completed_games.append({
                                'gamePk': game['gamePk'],
                                'is_home': game['teams']['home']['team']['id'] == team_id
                            })
                            
                        if len(completed_games) >= games_count:
                            break
                            
                if len(completed_games) >= games_count:
                    break
                    
            if not completed_games:
                return 'N/A'
                
            # 各試合のチーム打撃成績を集計
            total_ab = 0
            total_h = 0
            total_bb = 0
            total_hbp = 0
            total_sf = 0
            total_2b = 0
            total_3b = 0
            total_hr = 0
            
            for game_info in completed_games[:games_count]:
                boxscore = self.client._make_request(f"game/{game_info['gamePk']}/boxscore")
                
                if boxscore and 'teams' in boxscore:
                    # 自チームのデータを取得
                    side = 'home' if game_info['is_home'] else 'away'
                    team_data = boxscore['teams'][side]
                    
                    if 'teamStats' in team_data and 'batting' in team_data['teamStats']:
                        batting = team_data['teamStats']['batting']
                        
                        ab = batting.get('atBats', 0)
                        h = batting.get('hits', 0)
                        bb = batting.get('baseOnBalls', 0)
                        hbp = batting.get('hitByPitch', 0)
                        sf = batting.get('sacFlies', 0)
                        doubles = batting.get('doubles', 0)
                        triples = batting.get('triples', 0)
                        hr = batting.get('homeRuns', 0)
                        
                        total_ab += ab
                        total_h += h
                        total_bb += bb
                        total_hbp += hbp
                        total_sf += sf
                        total_2b += doubles
                        total_3b += triples
                        total_hr += hr
                        
            # OPS計算
            if total_ab > 0:
                # 単打数 = 安打 - (二塁打 + 三塁打 + 本塁打)
                singles = total_h - (total_2b + total_3b + total_hr)
                # 塁打数
                total_bases = singles + (2 * total_2b) + (3 * total_3b) + (4 * total_hr)
                
                # 打席数
                pa = total_ab + total_bb + total_hbp + total_sf
                
                if pa > 0:
                    obp = (total_h + total_bb + total_hbp) / pa
                    slg = total_bases / total_ab
                    ops = obp + slg
                    return f"{ops:.3f}"
                    
            return 'N/A'
                
        except Exception as e:
            print(f"      過去{games_count}試合OPS計算エラー: {str(e)}")
            return 'N/A'
            
    def format_game_message(self, game_data):
        """1試合の完全メッセージを作成"""
        game_time = datetime.fromisoformat(game_data['gameDate'].replace('Z', '+00:00'))
        jst_time = game_time.astimezone(self.jst)
        
        message = f"**{game_data['away_team']} @ {game_data['home_team']}**\n"
        message += f"開始時刻: {jst_time.strftime('%m/%d %H:%M')} (日本時間)\n"
        message += "="*50 + "\n\n"
        
        # Away Team投手
        message += f"**【{game_data['away_team']}】**\n"
        if game_data.get('away_pitcher'):
            p = game_data['away_pitcher']
            message += f"先発: {p['name']} ({p['wins']}勝{p['losses']}敗)\n"
            message += f"ERA: {p['era']} | FIP: {p['fip']} | WHIP: {p['whip']}\n"
            message += f"K%: {p['k_pct']} | BB%: {p['bb_pct']} | K-BB%: {p['k_bb']}\n"
            message += f"GB%: {p['gb_pct']} | FB%: {p['fb_pct']} | QS率: {p['qs_rate']}\n"
            message += f"対左: {p['vs_left']} | 対右: {p['vs_right']}\n"
        else:
            message += "先発投手: 未定\n"
            
        # Away Teamチーム打撃成績
        if game_data.get('away_team_batting'):
            b = game_data['away_team_batting']
            message += f"\nチーム打撃成績:\n"
            message += f"AVG: {b['avg']} | OPS: {b['ops']} | 得点: {b['runs']} | 本塁打: {b['hr']}\n"
            message += f"過去5試合OPS: {b['recent_5_ops']} | 過去10試合OPS: {b['recent_10_ops']}\n"
                
        message += "\n"
        
        # Home Team投手
        message += f"**【{game_data['home_team']}】**\n"
        if game_data.get('home_pitcher'):
            p = game_data['home_pitcher']
            message += f"先発: {p['name']} ({p['wins']}勝{p['losses']}敗)\n"
            message += f"ERA: {p['era']} | FIP: {p['fip']} | WHIP: {p['whip']}\n"
            message += f"K%: {p['k_pct']} | BB%: {p['bb_pct']} | K-BB%: {p['k_bb']}\n"
            message += f"GB%: {p['gb_pct']} | FB%: {p['fb_pct']} | QS率: {p['qs_rate']}\n"
            message += f"対左: {p['vs_left']} | 対右: {p['vs_right']}\n"
        else:
            message += "先発投手: 未定\n"
            
        # Home Teamチーム打撃成績
        if game_data.get('home_team_batting'):
            b = game_data['home_team_batting']
            message += f"\nチーム打撃成績:\n"
            message += f"AVG: {b['avg']} | OPS: {b['ops']} | 得点: {b['runs']} | 本塁打: {b['hr']}\n"
            message += f"過去5試合OPS: {b['recent_5_ops']} | 過去10試合OPS: {b['recent_10_ops']}\n"
                
        message += "\n" + "="*50
        
        return message
        
    def run_discord_report(self):
        """Discord配信を実行"""
        print("MLB Discord Complete Report - 完全版配信")
        print("="*50)
        
        # 明日の試合を取得
        now_jst = datetime.now(self.jst)
        tomorrow_est = (now_jst - timedelta(hours=13) + timedelta(days=1)).date()
        
        print(f"明日({tomorrow_est})の試合を取得中...")
        
        schedule = self.client._make_request(
            f"schedule?sportId=1&date={tomorrow_est}&hydrate=probablePitcher,team"
        )
        
        if not schedule or not schedule.get('dates'):
            print("明日の試合はありません")
            self.discord_client.send_text_message("明日の試合はありません")
            return
            
        games_data = []
        
        for date in schedule['dates']:
            for game in date.get('games', []):
                if game['status']['abstractGameState'] != 'Preview':
                    continue
                    
                games_data.append({
                    'gamePk': game['gamePk'],
                    'gameDate': game['gameDate'],
                    'away_team': game['teams']['away']['team']['name'],
                    'home_team': game['teams']['home']['team']['name'],
                    'away_team_id': game['teams']['away']['team']['id'],
                    'home_team_id': game['teams']['home']['team']['id'],
                    'away_pitcher_info': game['teams']['away'].get('probablePitcher', {}),
                    'home_pitcher_info': game['teams']['home'].get('probablePitcher', {})
                })
                
        print(f"\n{len(games_data)}試合を検出。処理を開始します...\n")
        
        # ヘッダーメッセージ
        header = f"**MLB 明日の試合予定 ({tomorrow_est})**\n"
        header += f"全{len(games_data)}試合の詳細情報\n"
        header += "="*50
        self.discord_client.send_text_message(header)
        time.sleep(2)
        
        # 各試合を処理
        for i, game in enumerate(games_data):
            print(f"試合 {i+1}/{len(games_data)}: {game['away_team']} @ {game['home_team']}")
            
            try:
                # 投手統計取得
                for side in ['away', 'home']:
                    pitcher_info = game[f'{side}_pitcher_info']
                    if pitcher_info and pitcher_info.get('id'):
                        print(f"  {pitcher_info['fullName']}の統計を取得中...")
                        pitcher_stats = self.get_complete_pitcher_stats(
                            pitcher_info['id'], 
                            pitcher_info['fullName'],
                            2025
                        )
                        game[f'{side}_pitcher'] = pitcher_stats
                        
                # チーム打撃統計取得
                print("  チーム打撃統計を取得中...")
                game['away_team_batting'] = self.get_team_batting_stats(game['away_team_id'], 2025)
                game['home_team_batting'] = self.get_team_batting_stats(game['home_team_id'], 2025)
                
                # メッセージ作成と送信
                message = self.format_game_message(game)
                
                # Discord文字数制限（2000文字）を確認
                if len(message) > 1900:
                    # メッセージが長すぎる場合は簡略化
                    print("  メッセージ簡略化中...")
                    message = self.format_game_message(game)
                    
                self.discord_client.send_text_message(message)
                print(f"  ✓ 試合 {i+1} 配信完了")
                
            except Exception as e:
                print(f"  ✗ 試合 {i+1} エラー: {str(e)}")
                error_msg = f"試合 {i+1} ({game['away_team']} @ {game['home_team']}) の処理中にエラーが発生しました"
                self.discord_client.send_text_message(error_msg)
                
            time.sleep(3)  # Discord制限対策
            
        # 完了通知
        footer = "="*50 + "\n"
        footer += f"全{len(games_data)}試合の配信完了"
        self.discord_client.send_text_message(footer)
        
        print(f"\n処理完了！全{len(games_data)}試合を配信しました。")

if __name__ == "__main__":
    system = DiscordCompleteReport()
    system.run_discord_report()