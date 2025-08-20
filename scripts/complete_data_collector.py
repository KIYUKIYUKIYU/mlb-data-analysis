"""
MLB完全データ収集システム
過去N試合のOPS、先発投手情報などを確実に取得
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.mlb_api_client import MLBApiClient
import time


class CompleteDataCollector:
    def __init__(self):
        self.client = MLBApiClient()
        
    def get_recent_games_stats(self, team_id: int, num_games: int = 10) -> Dict:
        """過去N試合の打撃成績を取得"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 30日前から検索
        
        # スケジュール取得
        schedule = self.client._make_request(
            f"schedule?teamId={team_id}&startDate={start_date.strftime('%Y-%m-%d')}"
            f"&endDate={end_date.strftime('%Y-%m-%d')}&sportId=1"
        )
        
        if not schedule or not schedule.get('dates'):
            return {'last5': None, 'last10': None}
            
        # 終了した試合を収集
        finished_games = []
        for date in reversed(schedule['dates']):  # 新しい順
            for game in date.get('games', []):
                if game['status']['codedGameState'] == 'F':  # 終了試合
                    game_pk = game['gamePk']
                    finished_games.append({
                        'gamePk': game_pk,
                        'date': game['gameDate'],
                        'home': game['teams']['home']['team']['id'] == team_id
                    })
                    
        # 最新N試合を取得
        recent_games = finished_games[:num_games]
        
        # 各試合の詳細統計を取得
        ops_last5 = []
        ops_last10 = []
        
        for i, game_info in enumerate(recent_games[:10]):
            game_stats = self._get_game_team_stats(game_info['gamePk'], team_id, game_info['home'])
            
            if game_stats and 'ops' in game_stats:
                if i < 5:
                    ops_last5.append(float(game_stats['ops']))
                ops_last10.append(float(game_stats['ops']))
                
            time.sleep(0.2)  # API制限対策
            
        # OPS計算
        result = {
            'last5': round(sum(ops_last5) / len(ops_last5), 3) if ops_last5 else None,
            'last10': round(sum(ops_last10) / len(ops_last10), 3) if ops_last10 else None,
            'last5_games': len(ops_last5),
            'last10_games': len(ops_last10)
        }
        
        return result
        
    def _get_game_team_stats(self, game_pk: int, team_id: int, is_home: bool) -> Dict:
        """特定試合のチーム打撃統計を取得"""
        boxscore = self.client._make_request(f"game/{game_pk}/boxscore")
        
        if not boxscore:
            return {}
            
        try:
            team_type = 'home' if is_home else 'away'
            team_stats = boxscore['teams'][team_type]['teamStats']['batting']
            
            # OPS計算 (OBP + SLG)
            obp = float(team_stats.get('obp', 0))
            slg = float(team_stats.get('slg', 0))
            ops = obp + slg
            
            return {
                'avg': team_stats.get('avg', '.000'),
                'obp': team_stats.get('obp', '.000'),
                'slg': team_stats.get('slg', '.000'),
                'ops': f"{ops:.3f}",
                'hits': team_stats.get('hits', 0),
                'runs': team_stats.get('runs', 0)
            }
        except:
            return {}
            
    def get_probable_pitchers_enhanced(self, game_data: Dict) -> Dict:
        """複数の方法で先発投手を取得"""
        result = {
            'away': {'name': '未定', 'id': None, 'stats': {}},
            'home': {'name': '未定', 'id': None, 'stats': {}}
        }
        
        game_pk = game_data['gamePk']
        
        # 方法1: 通常のprobablePitcher
        away_pitcher = game_data['teams']['away'].get('probablePitcher', {})
        home_pitcher = game_data['teams']['home'].get('probablePitcher', {})
        
        if away_pitcher.get('id'):
            result['away']['name'] = away_pitcher.get('fullName', '未定')
            result['away']['id'] = away_pitcher.get('id')
            
        if home_pitcher.get('id'):
            result['home']['name'] = home_pitcher.get('fullName', '未定')
            result['home']['id'] = home_pitcher.get('id')
            
        # 方法2: game contentから取得
        if result['away']['id'] is None or result['home']['id'] is None:
            content = self.client._make_request(f"game/{game_pk}/content")
            
            if content and 'gameData' in content:
                probables = content['gameData'].get('probablePitchers', {})
                
                if not result['away']['id'] and probables.get('away'):
                    result['away']['name'] = probables['away'].get('fullName', '未定')
                    result['away']['id'] = probables['away'].get('id')
                    
                if not result['home']['id'] and probables.get('home'):
                    result['home']['name'] = probables['home'].get('fullName', '未定')
                    result['home']['id'] = probables['home'].get('id')
                    
        # 先発投手の成績を取得
        for team in ['away', 'home']:
            if result[team]['id']:
                pitcher_stats = self._get_pitcher_current_stats(result[team]['id'])
                result[team]['stats'] = pitcher_stats
                
        return result
        
    def _get_pitcher_current_stats(self, pitcher_id: int) -> Dict:
        """投手の今季成績を取得"""
        stats = self.client._make_request(
            f"people/{pitcher_id}/stats?stats=season&season=2024&group=pitching"
        )
        
        if not stats or not stats.get('stats'):
            return {}
            
        try:
            stat_line = stats['stats'][0]['splits'][0]['stat']
            return {
                'era': stat_line.get('era', '-.--'),
                'whip': stat_line.get('whip', '-.--'),
                'wins': stat_line.get('wins', 0),
                'losses': stat_line.get('losses', 0),
                'strikeouts': stat_line.get('strikeOuts', 0),
                'innings': stat_line.get('inningsPitched', '0.0')
            }
        except:
            return {}
            
    def get_complete_matchup_data(self, game_data: Dict) -> Dict:
        """完全な対戦データを収集"""
        away_team = game_data['teams']['away']['team']
        home_team = game_data['teams']['home']['team']
        
        print(f"\n収集中: {away_team['name']} @ {home_team['name']}")
        
        # 先発投手情報
        pitchers = self.get_probable_pitchers_enhanced(game_data)
        
        # チーム成績
        away_season = self._get_team_season_stats(away_team['id'])
        home_season = self._get_team_season_stats(home_team['id'])
        
        # 過去N試合のOPS
        print("  過去試合のOPS計算中...")
        away_recent = self.get_recent_games_stats(away_team['id'], 10)
        home_recent = self.get_recent_games_stats(home_team['id'], 10)
        
        # 投手陣成績
        away_pitching = self._get_team_pitching_stats(away_team['id'])
        home_pitching = self._get_team_pitching_stats(home_team['id'])
        
        return {
            'game_id': game_data['gamePk'],
            'game_date': game_data['gameDate'],
            'away': {
                'team': away_team['name'],
                'team_id': away_team['id'],
                'starter': pitchers['away'],
                'batting': {
                    'avg': away_season.get('avg', '.000'),
                    'ops': away_season.get('ops', '.000'),
                    'runs': away_season.get('runs', 0),
                    'last5_ops': away_recent['last5'] or 'N/A',
                    'last10_ops': away_recent['last10'] or 'N/A'
                },
                'pitching': away_pitching
            },
            'home': {
                'team': home_team['name'],
                'team_id': home_team['id'],
                'starter': pitchers['home'],
                'batting': {
                    'avg': home_season.get('avg', '.000'),
                    'ops': home_season.get('ops', '.000'),
                    'runs': home_season.get('runs', 0),
                    'last5_ops': home_recent['last5'] or 'N/A',
                    'last10_ops': home_recent['last10'] or 'N/A'
                },
                'pitching': home_pitching
            }
        }
        
    def _get_team_season_stats(self, team_id: int) -> Dict:
        """チームのシーズン打撃成績"""
        stats = self.client._make_request(
            f"teams/{team_id}/stats?season=2024&stats=season&group=hitting"
        )
        
        if not stats or not stats.get('stats'):
            return {}
            
        try:
            return stats['stats'][0]['splits'][0]['stat']
        except:
            return {}
            
    def _get_team_pitching_stats(self, team_id: int) -> Dict:
        """チーム投手陣の成績"""
        stats = self.client._make_request(
            f"teams/{team_id}/stats?season=2024&stats=season&group=pitching"
        )
        
        if not stats or not stats.get('stats'):
            return {'era': 'N/A', 'whip': 'N/A'}
            
        try:
            stat_line = stats['stats'][0]['splits'][0]['stat']
            return {
                'era': stat_line.get('era', 'N/A'),
                'whip': stat_line.get('whip', 'N/A')
            }
        except:
            return {'era': 'N/A', 'whip': 'N/A'}
            

