import requests
from datetime import datetime, timedelta
import json
import os

class MLBApiClient:
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com/api/v1"
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_schedule(self, date):
        """指定日の試合スケジュールを取得"""
        url = f"{self.base_url}/schedule"
        params = {
            'sportId': 1,
            'date': date,
            'hydrate': 'team,probablePitcher(note)'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return None
    
    def get_team_stats(self, team_id, season):
        """チームの統計情報を取得"""
        url = f"{self.base_url}/teams/{team_id}/stats"
        params = {
            'stats': 'season',
            'season': season,
            'group': 'hitting'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching team stats: {e}")
            return None
    
    def get_player_info(self, player_id):
        """選手の基本情報を取得"""
        url = f"{self.base_url}/people/{player_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('people', [{}])[0]
        except Exception as e:
            print(f"Error fetching player info: {e}")
            return {}
    
    def get_player_stats_by_season(self, player_id, season):
        """選手のシーズン統計を取得"""
        url = f"{self.base_url}/people/{player_id}/stats"
        params = {
            'stats': 'season',
            'season': season,
            'group': 'pitching'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching player stats: {e}")
            return None
    
    def get_player_splits(self, player_id, season):
        """選手のスプリット統計を取得"""
        url = f"{self.base_url}/people/{player_id}/stats"
        params = {
            'stats': 'vsPlayer',
            'season': season,
            'group': 'pitching'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching player splits: {e}")
            return None
    
    def get_team_roster(self, team_id):
        """チームのロースターを取得"""
        url = f"{self.base_url}/teams/{team_id}/roster"
        params = {
            'rosterType': 'active'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching team roster: {e}")
            return None
    
    def get_team_splits_vs_pitchers(self, team_id, season):
        """チームの対左右投手成績を取得"""
        url = f"{self.base_url}/teams/{team_id}/stats"
        params = {
            'stats': 'vsPlayer',
            'season': season,
            'group': 'hitting'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            result = {
                'vs_left': {'avg': '.250', 'ops': '.700'},
                'vs_right': {'avg': '.250', 'ops': '.700'}
            }
            
            if 'stats' in data:
                for stat in data['stats']:
                    if stat.get('group', {}).get('displayName') == 'vs Left':
                        splits = stat.get('splits', [])
                        if splits:
                            split_stats = splits[0].get('stat', {})
                            result['vs_left'] = {
                                'avg': split_stats.get('avg', '.250'),
                                'ops': split_stats.get('ops', '.700')
                            }
                    elif stat.get('group', {}).get('displayName') == 'vs Right':
                        splits = stat.get('splits', [])
                        if splits:
                            split_stats = splits[0].get('stat', {})
                            result['vs_right'] = {
                                'avg': split_stats.get('avg', '.250'),
                                'ops': split_stats.get('ops', '.700')
                            }
            
            return result
            
        except Exception as e:
            print(f"Error fetching team splits: {e}")
            return {
                'vs_left': {'avg': '.250', 'ops': '.700'},
                'vs_right': {'avg': '.250', 'ops': '.700'}
            }
    
    def calculate_team_recent_ops(self, team_id):
        """チームの過去5試合と10試合のOPSを計算"""
        try:
            # 現在日付から過去10日間の試合を取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=15)  # 余裕を持って15日前から
            
            url = f"{self.base_url}/schedule"
            params = {
                'sportId': 1,
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'teamId': team_id,
                'hydrate': 'linescore'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            schedule_data = response.json()
            
            # 試合データを収集
            game_stats = []
            dates = schedule_data.get('dates', [])
            
            for date in dates:
                for game in date.get('games', []):
                    if game.get('status', {}).get('codedGameState') in ['F', 'O']:  # 終了した試合のみ
                        game_pk = game.get('gamePk')
                        
                        # 試合の詳細統計を取得
                        stats_url = f"{self.base_url}/game/{game_pk}/boxscore"
                        try:
                            stats_response = requests.get(stats_url)
                            stats_response.raise_for_status()
                            boxscore = stats_response.json()
                            
                            # チームが home か away かを判定
                            if boxscore.get('teams', {}).get('home', {}).get('team', {}).get('id') == team_id:
                                team_stats = boxscore.get('teams', {}).get('home', {}).get('teamStats', {}).get('batting', {})
                            else:
                                team_stats = boxscore.get('teams', {}).get('away', {}).get('teamStats', {}).get('batting', {})
                            
                            if team_stats:
                                hits = int(team_stats.get('hits', 0))
                                at_bats = int(team_stats.get('atBats', 0))
                                walks = int(team_stats.get('baseOnBalls', 0))
                                hbp = int(team_stats.get('hitByPitch', 0))
                                sac_flies = int(team_stats.get('sacFlies', 0))
                                
                                # OBP計算
                                pa = at_bats + walks + hbp + sac_flies
                                if pa > 0:
                                    obp = (hits + walks + hbp) / pa
                                else:
                                    obp = 0
                                
                                # SLG計算（簡易版: 塁打数が取得できない場合は推定）
                                total_bases = int(team_stats.get('totalBases', hits * 1.5))  # 推定値
                                if at_bats > 0:
                                    slg = total_bases / at_bats
                                else:
                                    slg = 0
                                
                                ops = obp + slg
                                game_stats.append({
                                    'date': date.get('date'),
                                    'ops': ops
                                })
                        except:
                            continue
            
            # 最新の試合から順にソート
            game_stats.sort(key=lambda x: x['date'], reverse=True)
            
            # 過去5試合と10試合のOPS計算
            ops_5_games = 0.700  # デフォルト値
            ops_10_games = 0.700  # デフォルト値
            
            if len(game_stats) >= 5:
                ops_5_games = sum(g['ops'] for g in game_stats[:5]) / 5
            elif len(game_stats) > 0:
                ops_5_games = sum(g['ops'] for g in game_stats) / len(game_stats)
            
            if len(game_stats) >= 10:
                ops_10_games = sum(g['ops'] for g in game_stats[:10]) / 10
            elif len(game_stats) > 0:
                ops_10_games = sum(g['ops'] for g in game_stats) / len(game_stats)
            
            return {
                'last_5_games': round(ops_5_games, 3),
                'last_10_games': round(ops_10_games, 3)
            }
            
        except Exception as e:
            print(f"Error calculating recent OPS: {e}")
            return {
                'last_5_games': 0.700,
                'last_10_games': 0.700
            }