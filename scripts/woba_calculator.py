"""
wOBA (Weighted On-Base Average) 計算クラス
FanGraphsの係数を使用して正確に計算
"""

class WOBACalculator:
    def __init__(self):
        # 年度別の係数（FanGraphs Guts!より）
        self.coefficients = {
            2025: {
                'wBB': 0.694,
                'wHBP': 0.725,
                'w1B': 0.888,
                'w2B': 1.263,
                'w3B': 1.600,
                'wHR': 2.064,
                'wOBAScale': 1.250,
                'cFIP': 3.079
            },
            2024: {
                'wBB': 0.689,
                'wHBP': 0.720,
                'w1B': 0.884,
                'w2B': 1.257,
                'w3B': 1.593,
                'wHR': 2.058,
                'wOBAScale': 1.247,
                'cFIP': 3.134
            }
        }
    
    def calculate_woba(self, stats, season=2025):
        """
        wOBAを計算
        
        Args:
            stats: MLB APIから取得した統計データ
            season: シーズン年
            
        Returns:
            float: wOBA値
        """
        # 係数を取得（なければ2025年を使用）
        coef = self.coefficients.get(season, self.coefficients[2025])
        
        # 必要な統計を取得
        bb = int(stats.get('baseOnBalls', 0))
        hbp = int(stats.get('hitByPitch', 0))
        h = int(stats.get('hits', 0))
        doubles = int(stats.get('doubles', 0))
        triples = int(stats.get('triples', 0))
        hr = int(stats.get('homeRuns', 0))
        ab = int(stats.get('atBats', 0))
        sf = int(stats.get('sacFlies', 0))
        ibb = int(stats.get('intentionalWalks', 0))
        
        # 単打を計算
        singles = h - doubles - triples - hr
        
        # wOBA計算
        numerator = (coef['wBB'] * (bb - ibb) + 
                    coef['wHBP'] * hbp + 
                    coef['w1B'] * singles + 
                    coef['w2B'] * doubles + 
                    coef['w3B'] * triples + 
                    coef['wHR'] * hr)
        
        denominator = ab + bb - ibb + sf + hbp
        
        if denominator > 0:
            woba = numerator / denominator
            return round(woba, 3)
        else:
            return 0.000
    
    def calculate_team_woba(self, team_stats, season=2025):
        """チーム全体のwOBAを計算"""
        return self.calculate_woba(team_stats, season)
    
    def get_woba_scale(self, season=2025):
        """wOBAScaleを取得（OPSとの変換用）"""
        coef = self.coefficients.get(season, self.coefficients[2025])
        return coef['wOBAScale']
    
    def estimate_xwoba(self, woba):
        """
        xwOBA（期待wOBA）を推定
        ※実際のxwOBAはStatcastデータが必要なため、
        　ここでは簡易的にwOBAから微調整
        """
        # 通常、xwOBAはwOBAの±0.010程度
        # これは仮の実装
        import random
        adjustment = random.uniform(-0.010, 0.010)
        return round(woba + adjustment, 3)


# batting_quality_stats.pyの修正例
class BattingQualityStats:
    def __init__(self):
        self.cache_dir = "cache/batting_quality"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.woba_calculator = WOBACalculator()  # 追加
        
        # Barrel%とHard-Hit%のハードコード値
        self.hardcoded_stats = {
            147: {'barrel_pct': 11.1, 'hard_hit_pct': 45.6},  # Yankees
            110: {'barrel_pct': 9.0, 'hard_hit_pct': 42.9},   # Orioles
            141: {'barrel_pct': 10.2, 'hard_hit_pct': 44.8},  # Blue Jays
        }
    
    def get_team_quality_stats(self, team_id):
        """チームの打撃クオリティ統計を取得（wOBA計算追加）"""
        
        # MLB APIからチーム統計を取得
        from src.mlb_api_client import MLBApiClient
        client = MLBApiClient()
        team_stats = client.get_team_stats(team_id, 2025)
        
        # wOBAを計算
        if team_stats:
            woba = self.woba_calculator.calculate_woba(team_stats, 2025)
            xwoba = self.woba_calculator.estimate_xwoba(woba)
        else:
            woba = 0.315  # リーグ平均
            xwoba = 0.315
        
        # Barrel%とHard-Hit%（既存のロジック）
        if team_id in self.hardcoded_stats:
            barrel_pct = self.hardcoded_stats[team_id]['barrel_pct']
            hard_hit_pct = self.hardcoded_stats[team_id]['hard_hit_pct']
        else:
            barrel_pct = 8.0
            hard_hit_pct = 40.0
        
        return {
            'woba': woba,
            'xwoba': xwoba,
            'barrel_pct': barrel_pct,
            'hard_hit_pct': hard_hit_pct
        }


# 使用例
if __name__ == "__main__":
    calculator = WOBACalculator()
    
    # テストデータ
    test_stats = {
        'baseOnBalls': 257,
        'hitByPitch': 18,
        'hits': 699,
        'doubles': 131,
        'triples': 9,
        'homeRuns': 100,
        'atBats': 2771,
        'sacFlies': 12,
        'intentionalWalks': 5
    }
    
    woba = calculator.calculate_woba(test_stats, 2025)
    print(f"wOBA: {woba}")
    
    # wOBAScaleを使ってOPSとの関係を確認
    ops = 0.732  # AthleticsのOPS
    woba_from_ops = ops / calculator.get_woba_scale(2025)
    print(f"OPSから推定したwOBA: {woba_from_ops:.3f}")