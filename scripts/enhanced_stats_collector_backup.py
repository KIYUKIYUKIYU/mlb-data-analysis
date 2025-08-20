 
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
        """投手の高度な統計を取得（MLB API seasonAdvanced対応版）"""
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
            # get_player_stats_by_seasonは直接統計データを返す
            if isinstance(season_stats, dict) and len(season_stats) > 0:
                stats = season_stats
            else:
                stats = {}

            # 基本統計
            innings_pitched_str = stats.get('inningsPitched', '0.0') or '0.0'
            if '.' in str(innings_pitched_str):
                parts = str(innings_pitched_str).split('.')
                innings = float(parts[0])
                outs = float(parts[1]) if len(parts) > 1 else 0
                innings_pitched = innings + (outs / 3.0)
            else:
                innings_pitched = float(innings_pitched_str)

            # ===== MLB API seasonAdvanced から GB%/FB%/SwStr%/BABIP を取得 =====
            advanced_stats = self._get_advanced_stats(pitcher_id, 2025)

            # 対左右成績（既に正常に動作）
            splits_data = self.client.get_player_splits(pitcher_id, 2025)
            vs_left = {'avg': '.250', 'ops': '.700'}
            vs_right = {'avg': '.250', 'ops': '.700'}
            splits_note = ''

            if splits_data:
                if 'vs_left' in splits_data and splits_data['vs_left']:
                    vs_left = {
                        'avg': splits_data['vs_left'].get('avg', '.250'),
                        'ops': splits_data['vs_left'].get('ops', '.700')
                    }
                if 'vs_right' in splits_data and splits_data['vs_right']:
                    vs_right = {
                        'avg': splits_data['vs_right'].get('avg', '.250'),
                        'ops': splits_data['vs_right'].get('ops', '.700')
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

            # xFIPをMLB APIから直接取得
            xfip = None
            try:
                url = f"{self.client.base_url}/api/v1/people/{pitcher_id}/stats"
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

            if xfip is not None:
                xfip_value = float(xfip)
            else:
                # xFIPがない場合はFIPを使用
                xfip_value = fip

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

            result = {
                'name': player_info.get('fullName', 'Unknown'),
                'wins': stats.get('wins', 0) or 0,
                'losses': stats.get('losses', 0) or 0,
                'era': str(stats.get('era', '0.00') or '0.00'),
                'fip': str(fip),
                'xfip': str(xfip_value),
                'whip': str(stats.get('whip', '0.00') or '0.00'),
                'k_bb_percent': str(k_bb_percent),
                'qs_rate': str(qs_rate),
                'gb_percent': advanced_stats.get('gb_percent', '0.0'),
                'fb_percent': advanced_stats.get('fb_percent', '0.0'),
                'swstr_percent': advanced_stats.get('swstr_percent', '0.0'),
                'babip': advanced_stats.get('babip', '.000'),
                'vs_left': vs_left,
                'vs_right': vs_right,
                'splits_note': splits_note
            }

            # キャッシュに保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=True)

            return result

        except Exception as e:
            print(f"Error getting enhanced stats for pitcher {pitcher_id}: {e}")
            return self._get_default_stats()

    def _get_advanced_stats(self, pitcher_id, season):
        """MLB API seasonAdvancedから詳細統計を取得"""
        try:
            url = f"{self.client.base_url}/api/v1/people/{pitcher_id}/stats"
            params = {
                'stats': 'seasonAdvanced',
                'season': season,
                'group': 'pitching'
            }

            response = self.client.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()

                if data.get('stats') and data['stats']:
                    for stat_group in data['stats']:
                        if stat_group.get('splits'):
                            advanced = stat_group['splits'][0].get('stat', {})

                            # 打球データ
                            balls_in_play = int(advanced.get('ballsInPlay', 0))

                            if balls_in_play > 0:
                                # GB%, FB%, LD%を計算
                                ground_outs = int(advanced.get('groundOuts', 0))
                                ground_hits = int(advanced.get('groundHits', 0))
                                fly_outs = int(advanced.get('flyOuts', 0))
                                fly_hits = int(advanced.get('flyHits', 0))
                                line_outs = int(advanced.get('lineOuts', 0))
                                line_hits = int(advanced.get('lineHits', 0))

                                gb_total = ground_outs + ground_hits
                                fb_total = fly_outs + fly_hits
                                ld_total = line_outs + line_hits

                                gb_percent = round((gb_total / balls_in_play) * 100, 1)
                                fb_percent = round((fb_total / balls_in_play) * 100, 1)
                                ld_percent = round((ld_total / balls_in_play) * 100, 1)

                                # SwStr%を計算
                                total_swings = int(advanced.get('totalSwings', 0))
                                swing_and_misses = int(advanced.get('swingAndMisses', 0))

                                if total_swings > 0:
                                    swstr_percent = round((swing_and_misses / total_swings) * 100, 1)
                                else:
                                    swstr_percent = 0.0

                                # BABIP
                                babip = advanced.get('babip', '.000')

                                return {
                                    'gb_percent': str(gb_percent),
                                    'fb_percent': str(fb_percent),
                                    'ld_percent': str(ld_percent),
                                    'swstr_percent': str(swstr_percent),
                                    'babip': babip
                                }

        except Exception as e:
            print(f"Advanced stats取得エラー: {e}")

        return {
            'gb_percent': '0.0',
            'fb_percent': '0.0',
            'swstr_percent': '0.0',
            'babip': '.000'
        }

    def _get_default_stats(self):
        """デフォルトの統計値を返す"""
        return {
            'name': 'Unknown',
            'wins': 0,
            'losses': 0,
            'era': '0.00',
            'fip': '0.00',
            'xfip': '0.00',
            'whip': '0.00',
            'k_bb_percent': '0.0',
            'qs_rate': '0.0',
            'gb_percent': '0.0',
            'fb_percent': '0.0',
            'swstr_percent': '0.0',
            'babip': '.000',
            'vs_left': {'avg': '.250', 'ops': '.700'},
            'vs_right': {'avg': '.250', 'ops': '.700'},
            'splits_note': 'デフォルト値'
        }