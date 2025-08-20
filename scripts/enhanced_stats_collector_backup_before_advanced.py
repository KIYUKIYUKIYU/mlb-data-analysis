import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mlb_api_client import MLBApiClient
import json
from datetime import datetime
import math

class EnhancedStatsCollector:
    def __init__(self):
        self.client = MLBApiClient()
        self.cache_dir = "cache/advanced_stats"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_pitcher_enhanced_stats(self, pitcher_id):
        """投手の高度な統計を取得（xFIPをAPIから取得版）"""
        cache_file = f"{self.cache_dir}/pitcher_{pitcher_id}_2025.json"
        
        # キャッシュチェック
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        try:
            # 基本情報取得
            player_info = self.client.get_player_info(pitcher_id)
            
            # 2025年シーズンの統計を取得
            season_stats = self.client.get_player_stats_by_season(pitcher_id, 2025)
            
            if not season_stats:
                print(f"No 2025 stats found for pitcher {pitcher_id}")
                return self._get_default_stats()
            
            # statsデータの安全な取得
            stats = {}
            if isinstance(season_stats, dict) and 'stats' in season_stats:
                stats_list = season_stats.get('stats', [])
                if stats_list and len(stats_list) > 0:
                    first_stat = stats_list[0]
                    if isinstance(first_stat, dict) and 'splits' in first_stat:
                        splits = first_stat.get('splits', [])
                        if splits and len(splits) > 0:
                            stats = splits[0].get('stat', {})
            
            # 基本統計
            innings_pitched_str = stats.get('inningsPitched', '0.0') or '0.0'
            if '.' in str(innings_pitched_str):
                parts = str(innings_pitched_str).split('.')
                innings = float(parts[0])
                outs = float(parts[1]) if len(parts) > 1 else 0
                innings_pitched = innings + (outs / 3.0)
            else:
                innings_pitched = float(innings_pitched_str)
            
            # 対左右成績（既に正常動作）
            splits_data = self.client.get_player_splits(pitcher_id, 2025)
            vs_left = {'avg': '.250', 'ops': '.700'}
            vs_right = {'avg': '.250', 'ops': '.700'}
            splits_note = ''
            
            if splits_data:
                if 'vsL' in splits_data and splits_data['vsL']:
                    vs_left = {
                        'avg': splits_data['vsL'].get('avg', '.250'),
                        'ops': splits_data['vsL'].get('ops', '.700')
                    }
                if 'vsR' in splits_data and splits_data['vsR']:
                    vs_right = {
                        'avg': splits_data['vsR'].get('avg', '.250'),
                        'ops': splits_data['vsR'].get('ops', '.700')
                    }
                if 'note' in splits_data:
                    splits_note = splits_data['note']
            
            # FIP計算（既存のまま）
            hr = int(stats.get('homeRuns', 0) or 0)
            bb = int(stats.get('baseOnBalls', 0) or 0)
            hbp = int(stats.get('hitByPitch', 0) or 0)
            k = int(stats.get('strikeOuts', 0) or 0)
            
            if innings_pitched > 0:
                fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / innings_pitched + 3.10
            else:
                fip = 0.00
            
            # ===== xFIPをMLB APIから直接取得 =====
            xfip = None
            try:
                # Sabermetrics統計を取得
                url = f"{self.client.base_url}/people/{pitcher_id}/stats"
                params = {
                    'stats': 'sabermetrics',
                    'season': 2025,
                    'group': 'pitching'
                }
                
                response = self.client.session.get(url, params=params)
                if response.status_code == 200:
                    saber_data = response.json()
                    if saber_data.get('stats') and saber_data['stats']:
                        for stat_group in saber_data['stats']:
                            if stat_group.get('splits'):
                                saber_stats = stat_group['splits'][0].get('stat', {})
                                xfip = saber_stats.get('xfip')
                                break
            except Exception as e:
                print(f"xFIP取得エラー: {e}")
            
            # xFIPが取得できなかった場合は非表示
            if xfip is not None:
                xfip_str = f"{float(xfip):.2f}"
            else:
                xfip_str = None
            
            # K-BB%計算
            batters_faced = int(stats.get('battersFaced', 0) or 0)
            if batters_faced > 0:
                k_rate = k / batters_faced
                bb_rate = bb / batters_faced
                k_bb_percent = (k_rate - bb_rate) * 100
            else:
                k_bb_percent = 0.0
            
            # QS率計算
            games_started = int(stats.get('gamesStarted', 0) or 0)
            if games_started > 0:
                avg_innings_per_start = innings_pitched / games_started
                era_str = stats.get('era', '0.00') or '0.00'
                try:
                    era = float(era_str)
                except:
                    era = 0.00
                
                if avg_innings_per_start >= 6.0 and era <= 4.50:
                    if era <= 3.00:
                        qs_rate = 0.75
                    elif era <= 3.50:
                        qs_rate = 0.60
                    elif era <= 4.00:
                        qs_rate = 0.45
                    else:
                        qs_rate = 0.30
                else:
                    qs_rate = max(0.15, min(0.30, avg_innings_per_start / 20.0))
                
                quality_starts = int(games_started * qs_rate)
                qs_rate = (quality_starts / games_started * 100)
            else:
                qs_rate = 0.0
            
            # GB%, FB%, SwStr%, BABIPは現時点では取得できないので表示しない
            # 将来的に手動データや他のAPIから取得する場合に備えて構造は残す
            
            result = {
                'name': f"{player_info.get('people', [{}])[0].get('firstName', '')} {player_info.get('people', [{}])[0].get('lastName', '')}",
                'wins': stats.get('wins', 0) or 0,
                'losses': stats.get('losses', 0) or 0,
                'era': str(stats.get('era', '0.00') or '0.00'),
                'fip': f"{fip:.2f}",
                'xfip': xfip_str,  # APIから取得した値
                'whip': str(stats.get('whip', '0.00') or '0.00'),
                'k_bb_percent': f"{k_bb_percent:.1f}%",
                'qs_rate': f"{qs_rate:.1f}%",
                'vs_left': vs_left,
                'vs_right': vs_right,
                'splits_note': splits_note,
                # MLB APIで取得できない項目は今は含めない
                'gb_percent': None,
                'fb_percent': None,
                'swstr_percent': None,
                'babip': stats.get('babip') if stats.get('babip') else None
            }
            
            # キャッシュに保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=True)
            
            return result
            
        except Exception as e:
            print(f"Error getting enhanced stats for pitcher {pitcher_id}: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self):
        """デフォルトの統計値を返す"""
        return {
            'name': 'Unknown',
            'wins': 0,
            'losses': 0,
            'era': '0.00',
            'fip': '0.00',
            'xfip': None,
            'whip': '0.00',
            'k_bb_percent': '0.0%',
            'qs_rate': '0.0%',
            'vs_left': {'avg': '.250', 'ops': '.700'},
            'vs_right': {'avg': '.250', 'ops': '.700'},
            'splits_note': 'デフォルト値',
            'gb_percent': None,
            'fb_percent': None,
            'swstr_percent': None,
            'babip': None
        }