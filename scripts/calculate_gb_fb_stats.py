import requests
import time
from typing import Dict, Tuple
from datetime import datetime, timedelta

class GBFBCalculator:
    """Play-by-playデータからGB%とFB%を計算"""
    
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com/api/v1"
        self.session = requests.Session()
    
    def calculate_pitcher_gb_fb(self, pitcher_id: int, limit_games: int = 5) -> Tuple[float, float]:
        """投手の最近の試合からGB%とFB%を計算"""
        try:
            # 投手の最近の試合を取得
            recent_games = self._get_pitcher_recent_games(pitcher_id, limit_games)
            
            if not recent_games:
                return 0.0, 0.0
            
            total_ground_balls = 0
            total_fly_balls = 0
            total_balls_in_play = 0
            
            # 各試合のplay-by-playを分析
            for game_pk in recent_games[:limit_games]:
                gb, fb, bip = self._analyze_game_for_pitcher(game_pk, pitcher_id)
                total_ground_balls += gb
                total_fly_balls += fb
                total_balls_in_play += bip
                
                time.sleep(0.5)  # API制限対策
            
            if total_balls_in_play == 0:
                return 0.0, 0.0
            
            gb_percent = (total_ground_balls / total_balls_in_play) * 100
            fb_percent = (total_fly_balls / total_balls_in_play) * 100
            
            return round(gb_percent, 1), round(fb_percent, 1)
            
        except Exception as e:
            print(f"Error calculating GB/FB for pitcher {pitcher_id}: {e}")
            return 0.0, 0.0
    
    def _get_pitcher_recent_games(self, pitcher_id: int, limit: int) -> list:
        """投手の最近の登板試合を取得"""
        try:
            # 2025年シーズンの投手成績を取得
            url = f"{self.base_url}/people/{pitcher_id}/stats"
            params = {
                'stats': 'gameLog',
                'season': 2025,
                'group': 'pitching'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            game_pks = []
            if 'stats' in data and data['stats']:
                for stat_group in data['stats']:
                    if 'splits' in stat_group:
                        for split in stat_group['splits'][:limit]:
                            if 'game' in split:
                                game_pks.append(split['game']['gamePk'])
            
            return game_pks
            
        except Exception as e:
            print(f"Error getting pitcher games: {e}")
            return []
    
    def _analyze_game_for_pitcher(self, game_pk: int, pitcher_id: int) -> Tuple[int, int, int]:
        """特定の試合で投手の打球タイプを分析"""
        try:
            url = f"{self.base_url}/game/{game_pk}/playByPlay"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            ground_balls = 0
            fly_balls = 0
            balls_in_play = 0
            
            for play in data.get('allPlays', []):
                # 投手が対象の投手かチェック
                if play.get('matchup', {}).get('pitcher', {}).get('id') == pitcher_id:
                    # 打球結果を分析
                    for event in play.get('playEvents', []):
                        if event.get('isPitch'):
                            details = event.get('details', {})
                            hit_data = event.get('hitData', {})
                            
                            # 打球タイプを判定
                            if hit_data:
                                launch_angle = hit_data.get('launchAngle', None)
                                if launch_angle is not None:
                                    balls_in_play += 1
                                    if launch_angle < 10:  # ゴロ
                                        ground_balls += 1
                                    elif launch_angle > 25:  # フライ
                                        fly_balls += 1
                            elif details.get('description'):
                                desc = details['description'].lower()
                                if any(word in desc for word in ['ground', 'grounder']):
                                    ground_balls += 1
                                    balls_in_play += 1
                                elif any(word in desc for word in ['fly', 'pop', 'line']):
                                    fly_balls += 1
                                    balls_in_play += 1
            
            return ground_balls, fly_balls, balls_in_play
            
        except Exception as e:
            print(f"Error analyzing game {game_pk}: {e}")
            return 0, 0, 0
    
    def get_estimated_gb_fb(self, pitcher_name: str) -> Tuple[float, float]:
        """投手名から推定GB%/FB%を返す（簡易版）"""
        # 実際のデータがない場合の推定値
        # 一般的な投手の平均値を使用
        DEFAULT_GB = 44.0
        DEFAULT_FB = 35.0
        
        # 特定の投手タイプの推定値
        gb_pitchers = ['mize', 'webb', 'framber']
        fb_pitchers = ['glasnow', 'cole', 'verlander']
        
        name_lower = pitcher_name.lower()
        
        for gb_pitcher in gb_pitchers:
            if gb_pitcher in name_lower:
                return 52.0, 28.0
        
        for fb_pitcher in fb_pitchers:
            if fb_pitcher in name_lower:
                return 38.0, 42.0
        
        return DEFAULT_GB, DEFAULT_FB


# テスト実行
if __name__ == "__main__":
    calculator = GBFBCalculator()
    
    # Dean Kremerでテスト
    print("Calculating GB%/FB% for Dean Kremer (ID: 665152)...")
    gb, fb = calculator.calculate_pitcher_gb_fb(665152, limit_games=3)
    print(f"GB%: {gb}%, FB%: {fb}%")
    
    # 推定値のテスト
    print("\n推定値テスト:")
    est_gb, est_fb = calculator.get_estimated_gb_fb("Dean Kremer")
    print(f"Dean Kremer - 推定 GB%: {est_gb}%, FB%: {est_fb}%")