 
"""
チーム打撃品質統計モジュール
wOBA計算とBarrel%/Hard-Hit%の取得（Baseball Savant統合版）
"""

import os
import json
import logging
from datetime import datetime, timedelta
import sys

# savant_statcast_fetcherをインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.savant_statcast_fetcher import SavantStatcastFetcher

class BattingQualityStats:
    """チーム打撃品質統計クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_dir = "cache/batting_quality"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Savantデータフェッチャーを初期化
        self.savant_fetcher = SavantStatcastFetcher()
        
        # 2025年のwOBA係数（FanGraphs）
        self.woba_weights = {
            'bb': 0.696,
            'hbp': 0.720,
            '1b': 0.883,
            '2b': 1.244,
            '3b': 1.569,
            'hr': 2.007
        }
        self.woba_scale = 1.157
        self.league_wobacon = 0.370
    
    def get_team_quality_stats(self, team_id):
        """
        チームの打撃品質統計を取得（Savantデータ使用）
        
        Args:
            team_id (int): チームID
            
        Returns:
            dict: Barrel%, Hard-Hit%を含む辞書
        """
        try:
            # キャッシュチェック
            cache_file = os.path.join(self.cache_dir, f"team_{team_id}_quality.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=6):
                    self.logger.info(f"Using cached quality stats for team {team_id}")
                    return cache_data['data']
            
            # Savantデータを取得
            statcast_data = self.savant_fetcher.get_team_statcast_data(team_id)
            
            result = {
                'barrel_pct': statcast_data['barrel_pct'],
                'hard_hit_pct': statcast_data['hard_hit_pct'],
                'data_source': statcast_data['source']
            }
            
            # キャッシュに保存
            cache_data = {
                'team_id': team_id,
                'data': result,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting quality stats: {str(e)}")
            # エラー時はデフォルト値を返す
            return {
                'barrel_pct': 8.0,
                'hard_hit_pct': 40.0,
                'data_source': 'error'
            }
    
    def _safe_float(self, value, default=0):
        """文字列または数値を安全にfloatに変換"""
        try:
            if isinstance(value, str):
                return float(value)
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default=0):
        """文字列または数値を安全にintに変換"""
        try:
            if isinstance(value, str):
                return int(float(value))  # "123.0"のような場合にも対応
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def calculate_woba(self, team_stats):
        """
        チームのwOBAとxwOBAを計算
        
        Args:
            team_stats (dict): チームの打撃統計
            
        Returns:
            dict: wOBAとxwOBAを含む辞書
        """
        try:
            # 必要な統計を取得（文字列を数値に変換）
            bb = self._safe_int(team_stats.get('baseOnBalls', 0))
            hbp = self._safe_int(team_stats.get('hitByPitch', 0))
            hits = self._safe_int(team_stats.get('hits', 0))
            doubles = self._safe_int(team_stats.get('doubles', 0))
            triples = self._safe_int(team_stats.get('triples', 0))
            hr = self._safe_int(team_stats.get('homeRuns', 0))
            ab = self._safe_int(team_stats.get('atBats', 0))
            sf = self._safe_int(team_stats.get('sacFlies', 0))
            ibb = self._safe_int(team_stats.get('intentionalWalks', 0))
            
            # シングルヒットを計算
            singles = hits - doubles - triples - hr
            
            # wOBAを計算
            numerator = (
                self.woba_weights['bb'] * bb +
                self.woba_weights['hbp'] * hbp +
                self.woba_weights['1b'] * singles +
                self.woba_weights['2b'] * doubles +
                self.woba_weights['3b'] * triples +
                self.woba_weights['hr'] * hr
            )
            
            denominator = ab + bb - ibb + sf + hbp
            
            if denominator > 0:
                woba = numerator / denominator
            else:
                woba = 0.300  # デフォルト値
            
            # xwOBAは簡易的に計算（実際の期待値ではなく推定）
            # OPSとの相関から推定（修正版の計算式）
            ops = self._safe_float(team_stats.get('ops', 0.700))
            xwoba = 0.220 + (0.13 * ops)  # より控えめな推定式
            
            return {
                'woba': round(woba, 3),
                'xwoba': round(xwoba, 3)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating wOBA: {str(e)}")
            return {
                'woba': 0.300,
                'xwoba': 0.300
            }
    
    def refresh_all_teams_data(self):
        """全チームのStatcastデータを更新"""
        self.logger.info("Refreshing all teams Statcast data...")
        
        # Savantから最新データを取得
        all_data = self.savant_fetcher.get_all_teams_statcast_data()
        
        # 統計情報を表示
        print("\n=== Updated Batting Quality Stats ===")
        print(f"{'Team':<4} {'Barrel%':>8} {'Hard-Hit%':>10} {'Source':>10}")
        print("-" * 35)
        
        for team_id, data in sorted(all_data.items()):
            team_abbr = self.savant_fetcher.team_mapping.get(team_id, f"T{team_id}")
            print(f"{team_abbr:<4} {data['barrel_pct']:>7.1f}% "
                  f"{data['hard_hit_pct']:>9.1f}% {data['source']:>10}")
        
        return all_data


# テスト用のメイン関数
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    stats = BattingQualityStats()
    
    # 特定チームのテスト
    test_teams = [147, 110, 136]  # Yankees, Orioles, Mariners
    
    print("\n=== Team Quality Stats Test ===")
    for team_id in test_teams:
        result = stats.get_team_quality_stats(team_id)
        print(f"Team {team_id}: {result}")
    
    # 全チームデータの更新
    print("\n=== Refreshing All Teams ===")
    stats.refresh_all_teams_data()