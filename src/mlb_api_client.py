"""
MLB Stats API クライアント
MLB公式APIを使用してデータを取得するモジュール
"""

import requests
from datetime import datetime, timedelta
import logging
import json
import os
import time
from typing import Dict, List, Optional, Tuple, Any

class MLBApiClient:
    """MLB Stats APIのクライアントクラス"""
    
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com"
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        self.cache_dir = "cache/splits_data"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_schedule(self, date=None):
        """指定日の試合スケジュールを取得"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/schedule",
                params={
                    'sportId': 1,
                    'date': date,
                    'hydrate': 'probablePitcher,team,linescore'  # 先発投手情報を含める
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching schedule: {str(e)}")
            return None
    
    def get_game_details(self, game_pk):
        """試合の詳細情報を取得"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1.1/game/{game_pk}/feed/live",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching game details: {str(e)}")
            return None
    
    def get_player_info(self, player_id):
        """選手の基本情報を取得"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/people/{player_id}",
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('people', [{}])[0] if data.get('people') else None
        except Exception as e:
            self.logger.error(f"Error fetching player info: {str(e)}")
            return None
    
    def get_player_stats_by_season(self, player_id, season=2025, stat_group="pitching"):
        """選手のシーズン統計を取得"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/people/{player_id}/stats",
                params={
                    'stats': 'season',
                    'season': season,
                    'group': stat_group,
                    'gameType': 'R'
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # 統計データを探す
            stats_list = data.get('stats', [])
            for stat_item in stats_list:
                if stat_item.get('type', {}).get('displayName') == 'season':
                    splits = stat_item.get('splits', [])
                    if splits:
                        return splits[0].get('stat', {})
            
            return {}
        except Exception as e:
            self.logger.error(f"Error fetching player stats: {str(e)}")
            return {}
    
    def get_player_splits(self, player_id, season=2025, stat_group="pitching"):
        """選手の対左右成績を取得（改善版）"""
        # キャッシュチェック
        cache_file = os.path.join(self.cache_dir, f"player_{player_id}_{season}_splits.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # キャッシュが24時間以内なら使用
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=24):
                    self.logger.info(f"Using cached splits data for player {player_id}")
                    return cache_data['data']
            except Exception as e:
                self.logger.warning(f"Cache read error: {e}")
        
        # APIから取得（リトライ機能付き）
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/people/{player_id}/stats",
                    params={
                        'stats': 'statSplits',
                        'season': season,
                        'group': stat_group,
                        'gameType': 'R',
                        'sitCodes': 'vl,vr'
                    },
                    timeout=30
                )
                
                if response.status_code == 500:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"500 error for player {player_id}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        self.logger.error(f"Max retries reached for player {player_id}")
                        return self._get_default_splits()
                
                response.raise_for_status()
                data = response.json()
                
                # データを解析
                result = self._parse_splits_data(data)
                
                # キャッシュに保存
                try:
                    cache_data = {
                        'player_id': player_id,
                        'season': season,
                        'data': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    self.logger.warning(f"Cache write error: {e}")
                
                return result
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Request error for player {player_id}: {e}, retrying...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.logger.error(f"Failed to get splits for player {player_id}: {e}")
                    return self._get_default_splits()
        
        return self._get_default_splits()
    
    def _parse_splits_data(self, data):
        """スプリットデータを解析"""
        result = {
            'vs_left': {'avg': .250, 'ops': .700},
            'vs_right': {'avg': .250, 'ops': .700}
        }
        
        stats_list = data.get('stats', [])
        for stat_item in stats_list:
            if stat_item.get('type', {}).get('displayName') == 'statSplits':
                splits = stat_item.get('splits', [])
                
                for split in splits:
                    split_name = split.get('split', {}).get('code', '')
                    stat = split.get('stat', {})
                    
                    if split_name == 'vl':  # vs Left
                        result['vs_left'] = {
                            'avg': stat.get('avg', .250),
                            'ops': stat.get('ops', .700)
                        }
                    elif split_name == 'vr':  # vs Right
                        result['vs_right'] = {
                            'avg': stat.get('avg', .250),
                            'ops': stat.get('ops', .700)
                        }
        
        return result
    
    def _get_default_splits(self):
        """デフォルトの対左右成績"""
        return {
            'vs_left': {'avg': .250, 'ops': .700},
            'vs_right': {'avg': .250, 'ops': .700}
        }
    
    def get_team_roster(self, team_id):
        """チームのロースターを取得"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/teams/{team_id}/roster",
                params={'rosterType': 'active'},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('roster', [])
        except Exception as e:
            self.logger.error(f"Error fetching team roster: {str(e)}")
            return []
    
    def get_team_stats(self, team_id, season=2025):
        """チームの統計を取得"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/teams/{team_id}/stats",
                params={
                    'stats': 'season',
                    'season': season,
                    'group': 'hitting',  # groupパラメータを追加
                    'gameType': 'R'
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # 統計データを探す（修正版）
            stats_list = data.get('stats', [])
            if stats_list and stats_list[0].get('splits'):
                return stats_list[0]['splits'][0].get('stat', {})
            
            return {}
        except Exception as e:
            self.logger.error(f"Error fetching team stats: {str(e)}")
            return {}
    
    def get_team_splits_vs_pitchers(self, team_id, season=2025):
        """チームの対左右投手成績を取得"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/teams/{team_id}/stats",
                params={
                    'stats': 'statSplits',
                    'season': season,
                    'group': 'hitting',
                    'gameType': 'R',
                    'sitCodes': 'vl,vr'
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            result = {
                'vs_left': {'avg': .250, 'ops': .700},
                'vs_right': {'avg': .250, 'ops': .700}
            }
            
            stats_list = data.get('stats', [])
            for stat_item in stats_list:
                if stat_item.get('type', {}).get('displayName') == 'statSplits':
                    splits = stat_item.get('splits', [])
                    
                    for split in splits:
                        split_name = split.get('split', {}).get('code', '')
                        stat = split.get('stat', {})
                        
                        if split_name == 'vl':
                            result['vs_left'] = {
                                'avg': stat.get('avg', .250),
                                'ops': stat.get('ops', .700)
                            }
                        elif split_name == 'vr':
                            result['vs_right'] = {
                                'avg': stat.get('avg', .250),
                                'ops': stat.get('ops', .700)
                            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching team splits: {str(e)}")
            return {
                'vs_left': {'avg': .250, 'ops': .700},
                'vs_right': {'avg': .250, 'ops': .700}
            }
    
    def calculate_team_recent_ops(self, team_id, games=5):
        """
        チームの過去N試合のOPSを計算
        
        Args:
            team_id (int): チームID
            games (int): 過去何試合分を計算するか（デフォルト5）
        
        Returns:
            float: 過去N試合のOPS（計算できない場合は0.700）
        """
        try:
            # 現在の日付から過去の日付範囲を計算
            end_date = datetime.now()
            start_date = end_date - timedelta(days=games * 2)  # 余裕を持って2倍の期間を取得
            
            # スケジュールAPIで過去の試合を取得
            params = {
                'teamId': team_id,
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'sportId': 1,
                'gameType': 'R'  # レギュラーシーズンのみ
            }
            
            response = self.session.get(
                f"{self.base_url}/api/v1/schedule",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # 完了した試合のみを抽出
            completed_games = []
            for date_info in data.get('dates', []):
                for game in date_info.get('games', []):
                    if game.get('status', {}).get('abstractGameState') == 'Final':
                        game_pk = game.get('gamePk')
                        if game_pk:
                            completed_games.append({
                                'gamePk': game_pk,
                                'date': game.get('gameDate')
                            })
            
            # 最新のN試合を取得
            completed_games.sort(key=lambda x: x['date'], reverse=True)
            recent_games = completed_games[:games]
            
            if len(recent_games) < games:
                self.logger.warning(f"Only {len(recent_games)} games found for team {team_id} in the last {games} games")
            
            # 各試合の打撃成績を取得
            total_hits = 0
            total_at_bats = 0
            total_walks = 0
            total_bases = 0
            
            for game_info in recent_games:
                game_pk = game_info['gamePk']
                
                # ボックススコアから打撃成績を取得
                boxscore_response = self.session.get(
                    f"{self.base_url}/api/v1.1/game/{game_pk}/feed/live",
                    timeout=30
                )
                boxscore_response.raise_for_status()
                boxscore_data = boxscore_response.json()
                
                # チームの打撃成績を探す
                teams_data = boxscore_data.get('liveData', {}).get('boxscore', {}).get('teams', {})
                
                for side in ['home', 'away']:
                    team_data = teams_data.get(side, {})
                    if team_data.get('team', {}).get('id') == team_id:
                        batting_stats = team_data.get('teamStats', {}).get('batting', {})
                        
                        # 必要な統計を収集
                        hits = batting_stats.get('hits', 0)
                        at_bats = batting_stats.get('atBats', 0)
                        walks = batting_stats.get('baseOnBalls', 0)
                        doubles = batting_stats.get('doubles', 0)
                        triples = batting_stats.get('triples', 0)
                        home_runs = batting_stats.get('homeRuns', 0)
                        
                        # 塁打数を計算
                        singles = hits - doubles - triples - home_runs
                        total_bases_game = singles + (2 * doubles) + (3 * triples) + (4 * home_runs)
                        
                        total_hits += hits
                        total_at_bats += at_bats
                        total_walks += walks
                        total_bases += total_bases_game
                        break
            
            # OPSを計算
            if total_at_bats > 0:
                # OBP (出塁率) = (安打 + 四球) / (打数 + 四球)
                obp = (total_hits + total_walks) / (total_at_bats + total_walks) if (total_at_bats + total_walks) > 0 else 0
                
                # SLG (長打率) = 塁打数 / 打数
                slg = total_bases / total_at_bats
                
                # OPS = OBP + SLG
                ops = obp + slg
                
                self.logger.info(f"Team {team_id} last {games} games: OPS={ops:.3f} (OBP={obp:.3f}, SLG={slg:.3f})")
                return round(ops, 3)
            else:
                self.logger.warning(f"No at-bats found for team {team_id} in recent games")
                return 0.700
                
        except Exception as e:
            self.logger.error(f"Error calculating recent OPS for team {team_id}: {str(e)}")
            return 0.700
    
    def calculate_team_recent_ops_with_cache(self, team_id, games=5):
        """キャッシュ機能付きの過去N試合OPS計算"""
        cache_dir = "cache/recent_ops"
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, f"team_{team_id}_last_{games}_games.json")
        
        # キャッシュチェック（6時間有効）
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=6):
                    self.logger.info(f"Using cached OPS for team {team_id} last {games} games")
                    return cache_data['ops']
            except Exception as e:
                self.logger.warning(f"Cache read error: {e}")
        
        # 実際の計算
        ops = self.calculate_team_recent_ops(team_id, games)
        
        # キャッシュに保存
        try:
            cache_data = {
                'team_id': team_id,
                'games': games,
                'ops': ops,
                'timestamp': datetime.now().isoformat()
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Cache write error: {e}")
        
        return ops
    
    def get_team_batting_stats(self, team_id, season=2025):
        """チームの打撃統計を取得（過去の試合OPSも含む）"""
        try:
            # 基本統計の取得
            stats = self.get_team_stats(team_id, season)
            
            if stats:
                # 過去5試合と10試合のOPSを計算（キャッシュ機能付き）
                ops_5_games = self.calculate_team_recent_ops_with_cache(team_id, games=5)
                ops_10_games = self.calculate_team_recent_ops_with_cache(team_id, games=10)
                
                # 統計に追加
                stats['recent_ops_5'] = ops_5_games
                stats['recent_ops_10'] = ops_10_games
                
                return stats
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting team batting stats: {str(e)}")
            return None