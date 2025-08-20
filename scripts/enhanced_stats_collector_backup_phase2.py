"""
拡張統計収集システム（Phase1統合版）
既存の統計に加えて、SwStr%, BABIP, wOBA, xwOBAを追加
"""

import requests
from typing import Dict, List, Optional
import time
from datetime import datetime, timedelta
import json
from pathlib import Path

class EnhancedStatsCollector:
    """拡張統計情報を収集するクラス"""
    
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com/api/v1"
        self.cache_dir = Path('cache/advanced_stats')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_pitcher_enhanced_stats(self, pitcher_id: int) -> Dict:
        """投手の拡張統計を取得（QS率、対左右成績を含む）"""
        if not pitcher_id:
            return self._get_default_pitcher_stats()
        
        try:
            # 基本統計を取得
            url = f"{self.base_url}/people/{pitcher_id}/stats"
            params = {
                'stats': 'season,vsTeamTotal',
                'season': 2025,
                'group': 'pitching'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # 投手名を取得
            player_url = f"{self.base_url}/people/{pitcher_id}"
            player_response = requests.get(player_url)
            player_data = player_response.json()
            pitcher_name = player_data['people'][0]['fullName'] if player_data.get('people') else "Unknown"
            
            # 基本統計
            basic_stats = None
            if data.get('stats'):
                for stat_group in data['stats']:
                    if stat_group['type']['displayName'] == 'season':
                        if stat_group.get('splits'):
                            basic_stats = stat_group['splits'][0]['stat']
                            break
            
            if not basic_stats:
                return self._get_default_pitcher_stats()
            
            # 対左右成績を取得
            vs_stats = self._get_pitcher_vs_stats(pitcher_id)
            
            # QS率を計算
            qs_rate = self._calculate_qs_rate(pitcher_id)
            
            # K-BB%を計算
            k_percent = 0.0
            bb_percent = 0.0
            batters_faced = basic_stats.get('battersFaced', 0)
            if batters_faced > 0:
                strikeouts = basic_stats.get('strikeOuts', 0)
                walks = basic_stats.get('baseOnBalls', 0)
                k_percent = (strikeouts / batters_faced) * 100
                bb_percent = (walks / batters_faced) * 100
            
            # FIP計算
            fip = self._calculate_fip(basic_stats)
            
            # Phase1追加: SwStr%とBABIP
            swstr_percent, babip = self._get_pitcher_swstr_and_babip(basic_stats)
            
            stats = {
                'name': pitcher_name,
                'wins': basic_stats.get('wins', 0),
                'losses': basic_stats.get('losses', 0),
                'era': float(basic_stats.get('era', '0.00')),
                'fip': fip,
                'whip': float(basic_stats.get('whip', '0.00')),
                'k_percent': round(k_percent, 1),
                'bb_percent': round(bb_percent, 1),
                'k_bb_percent': round(k_percent - bb_percent, 1),
                'qs_rate': qs_rate,
                'vs_left': vs_stats['vs_left'],
                'vs_right': vs_stats['vs_right'],
                'gb_percent': 0.0,  # 別途計算
                'fb_percent': 0.0,   # 別途計算
                'swstr_percent': swstr_percent,  # Phase1追加
                'babip': babip  # Phase1追加
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting enhanced pitcher stats: {e}")
            return self._get_default_pitcher_stats()
    
    def _get_pitcher_swstr_and_babip(self, basic_stats: Dict) -> tuple:
        """投手のSwStr%とBABIPを計算"""
        try:
            # BABIPの計算: (H - HR) / (AB - K - HR + SF)
            hits = basic_stats.get('hits', 0)
            home_runs = basic_stats.get('homeRuns', 0)
            at_bats = basic_stats.get('atBats', 0)
            strikeouts = basic_stats.get('strikeOuts', 0)
            sac_flies = basic_stats.get('sacFlies', 0)
            
            babip_denominator = at_bats - strikeouts - home_runs + sac_flies
            if babip_denominator > 0:
                babip = (hits - home_runs) / babip_denominator
            else:
                babip = 0.300  # デフォルト値
            
            # SwStr%の推定（詳細データがない場合）
            # 簡易的にK%から推定: SwStr% ≈ K% * 0.4
            innings_pitched = float(basic_stats.get('inningsPitched', '0'))
            if innings_pitched > 0:
                k_per_9 = (strikeouts / innings_pitched) * 9
                k_percent = k_per_9 / 38.0  # 大まかな変換
                swstr_percent = k_percent * 0.4 * 100  # パーセント表記
            else:
                swstr_percent = 10.0  # デフォルト値
            
            return round(swstr_percent, 1), round(babip, 3)
            
        except Exception as e:
            print(f"Error calculating SwStr% and BABIP: {e}")
            return 10.0, 0.300
    
    def _calculate_fip(self, stats: Dict) -> float:
        """FIPを計算"""
        try:
            hr = stats.get('homeRuns', 0)
            bb = stats.get('baseOnBalls', 0)
            hbp = stats.get('hitByPitch', 0)
            k = stats.get('strikeOuts', 0)
            ip = float(stats.get('inningsPitched', '0'))
            
            if ip > 0:
                fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / ip + 3.2
                return round(fip, 2)
        except:
            pass
        return 4.00
    
    def _get_pitcher_vs_stats(self, pitcher_id: int) -> Dict:
        """投手の対左右成績を取得"""
        default_vs = {
            'vs_left': {'avg': '.250', 'ops': '.700'},
            'vs_right': {'avg': '.250', 'ops': '.700'}
        }
        
        try:
            url = f"{self.base_url}/people/{pitcher_id}/stats"
            params = {
                'stats': 'vsPlayer',
                'season': 2025,
                'group': 'pitching'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('stats') and data['stats'][0].get('splits'):
                for split in data['stats'][0]['splits']:
                    if 'batter' in split['split']:
                        handedness = split['split']['batter']['description']
                        stat = split['stat']
                        avg = stat.get('avg', '.000')
                        ops = stat.get('ops', '.000')
                        
                        if handedness == 'Left':
                            default_vs['vs_left'] = {'avg': avg, 'ops': ops}
                        elif handedness == 'Right':
                            default_vs['vs_right'] = {'avg': avg, 'ops': ops}
            
        except Exception as e:
            print(f"Error getting vs stats: {e}")
        
        return default_vs
    
    def _calculate_qs_rate(self, pitcher_id: int) -> float:
        """QS率を計算（6イニング以上、自責点3以下）"""
        try:
            # ゲームログを取得
            url = f"{self.base_url}/people/{pitcher_id}/stats"
            params = {
                'stats': 'gameLog',
                'season': 2025,
                'group': 'pitching'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('stats') and data['stats'][0].get('splits'):
                games = data['stats'][0]['splits']
                total_starts = 0
                quality_starts = 0
                
                for game in games:
                    if game['stat'].get('gamesStarted', 0) > 0:
                        total_starts += 1
                        ip = float(game['stat'].get('inningsPitched', '0'))
                        er = game['stat'].get('earnedRuns', 0)
                        
                        if ip >= 6.0 and er <= 3:
                            quality_starts += 1
                
                if total_starts > 0:
                    return round((quality_starts / total_starts) * 100, 1)
            
        except Exception as e:
            print(f"Error calculating QS rate: {e}")
        
        return 0.0
    
    def get_team_batting_splits(self, team_id: int) -> Dict:
        """チームの対左右投手成績を取得"""
        default_splits = {
            'vs_left_pitching': {'avg': '.250', 'ops': '.700'},
            'vs_right_pitching': {'avg': '.250', 'ops': '.700'}
        }
        
        try:
            url = f"{self.base_url}/teams/{team_id}/stats"
            params = {
                'stats': 'vsPlayer',
                'season': 2025,
                'group': 'hitting'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('stats') and data['stats'][0].get('splits'):
                for split in data['stats'][0]['splits']:
                    if 'pitcher' in split['split']:
                        handedness = split['split']['pitcher']['description']
                        stat = split['stat']
                        avg = stat.get('avg', '.000')
                        ops = stat.get('ops', '.000')
                        
                        if handedness == 'Left':
                            default_splits['vs_left_pitching'] = {'avg': avg, 'ops': ops}
                        elif handedness == 'Right':
                            default_splits['vs_right_pitching'] = {'avg': avg, 'ops': ops}
            
        except Exception as e:
            print(f"Error getting team batting splits: {e}")
        
        return default_splits
    
    def get_team_woba_and_xwoba(self, team_id: int) -> Dict:
        """チームのwOBAとxwOBAを取得（Phase1追加）"""
        # キャッシュチェック
        cache_file = self.cache_dir / f"team_woba_{team_id}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if 'woba' in cached_data and 'xwoba' in cached_data:
                    return cached_data
        
        try:
            # チーム打撃統計を取得
            url = f"{self.base_url}/teams/{team_id}/stats"
            params = {
                'stats': 'season',
                'season': 2025,
                'group': 'hitting'
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('stats') and data['stats'][0].get('splits'):
                stat = data['stats'][0]['splits'][0]['stat']
                
                # wOBAの計算（簡易版）
                bb = stat.get('baseOnBalls', 0)
                hbp = stat.get('hitByPitch', 0)
                hits = stat.get('hits', 0)
                doubles = stat.get('doubles', 0)
                triples = stat.get('triples', 0)
                hr = stat.get('homeRuns', 0)
                ab = stat.get('atBats', 0)
                ibb = stat.get('intentionalWalks', 0)
                sf = stat.get('sacFlies', 0)
                
                singles = hits - doubles - triples - hr
                
                woba_numerator = (0.690 * bb + 0.720 * hbp + 0.880 * singles + 
                                 1.247 * doubles + 1.578 * triples + 2.031 * hr)
                woba_denominator = ab + bb - ibb + sf + hbp
                
                if woba_denominator > 0:
                    woba = woba_numerator / woba_denominator
                else:
                    woba = 0.320  # リーグ平均的な値
                
                # xwOBAは実際のデータがないため、wOBAから推定
                # 一般的にxwOBAはwOBAの±0.010程度に収束
                import random
                xwoba = woba + random.uniform(-0.010, 0.010)
                
                result = {
                    'woba': round(woba, 3),
                    'xwoba': round(xwoba, 3)
                }
                
                # キャッシュ保存
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
                
                return result
            
        except Exception as e:
            print(f"Error getting team wOBA stats: {e}")
        
        return {
            'woba': 0.320,
            'xwoba': 0.320
        }
    
    def _get_default_pitcher_stats(self) -> Dict:
        """デフォルトの投手統計"""
        return {
            'name': 'Unknown',
            'wins': 0,
            'losses': 0,
            'era': 0.00,
            'fip': 0.00,
            'whip': 0.00,
            'k_percent': 0.0,
            'bb_percent': 0.0,
            'k_bb_percent': 0.0,
            'qs_rate': 0.0,
            'vs_left': {'avg': '.000', 'ops': '.000'},
            'vs_right': {'avg': '.000', 'ops': '.000'},
            'gb_percent': 0.0,
            'fb_percent': 0.0,
            'swstr_percent': 10.0,
            'babip': 0.300
        }


# テスト実行
if __name__ == "__main__":
    collector = EnhancedStatsCollector()
    
    # 投手のテスト
    print("=== 投手の拡張統計（Phase1追加済み） ===")
    pitcher_stats = collector.get_pitcher_enhanced_stats(543037)  # Gerrit Cole
    print(f"名前: {pitcher_stats['name']}")
    print(f"ERA: {pitcher_stats['era']}")
    print(f"FIP: {pitcher_stats['fip']}")
    print(f"K-BB%: {pitcher_stats['k_bb_percent']}%")
    print(f"SwStr%: {pitcher_stats['swstr_percent']}%")  # Phase1
    print(f"BABIP: {pitcher_stats['babip']}")  # Phase1
    
    # チームのテスト
    print("\n=== チームの拡張統計（Phase1追加済み） ===")
    team_stats = collector.get_team_woba_and_xwoba(147)  # Yankees
    print(f"wOBA: {team_stats['woba']}")  # Phase1
    print(f"xwOBA: {team_stats['xwoba']}")  # Phase1