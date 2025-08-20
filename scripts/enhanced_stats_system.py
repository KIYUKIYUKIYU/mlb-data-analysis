"""
MLB統計データ拡充システム
時差計算修正 + 追加スタッツ実装
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.mlb_api_client import MLBApiClient
import time


class EnhancedStatsSystem:
    def __init__(self):
        self.client = MLBApiClient()
        
    def get_japan_tomorrow_games(self):
        """日本時間基準の明日の試合を取得"""
        japan_now = datetime.now()
        print(f"現在の日本時間: {japan_now.strftime('%Y-%m-%d %H:%M')}")
        
        # 日本時間の明日の試合を判定
        # MLB試合は通常、日本時間の早朝〜昼に行われる
        # 日本の夜19時なら、今日の深夜〜明日の試合を取得すべき
        
        # アメリカ東部時間
        et_now = japan_now - timedelta(hours=13)
        
        # 日本時間で「明日の試合」とは：
        # - 今が夜（18時以降）なら → 今夜〜明日の試合（MLB的には今日〜明日朝）
        # - 今が昼間なら → 今日の夜〜明日の試合
        
        if japan_now.hour >= 18:  # 日本の夜
            # 今夜から明日の試合 = MLBの今日の試合
            mlb_date = et_now.strftime('%Y-%m-%d')
        else:
            # 明日の試合 = MLBの今日〜明日
            mlb_date = et_now.strftime('%Y-%m-%d')
            
        print(f"取得するMLB日付: {mlb_date}")
        
        # hydrate=probablePitcherで取得
        schedule = self.client._make_request(
            f"schedule?sportId=1&date={mlb_date}&hydrate=probablePitcher,team"
        )
        
        if not schedule.get('dates'):
            return []
            
        games = schedule['dates'][0].get('games', [])
        
        # 日本時間でフィルタリング（明日の試合のみ）
        japan_tomorrow_start = japan_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        japan_tomorrow_end = japan_tomorrow_start + timedelta(days=1)
        
        filtered_games = []
        for game in games:
            # タイムゾーン情報を削除して比較
            game_time_str = game['gameDate'].replace('Z', '')
            game_time = datetime.fromisoformat(game_time_str)
            game_time_jp = game_time + timedelta(hours=9)
            
            if japan_tomorrow_start <= game_time_jp < japan_tomorrow_end:
                filtered_games.append(game)
                
        print(f"日本時間の明日の試合数: {len(filtered_games)}")
        return filtered_games
        
    def calculate_advanced_pitcher_stats(self, pitcher_id: int) -> Dict:
        """投手の拡張統計を計算"""
        # 基本統計
        season_stats = self.client._make_request(
            f"people/{pitcher_id}/stats?stats=season&season=2024&group=pitching"
        )
        
        if not season_stats or not season_stats.get('stats'):
            return {}
            
        stat_line = season_stats['stats'][0]['splits'][0]['stat']
        
        # 基本データ
        innings = float(stat_line.get('inningsPitched', 0))
        batters_faced = stat_line.get('battersFaced', 0)
        strikeouts = stat_line.get('strikeOuts', 0)
        walks = stat_line.get('baseOnBalls', 0)
        hits = stat_line.get('hits', 0)
        home_runs = stat_line.get('homeRuns', 0)
        ground_outs = stat_line.get('groundOuts', 0)
        air_outs = stat_line.get('airOuts', 0)
        
        # 計算
        total_outs = ground_outs + air_outs
        
        advanced_stats = {
            'k_rate': round((strikeouts / batters_faced * 100), 1) if batters_faced > 0 else 0,
            'bb_rate': round((walks / batters_faced * 100), 1) if batters_faced > 0 else 0,
            'k_bb_rate': round((strikeouts / walks), 2) if walks > 0 else 0,
            'ground_ball_rate': round((ground_outs / total_outs * 100), 1) if total_outs > 0 else 0,
            'fly_ball_rate': round((air_outs / total_outs * 100), 1) if total_outs > 0 else 0,
            'hr_per_9': round((home_runs * 9 / innings), 2) if innings > 0 else 0,
            'whip': stat_line.get('whip', '0.00'),
            'era': stat_line.get('era', '0.00'),
            'fip': self._calculate_fip(stat_line)
        }
        
        # 左右別被打率
        splits = self.client._make_request(
            f"people/{pitcher_id}/stats?stats=statSplits&season=2024&group=pitching"
        )
        
        if splits and splits.get('stats'):
            for split_group in splits['stats']:
                for split in split_group.get('splits', []):
                    if split.get('split', {}).get('code') == 'vl':
                        advanced_stats['vs_left_avg'] = split.get('stat', {}).get('avg', '.000')
                    elif split.get('split', {}).get('code') == 'vr':
                        advanced_stats['vs_right_avg'] = split.get('stat', {}).get('avg', '.000')
                        
        # QS率計算
        game_log = self.client._make_request(
            f"people/{pitcher_id}/stats?stats=gameLog&season=2024&group=pitching"
        )
        
        if game_log and game_log.get('stats'):
            advanced_stats['qs_rate'] = self._calculate_qs_rate(game_log['stats'][0].get('splits', []))
            
        return advanced_stats
        
    def _calculate_fip(self, stats: Dict) -> float:
        """FIP計算"""
        try:
            hr = stats.get('homeRuns', 0)
            bb = stats.get('baseOnBalls', 0)
            hbp = stats.get('hitByPitch', 0)
            k = stats.get('strikeOuts', 0)
            ip = float(stats.get('inningsPitched', 1))
            
            fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / ip + 3.2
            return round(fip, 2)
        except:
            return 0.0
            
    def _calculate_qs_rate(self, game_logs: List[Dict]) -> float:
        """QS率計算"""
        starts = 0
        quality_starts = 0
        
        for game in game_logs:
            stat = game.get('stat', {})
            if game.get('isStarter', False):
                starts += 1
                innings = float(stat.get('inningsPitched', 0))
                earned_runs = stat.get('earnedRuns', 0)
                
                if innings >= 6.0 and earned_runs <= 3:
                    quality_starts += 1
                    
        return round((quality_starts / starts * 100), 1) if starts > 0 else 0.0
        
    def calculate_batter_vs_pitcher_stats(self, batter_id: int, pitcher_hand: str) -> Dict:
        """打者の対左右投手成績"""
        splits = self.client._make_request(
            f"people/{batter_id}/stats?stats=statSplits&season=2024&group=hitting"
        )
        
        if not splits or not splits.get('stats'):
            return {}
            
        result = {}
        target_code = 'vl' if pitcher_hand == 'L' else 'vr'
        
        for split_group in splits['stats']:
            for split in split_group.get('splits', []):
                if split.get('split', {}).get('code') == target_code:
                    stat = split.get('stat', {})
                    result = {
                        'avg': stat.get('avg', '.000'),
                        'ops': stat.get('ops', '.000'),
                        'at_bats': stat.get('atBats', 0),
                        'hits': stat.get('hits', 0),
                        'home_runs': stat.get('homeRuns', 0)
                    }
                    break
                    
        return result
        
    def get_complete_game_analysis(self, game_data: Dict) -> Dict:
        """完全な試合分析データ"""
        away_team = game_data['teams']['away']['team']
        home_team = game_data['teams']['home']['team']
        
        print(f"\n詳細分析中: {away_team['name']} @ {home_team['name']}")
        
        # 先発投手
        away_pitcher = game_data['teams']['away'].get('probablePitcher', {})
        home_pitcher = game_data['teams']['home'].get('probablePitcher', {})
        
        # 投手の詳細統計
        away_pitcher_stats = {}
        home_pitcher_stats = {}
        
        if away_pitcher.get('id'):
            print("  Away投手の詳細統計取得中...")
            away_pitcher_stats = self.calculate_advanced_pitcher_stats(away_pitcher['id'])
            
        if home_pitcher.get('id'):
            print("  Home投手の詳細統計取得中...")
            home_pitcher_stats = self.calculate_advanced_pitcher_stats(home_pitcher['id'])
            
        # 時間変換
        game_time_str = game_data['gameDate'].replace('Z', '')
        game_time = datetime.fromisoformat(game_time_str)
        game_time_jp = game_time + timedelta(hours=9)
        
        return {
            'game_id': game_data['gamePk'],
            'game_date': game_data['gameDate'],
            'game_time_jp': game_time_jp.strftime('%m/%d %H:%M'),
            'away': {
                'team': away_team['name'],
                'team_id': away_team['id'],
                'pitcher': {
                    'name': away_pitcher.get('fullName', '未定'),
                    'id': away_pitcher.get('id'),
                    'hand': away_pitcher.get('pitchHand', {}).get('code', 'R'),
                    'stats': away_pitcher_stats
                }
            },
            'home': {
                'team': home_team['name'],
                'team_id': home_team['id'],
                'pitcher': {
                    'name': home_pitcher.get('fullName', '未定'),
                    'id': home_pitcher.get('id'),
                    'hand': home_pitcher.get('pitchHand', {}).get('code', 'R'),
                    'stats': home_pitcher_stats
                }
            }
        }
        

def main():
    """テスト実行"""
    system = EnhancedStatsSystem()
    
    print("="*60)
    print("拡張統計システムテスト")
    print("="*60)
    
    # 日本時間の明日の試合を取得
    games = system.get_japan_tomorrow_games()
    
    if games:
        # 最初の試合で詳細分析
        first_game = games[0]
        analysis = system.get_complete_game_analysis(first_game)
        
        print("\n【分析結果】")
        print(f"{analysis['away']['team']} @ {analysis['home']['team']}")
        print(f"日本時間: {analysis['game_time_jp']}")
        
        # Away投手
        away_p = analysis['away']['pitcher']
        if away_p['stats']:
            print(f"\n{away_p['name']} ({away_p['hand']})")
            print(f"  ERA: {away_p['stats']['era']} / FIP: {away_p['stats']['fip']}")
            print(f"  K%: {away_p['stats']['k_rate']}% / BB%: {away_p['stats']['bb_rate']}%")
            print(f"  GB%: {away_p['stats']['ground_ball_rate']}% / FB%: {away_p['stats']['fly_ball_rate']}%")
            print(f"  QS率: {away_p['stats'].get('qs_rate', 0)}%")
            print(f"  対左: {away_p['stats'].get('vs_left_avg', 'N/A')} / 対右: {away_p['stats'].get('vs_right_avg', 'N/A')}")
            
        # Home投手
        home_p = analysis['home']['pitcher']
        if home_p['stats']:
            print(f"\n{home_p['name']} ({home_p['hand']})")
            print(f"  ERA: {home_p['stats']['era']} / FIP: {home_p['stats']['fip']}")
            print(f"  K%: {home_p['stats']['k_rate']}% / BB%: {home_p['stats']['bb_rate']}%")
            print(f"  GB%: {home_p['stats']['ground_ball_rate']}% / FB%: {home_p['stats']['fly_ball_rate']}%")
            print(f"  QS率: {home_p['stats'].get('qs_rate', 0)}%")
            print(f"  対左: {home_p['stats'].get('vs_left_avg', 'N/A')} / 対右: {home_p['stats'].get('vs_right_avg', 'N/A')}")
    

if __name__ == "__main__":
    main()