"""
三振率、ゴロ率、フライ率などの正確な計算
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mlb_api_client import MLBApiClient
import json
from datetime import datetime

class AccurateRateCalculator:
    def __init__(self):
        self.client = MLBApiClient()
    
    def get_pitcher_stats(self, player_id, season=2024):
        """投手の詳細統計を取得"""
        endpoint = f"people/{player_id}/stats?stats=season&season={season}&gameType=R"
        response = self.client._make_request(endpoint)
        
        if not response or 'stats' not in response:
            return None
            
        # 投球統計を探す
        for stat_group in response['stats']:
            if stat_group.get('group', {}).get('displayName') == 'pitching':
                if 'splits' in stat_group and stat_group['splits']:
                    return stat_group['splits'][0].get('stat', {})
        
        return None
    
    def get_batter_stats(self, player_id, season=2024):
        """打者の詳細統計を取得"""
        endpoint = f"people/{player_id}/stats?stats=season&season={season}&gameType=R"
        response = self.client._make_request(endpoint)
        
        if not response or 'stats' not in response:
            return None
            
        # 打撃統計を探す
        for stat_group in response['stats']:
            if stat_group.get('group', {}).get('displayName') == 'hitting':
                if 'splits' in stat_group and stat_group['splits']:
                    return stat_group['splits'][0].get('stat', {})
        
        return None
    
    def calculate_pitcher_rates(self, stats):
        """投手の各種率を計算"""
        if not stats:
            return {}
            
        results = {}
        
        # 三振率 (K%) = 三振数 / 打者数
        batters_faced = float(stats.get('battersFaced', 0))
        if batters_faced > 0:
            strikeouts = float(stats.get('strikeOuts', 0))
            results['k_rate'] = round((strikeouts / batters_faced) * 100, 1)
            results['k_per_9'] = round((strikeouts / float(stats.get('inningsPitched', 1))) * 9, 1)
        else:
            results['k_rate'] = 0.0
            results['k_per_9'] = 0.0
        
        # 四球率 (BB%) = 四球数 / 打者数
        if batters_faced > 0:
            walks = float(stats.get('baseOnBalls', 0))
            results['bb_rate'] = round((walks / batters_faced) * 100, 1)
            results['bb_per_9'] = round((walks / float(stats.get('inningsPitched', 1))) * 9, 1)
        else:
            results['bb_rate'] = 0.0
            results['bb_per_9'] = 0.0
        
        # K/BB比率
        walks = float(stats.get('baseOnBalls', 0))
        if walks > 0:
            results['k_bb_ratio'] = round(float(stats.get('strikeOuts', 0)) / walks, 2)
        else:
            results['k_bb_ratio'] = float('inf') if stats.get('strikeOuts', 0) > 0 else 0.0
        
        # ゴロ率・フライ率
        ground_outs = float(stats.get('groundOuts', 0))
        air_outs = float(stats.get('airOuts', 0))
        total_batted_balls = ground_outs + air_outs
        
        if total_batted_balls > 0:
            results['ground_ball_rate'] = round((ground_outs / total_batted_balls) * 100, 1)
            results['fly_ball_rate'] = round((air_outs / total_batted_balls) * 100, 1)
            results['gb_fb_ratio'] = round(ground_outs / air_outs, 2) if air_outs > 0 else float('inf')
        else:
            results['ground_ball_rate'] = 0.0
            results['fly_ball_rate'] = 0.0
            results['gb_fb_ratio'] = 0.0
        
        # WHIP
        innings = float(stats.get('inningsPitched', 0))
        if innings > 0:
            hits = float(stats.get('hits', 0))
            walks = float(stats.get('baseOnBalls', 0))
            results['whip'] = round((hits + walks) / innings, 2)
        else:
            results['whip'] = 0.0
        
        return results
    
    def calculate_batter_rates(self, stats):
        """打者の各種率を計算"""
        if not stats:
            return {}
            
        results = {}
        
        # 三振率 (K%) = 三振数 / 打席数
        plate_appearances = float(stats.get('plateAppearances', 0))
        if plate_appearances > 0:
            strikeouts = float(stats.get('strikeOuts', 0))
            results['k_rate'] = round((strikeouts / plate_appearances) * 100, 1)
        else:
            results['k_rate'] = 0.0
        
        # 四球率 (BB%) = 四球数 / 打席数
        if plate_appearances > 0:
            walks = float(stats.get('baseOnBalls', 0))
            results['bb_rate'] = round((walks / plate_appearances) * 100, 1)
        else:
            results['bb_rate'] = 0.0
        
        # BB/K比率
        strikeouts = float(stats.get('strikeOuts', 0))
        if strikeouts > 0:
            results['bb_k_ratio'] = round(float(stats.get('baseOnBalls', 0)) / strikeouts, 2)
        else:
            results['bb_k_ratio'] = float('inf') if stats.get('baseOnBalls', 0) > 0 else 0.0
        
        # ゴロ率・フライ率（打者の場合）
        ground_outs = float(stats.get('groundOuts', 0))
        air_outs = float(stats.get('airOuts', 0))
        total_outs = ground_outs + air_outs
        
        if total_outs > 0:
            results['ground_out_rate'] = round((ground_outs / total_outs) * 100, 1)
            results['air_out_rate'] = round((air_outs / total_outs) * 100, 1)
        else:
            results['ground_out_rate'] = 0.0
            results['air_out_rate'] = 0.0
        
        # ISO (Isolated Power) = SLG - AVG
        avg = float(stats.get('avg', 0))
        slg = float(stats.get('slg', 0))
        results['iso'] = round(slg - avg, 3)
        
        # BABIP
        hits = float(stats.get('hits', 0))
        home_runs = float(stats.get('homeRuns', 0))
        at_bats = float(stats.get('atBats', 0))
        strikeouts = float(stats.get('strikeOuts', 0))
        sac_flies = float(stats.get('sacFlies', 0))
        
        babip_denominator = at_bats - strikeouts - home_runs + sac_flies
        if babip_denominator > 0:
            results['babip'] = round((hits - home_runs) / babip_denominator, 3)
        else:
            results['babip'] = 0.0
        
        return results
    
    def analyze_team_accurate_rates(self, team_id, season=2024):
        """チーム全体の正確な率を分析"""
        roster = self.client.get_team_roster(team_id, season=season)
        if not roster or 'roster' not in roster:
            print(f"チーム{team_id}のロースターが取得できませんでした")
            return None
        
        pitchers = []
        batters = []
        
        print(f"\nチーム{team_id}の正確な率分析を開始...")
        print("（データ取得に時間がかかる場合があります）\n")
        
        player_count = 0
        for player in roster['roster']:
            player_id = player['person']['id']
            player_name = player['person']['fullName']
            position = player.get('position', {}).get('abbreviation', 'N/A')
            
            if position == 'P':
                # 投手の統計
                print(f"投手 {player_name} のデータ取得中...")
                stats = self.get_pitcher_stats(player_id, season=season)
                if stats and float(stats.get('inningsPitched', 0)) > 0:
                    rates = self.calculate_pitcher_rates(stats)
                    pitchers.append({
                        'player_id': player_id,
                        'name': player_name,
                        'innings': stats.get('inningsPitched', 0),
                        'era': stats.get('era', 0),
                        **rates
                    })
                    print(f"  → K%={rates['k_rate']}%, GB%={rates['ground_ball_rate']}%, WHIP={rates['whip']}")
            else:
                # 野手の統計
                print(f"野手 {player_name} ({position}) のデータ取得中...")
                stats = self.get_batter_stats(player_id, season=season)
                if stats and int(stats.get('plateAppearances', 0)) > 0:
                    rates = self.calculate_batter_rates(stats)
                    batters.append({
                        'player_id': player_id,
                        'name': player_name,
                        'position': position,
                        'pa': stats.get('plateAppearances', 0),
                        'avg': stats.get('avg', 0),
                        'ops': stats.get('ops', 0),
                        **rates
                    })
                    print(f"  → K%={rates['k_rate']}%, BB%={rates['bb_rate']}%, ISO={rates['iso']}")
            
            player_count += 1
            # API制限対策
            if player_count % 5 == 0:
                import time
                time.sleep(1)
        
        # データ保存
        output_dir = 'data/processed/accurate_rates'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/team_{team_id}_rates_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'team_id': team_id,
                'timestamp': timestamp,
                'pitchers': pitchers,
                'batters': batters
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n分析結果を保存: {filename}")
        
        # 投手陣のトップ5（K率順）
        if pitchers:
            pitchers_sorted = sorted(pitchers, key=lambda x: x['k_rate'], reverse=True)
            print("\n【投手陣 K率トップ5】")
            for i, p in enumerate(pitchers_sorted[:5], 1):
                print(f"{i}. {p['name']}: K%={p['k_rate']}% (ERA={p['era']})")
            
            avg_k_rate = sum(p['k_rate'] for p in pitchers) / len(pitchers)
            avg_gb_rate = sum(p['ground_ball_rate'] for p in pitchers) / len(pitchers)
            print(f"\n投手陣平均 - K%: {round(avg_k_rate, 1)}%, GB%: {round(avg_gb_rate, 1)}%")
        
        # 野手陣のパワー指標トップ5（ISO順）
        if batters:
            batters_sorted = sorted(batters, key=lambda x: x['iso'], reverse=True)
            print("\n【野手陣 ISOトップ5】")
            for i, b in enumerate(batters_sorted[:5], 1):
                print(f"{i}. {b['name']} ({b['position']}): ISO={b['iso']} (K%={b['k_rate']}%)")
            
            avg_k_rate = sum(b['k_rate'] for b in batters) / len(batters)
            avg_bb_rate = sum(b['bb_rate'] for b in batters) / len(batters)
            print(f"\n野手陣平均 - K%: {round(avg_k_rate, 1)}%, BB%: {round(avg_bb_rate, 1)}%")
        
        return {'pitchers': pitchers, 'batters': batters}

def main():
    calculator = AccurateRateCalculator()
    
    # テスト用：ヤンキースの正確な率を計算
    calculator.analyze_team_accurate_rates(147, season=2024)  # NYY

if __name__ == "__main__":
    main()