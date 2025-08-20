 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB Cached Stats System - キャッシュ機能付き
Play-by-playデータをキャッシュして効率化

実行: python -m scripts.cached_stats_system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient
import time
import traceback

class CachedStatsSystem:
    def __init__(self):
        self.client = MLBApiClient()
        self.discord_client = DiscordClient()
        self.jst = pytz.timezone('Asia/Tokyo')
        self.est = pytz.timezone('US/Eastern')
        # Play-by-playキャッシュを初期化
        self.pbp_cache = {}
        
    def _get_pbp_with_cache(self, game_pk):
        """キャッシュ付きでPlay-by-playデータを取得"""
        if game_pk in self.pbp_cache:
            print(f"        キャッシュから取得: {game_pk}")
            return self.pbp_cache[game_pk]
        
        print(f"        APIから取得: {game_pk}")
        pbp = self.client._make_request(f"game/{game_pk}/playByPlay")
        
        if pbp:
            self.pbp_cache[game_pk] = pbp
            
        # API制限対策 - Play-by-play取得後は必ず2秒待機
        time.sleep(2)
        
        return pbp
        
    def get_pitcher_stats(self, pitcher_id, season):
        """投手の全統計を取得（エラーハンドリング付き）"""
        try:
            stats = {
                'current': self._get_season_stats(pitcher_id, season),
                'previous': self._get_season_stats(pitcher_id, season - 1),
                'vs_left_right': self._get_vs_lr_stats(pitcher_id, season),
                'recent_games': self._get_recent_games(pitcher_id, season)
            }
            return stats
        except Exception as e:
            print(f"    エラー: 投手ID {pitcher_id} の統計取得中にエラー: {str(e)}")
            return {
                'current': None,
                'previous': None,
                'vs_left_right': {'vs_left': 'N/A', 'vs_right': 'N/A'},
                'recent_games': []
            }
        
    def _get_season_stats(self, pitcher_id, season):
        """シーズン統計を取得（エラーハンドリング付き）"""
        try:
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
            
            if ip > 0:
                fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / ip + 3.2
            else:
                fip = 0
                
            # K%, BB%計算
            batters_faced = stats.get('battersFaced', 0)
            k_pct = (k / batters_faced * 100) if batters_faced > 0 else 0
            bb_pct = (bb / batters_faced * 100) if batters_faced > 0 else 0
            
            # QS率計算（Game Logから）
            qs_rate = self._calculate_qs_rate(pitcher_id, season)
            
            # GB%, FB%計算
            gb_fb = self._calculate_gb_fb_rate(pitcher_id, season)
            
            return {
                'season': season,
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
            }
        except Exception as e:
            print(f"      シーズン統計エラー: {str(e)}")
            return None
        
    def _calculate_qs_rate(self, pitcher_id, season):
        """QS率を計算（エラーハンドリング付き）"""
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
        """GB%, FB%を計算（エラーハンドリング付き）"""
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
                
                # 三振を除いたアウト数
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
        
    def _get_vs_lr_stats(self, pitcher_id, season):
        """対左右成績を取得（キャッシュ機能付き）"""
        try:
            print(f"      対左右成績を取得中...")
            game_logs = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=gameLog&season={season}&group=pitching"
            )
            
            if not game_logs or not game_logs.get('stats'):
                return {'vs_left': 'N/A', 'vs_right': 'N/A'}
                
            vs_left = {'pa': 0, 'ab': 0, 'h': 0}
            vs_right = {'pa': 0, 'ab': 0, 'h': 0}
            
            # 最新10試合を維持（データの精度を保つ）
            games = game_logs['stats'][0].get('splits', [])[:10]
            
            for i, game in enumerate(games):
                game_pk = game.get('game', {}).get('gamePk')
                if not game_pk:
                    continue
                    
                print(f"      試合 {i+1}/10 のPlay-by-play取得中...")
                    
                try:
                    # キャッシュ機能を使用
                    pbp = self._get_pbp_with_cache(game_pk)
                    
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
                except Exception as e:
                    print(f"        警告: 試合 {game_pk} の処理でエラー: {str(e)}")
                    continue
                        
            # 被打率計算
            left_avg = vs_left['h'] / vs_left['ab'] if vs_left['ab'] > 0 else 0
            right_avg = vs_right['h'] / vs_right['ab'] if vs_right['ab'] > 0 else 0
            
            print(f"      対左右成績取得完了: 左{vs_left['ab']}打数, 右{vs_right['ab']}打数")
            
            return {
                'vs_left': f".{int(left_avg * 1000):03d}" if vs_left['ab'] > 0 else 'N/A',
                'vs_right': f".{int(right_avg * 1000):03d}" if vs_right['ab'] > 0 else 'N/A'
            }
        except Exception as e:
            print(f"      対左右成績エラー: {str(e)}")
            return {'vs_left': 'N/A', 'vs_right': 'N/A'}
        
    def _get_recent_games(self, pitcher_id, season):
        """最近の試合成績を取得（エラーハンドリング付き）"""
        try:
            game_logs = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=gameLog&season={season}&group=pitching"
            )
            
            if not game_logs or not game_logs.get('stats'):
                return []
                
            games = game_logs['stats'][0].get('splits', [])[:5]  # 最新5試合
            
            recent = []
            for game in games:
                stat = game['stat']
                date = game.get('date', 'N/A')
                opponent = game.get('team', {}).get('name', 'N/A')
                
                recent.append({
                    'date': date,
                    'opponent': opponent,
                    'ip': stat.get('inningsPitched', '0'),
                    'er': stat.get('earnedRuns', 0),
                    'k': stat.get('strikeOuts', 0),
                    'bb': stat.get('baseOnBalls', 0),
                    'h': stat.get('hits', 0)
                })
                
            return recent
        except:
            return []
        
    def format_pitcher_report(self, pitcher_name, stats):
        """投手レポートのフォーマット"""
        current = stats['current']
        previous = stats['previous']
        vs_lr = stats['vs_left_right']
        recent = stats['recent_games']
        
        report = f"**{pitcher_name} - 詳細統計**\n\n"
        
        # 現在のシーズン統計
        if current:
            report += f"**2025年シーズン統計** ({current['starts']}先発)\n"
            report += f"ERA: {current['era']} | FIP: {current['fip']} | WHIP: {current['whip']}\n"
            report += f"K%: {current['k_pct']} | BB%: {current['bb_pct']} | K-BB%: {current['k_bb']}\n"
            report += f"GB%: {current['gb_pct']} | FB%: {current['fb_pct']} | QS率: {current['qs_rate']}\n"
            report += f"対左打者: {vs_lr['vs_left']} | 対右打者: {vs_lr['vs_right']}\n\n"
        else:
            report += "**2025年シーズン統計**: データなし\n\n"
            
        # 前年度統計（データ不足の場合に重要）
        if previous:
            report += f"**2024年シーズン統計** (参考)\n"
            report += f"ERA: {previous['era']} | FIP: {previous['fip']} | WHIP: {previous['whip']}\n"
            report += f"{previous['wins']}勝{previous['losses']}敗 | {previous['ip']}回投球\n\n"
            
        # 最近の試合
        if recent:
            report += "**最近5試合**\n"
            for i, game in enumerate(recent[:3]):  # 3試合のみ表示
                report += f"{game['date']}: vs {game['opponent']} - "
                report += f"{game['ip']}回 {game['er']}失点 {game['k']}K {game['bb']}BB\n"
                
        # データ不足の場合の注記
        if current and current['starts'] < 5:
            report += f"\n⚠️ 注意: 2025年は{current['starts']}先発のみのため、統計の信頼性に注意"
            
        return report
        
    def get_tomorrow_games(self):
        """明日の試合を取得（日本時間基準）"""
        now_jst = datetime.now(self.jst)
        # 明日の日付を計算
        tomorrow_est = (now_jst - timedelta(hours=13) + timedelta(days=1)).date()
        
        print(f"明日の試合を取得中... (EST: {tomorrow_est})")
        
        try:
            schedule = self.client._make_request(
                f"schedule?sportId=1&date={tomorrow_est}&hydrate=probablePitcher"
            )
            
            if not schedule or not schedule.get('dates'):
                return []
                
            games = []
            for date in schedule['dates']:
                for game in date.get('games', []):
                    if game['status']['abstractGameState'] == 'Preview':
                        game_info = {
                            'gamePk': game['gamePk'],
                            'teams': {
                                'away': {
                                    'name': game['teams']['away']['team']['name'],
                                    'pitcher': game['teams']['away'].get('probablePitcher', {})
                                },
                                'home': {
                                    'name': game['teams']['home']['team']['name'],
                                    'pitcher': game['teams']['home'].get('probablePitcher', {})
                                }
                            },
                            'gameDate': game['gameDate']
                        }
                        games.append(game_info)
                        
            return games
        except Exception as e:
            print(f"試合情報取得エラー: {str(e)}")
            return []
        
    def run_cached_report(self):
        """キャッシュ機能付きレポートを実行"""
        print("MLB Cached Stats System - キャッシュ機能付き")
        print("="*50)
        print(f"キャッシュサイズ: {len(self.pbp_cache)} 試合")
        
        games = self.get_tomorrow_games()
        if not games:
            print("明日の試合はありません")
            return
            
        print(f"\n明日は{len(games)}試合あります。全試合を処理します...\n")
        
        success_count = 0
        error_count = 0
        
        for i, game in enumerate(games):
            print(f"\n========== 試合 {i+1}/{len(games)} ==========")
            
            try:
                away_pitcher = game['teams']['away']['pitcher']
                home_pitcher = game['teams']['home']['pitcher']
                
                report = f"**{game['teams']['away']['name']} @ {game['teams']['home']['name']}**\n"
                report += f"開始時刻: {game['gameDate']}\n\n"
                
                # 各投手の統計を取得
                for team, pitcher in [('Away', away_pitcher), ('Home', home_pitcher)]:
                    if pitcher and pitcher.get('id'):
                        pitcher_name = pitcher.get('fullName', 'Unknown')
                        pitcher_id = pitcher['id']
                        
                        print(f"  {pitcher_name}の統計を取得中...")
                        stats = self.get_pitcher_stats(pitcher_id, 2025)
                        
                        report += self.format_pitcher_report(pitcher_name, stats)
                        report += "\n" + "="*50 + "\n\n"
                    else:
                        report += f"{team}投手: 未定\n\n"
                        
                # 結果を表示
                print(report[:300] + "...")  # 最初の300文字を表示
                print(f"  ✓ 試合 {i+1} 完了")
                print(f"  キャッシュサイズ: {len(self.pbp_cache)} 試合")
                success_count += 1
                
            except Exception as e:
                print(f"  ✗ 試合 {i+1} エラー: {str(e)}")
                error_count += 1
                traceback.print_exc()
                
            # API制限対策
            print("  待機中...")
            time.sleep(1)  # Play-by-playは個別に2秒待機するので、ここは1秒で十分
            
        print(f"\n処理完了: 成功 {success_count}試合, エラー {error_count}試合")
        print(f"最終キャッシュサイズ: {len(self.pbp_cache)} 試合")

if __name__ == "__main__":
    system = CachedStatsSystem()
    system.run_cached_report()