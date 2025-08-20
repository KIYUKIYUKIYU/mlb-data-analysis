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
        """投手の高度な統計を取得"""
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
            
            # statsデータの安全な取得（新しい構造に対応）
            stats = {}
            if isinstance(season_stats, dict) and 'stats' in season_stats:
                stats_list = season_stats.get('stats', [])
                if stats_list and len(stats_list) > 0:
                    first_stat = stats_list[0]
                    # 新しい構造: splits配列の中にデータがある
                    if isinstance(first_stat, dict) and 'splits' in first_stat:
                        splits = first_stat.get('splits', [])
                        if splits and len(splits) > 0:
                            stats = splits[0].get('stat', {})
                    # 古い構造との互換性
                    elif isinstance(first_stat, dict) and 'stats' in first_stat:
                        stats = first_stat.get('stats', {})
            
            # 基本統計（文字列を数値に変換）
            innings_pitched_str = stats.get('inningsPitched', '0.0') or '0.0'
            # イニング数の変換（例: "91.2" -> 91.667）
            if '.' in str(innings_pitched_str):
                parts = str(innings_pitched_str).split('.')
                innings = float(parts[0])
                outs = float(parts[1]) if len(parts) > 1 else 0
                innings_pitched = innings + (outs / 3.0)
            else:
                innings_pitched = float(innings_pitched_str)
            
            # ===== 修正部分: 対左右成績の取得 =====
            # 改善版のget_player_splitsを使用（内部でget_player_splits_enhancedを呼ぶ）
            splits_data = self.client.get_player_splits(pitcher_id, 2025)
            
            # デフォルト値
            vs_left = {'avg': '.250', 'ops': '.700'}
            vs_right = {'avg': '.250', 'ops': '.700'}
            splits_note = ''
            
            # 新しいデータ構造に対応
            if splits_data:
                # vsL/vsRキーで直接アクセス
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
                
                # データソースの注記を取得
                if 'note' in splits_data:
                    splits_note = splits_data['note']
                elif 'data_source' in splits_data:
                    splits_note = splits_data['data_source']
            
            # FIP計算
            hr = int(stats.get('homeRuns', 0) or 0)
            bb = int(stats.get('baseOnBalls', 0) or 0)
            hbp = int(stats.get('hitByPitch', 0) or 0)
            k = int(stats.get('strikeOuts', 0) or 0)
            
            if innings_pitched > 0:
                fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / innings_pitched + 3.20
            else:
                fip = 0.00
            
            # xFIP計算（仮定：FB%を使用）
            batters_faced = int(stats.get('battersFaced', 0) or 0)
            fb_percent = 0.50  # デフォルト値
            if batters_faced > 0:
                # 実際のFB%データがない場合は推定
                gb_percent = float(stats.get('groundBallPercentage', 0.45) or 0.45)
                fb_percent = 1.0 - gb_percent
            
            # リーグ平均HR/FB率（仮定値）
            league_hr_fb = 0.135
            expected_hr = fb_percent * batters_faced * league_hr_fb
            
            if innings_pitched > 0:
                xfip = ((13 * expected_hr) + (3 * (bb + hbp)) - (2 * k)) / innings_pitched + 3.20
            else:
                xfip = 0.00
            
            # K-BB%計算
            if batters_faced > 0:
                k_rate = k / batters_faced
                bb_rate = bb / batters_faced
                k_bb_percent = (k_rate - bb_rate) * 100
            else:
                k_bb_percent = 0.0
            
            # GB%とFB%
            gb_percent = float(stats.get('groundBallPercentage', 0.45) or 0.45) * 100
            fb_percent = (1.0 - float(stats.get('groundBallPercentage', 0.45) or 0.45)) * 100
            
            # QS率計算（改善版）
            games_started = int(stats.get('gamesStarted', 0) or 0)
            quality_starts = 0
            
            if games_started > 0:
                # 平均イニング数とERAから推定
                avg_innings_per_start = innings_pitched / games_started if games_started > 0 else 0
                era_str = stats.get('era', '0.00') or '0.00'
                try:
                    era = float(era_str)
                except:
                    era = 0.00
                
                # 6イニング以上投げて3自責点以下の確率を推定
                if avg_innings_per_start >= 6.0 and era <= 4.50:
                    # ERAベースでQS率を推定
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
            else:
                qs_rate = 0.0
            
            qs_rate = (quality_starts / games_started * 100) if games_started > 0 else 0.0
            
            # SwStr%（現在は固定値）
            swstr_percent = 10.0
            
            result = {
                'name': f"{player_info.get('firstName', '')} {player_info.get('lastName', '')}",
                'wins': stats.get('wins', 0) or 0,
                'losses': stats.get('losses', 0) or 0,
                'era': str(stats.get('era', '0.00') or '0.00'),
                'fip': f"{fip:.2f}",
                'xfip': f"{xfip:.2f}",
                'whip': str(stats.get('whip', '0.00') or '0.00'),
                'k_bb_percent': f"{k_bb_percent:.1f}%",
                'gb_percent': f"{gb_percent:.1f}%",
                'fb_percent': f"{fb_percent:.1f}%",
                'qs_rate': f"{qs_rate:.1f}%",
                'swstr_percent': f"{swstr_percent:.1f}%",
                'babip': str(stats.get('babip', '.300') or '.300'),
                'vs_left': vs_left,
                'vs_right': vs_right,
                'splits_note': splits_note  # データソースの注記を追加
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
            'xfip': '0.00',
            'whip': '0.00',
            'k_bb_percent': '0.0%',
            'gb_percent': '45.0%',  # デフォルト値を現実的に
            'fb_percent': '55.0%',  # デフォルト値を現実的に
            'qs_rate': '0.0%',
            'swstr_percent': '10.0%',  # デフォルト値
            'babip': '.300',
            'vs_left': {'avg': '.250', 'ops': '.700'},
            'vs_right': {'avg': '.250', 'ops': '.700'},
            'splits_note': 'デフォルト値'
        }