def main():
    """テスト実行"""
    collector = CompleteDataCollector()
    
    # 明日の試合を1つテスト
    japan_now = datetime.now()
    et_now = japan_now - timedelta(hours=13)
    mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
    
    schedule = collector.client._make_request(f"schedule?sportId=1&date={mlb_tomorrow}")
    
    if schedule and schedule.get('dates'):
        first_game = schedule['dates'][0]['games'][0]
        
        print("="*60)
        print("完全データ収集テスト")
        print("="*60)
        
        complete_data = collector.get_complete_matchup_data(first_game)
        
        # 結果表示
        print("\n【収集結果】")
        print(f"\n{complete_data['away']['team']} @ {complete_data['home']['team']}")
        print(f"\n先発投手:")
        print(f"  {complete_data['away']['starter']['name']} (ERA: {complete_data['away']['starter']['stats'].get('era', 'N/A')})")
        print(f"  vs")
        print(f"  {complete_data['home']['starter']['name']} (ERA: {complete_data['home']['starter']['stats'].get('era', 'N/A')})")
        print(f"\n過去のOPS:")
        print(f"  {complete_data['away']['team']}: Last5={complete_data['away']['batting']['last5_ops']}, Last10={complete_data['away']['batting']['last10_ops']}")
        print(f"  {complete_data['home']['team']}: Last5={complete_data['home']['batting']['last5_ops']}, Last10={complete_data['home']['batting']['last10_ops']}")
        

if __name__ == "__main__":
    main()