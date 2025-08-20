"""
過去N試合のOPS（出塁率＋長打率）を計算するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mlb_api_client import MLBApiClient
from datetime import datetime, timedelta
import json

class RecentOPSCalculator:
    def __init__(self):
        self.client = MLBApiClient()
        
    def get_player_season_stats(self, player_id, season=2024):
        """選手のシーズン統計を取得"""
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
    
    def get_player_game_logs(self, player_id, season=2024):
        """選手のゲームログを取得"""
        endpoint = f"people/{player_id}/stats?stats=gameLog&season={season}&gameType=R"
        response = self.client._make_request(endpoint)
        
        if not response or 'stats' not in response:
            return []
            
        # ゲームログを抽出
        game_logs = []
        for stat_group in response['stats']:
            if 'splits' in stat_group:
                for split in stat_group['splits']:
                    if 'stat' in split and 'date' in split:
                        game_logs.append({
                            'date': split['date'],
                            'stats': split['stat']
                        })
        
        # 日付でソート（新しい順）
        game_logs.sort(key=lambda x: x['date'], reverse=True)
        return game_logs
    
    def calculate_ops_from_logs(self, game_logs):
        """ゲームログからOPSを計算"""
        total_stats = {
            'atBats': 0,
            'hits': 0,
            'doubles': 0,
            'triples': 0,
            'homeRuns': 0,
            'baseOnBalls': 0,
            'hitByPitch': 0,
            'sacFlies': 0
        }
        
        # 各試合の統計を合計
        for log in game_logs:
            stats = log['stats']
            for key in total_stats:
                if key in stats:
                    total_stats[key] += int(stats[key])
        
        # 計算用の値
        ab = total_stats['atBats']
        h = total_stats['hits']
        bb = total_stats['baseOnBalls']
        hbp = total_stats['hitByPitch']
        sf = total_stats['sacFlies']
        
        # OBP（出塁率）計算
        obp_denominator = ab + bb + hbp + sf
        obp = (h + bb + hbp) / obp_denominator if obp_denominator > 0 else 0
        
        # SLG（長打率）計算
        if ab > 0:
            singles = h - total_stats['doubles'] - total_stats['triples'] - total_stats['homeRuns']
            tb = singles + (2 * total_stats['doubles']) + (3 * total_stats['triples']) + (4 * total_stats['homeRuns'])
            slg = tb / ab
        else:
            slg = 0
        
        # OPS計算
        ops = obp + slg
        
        return round(obp, 3), round(slg, 3), round(ops, 3)
    
    def analyze_team_recent_ops(self, team_id, games=5, season=2024):
        """チーム全体の直近OPSを分析"""
        # ロースター取得
        roster = self.client.get_team_roster(team_id, season=season)
        if not roster or 'roster' not in roster:
            print(f"チーム{team_id}のロースターが取得できませんでした")
            return None
            
        results = []
        
        print(f"\nチーム{team_id}の直近{games}試合OPS分析を開始...")
        print("（データ取得に時間がかかる場合があります）")
        
        player_count = 0
        for player in roster['roster']:
            player_id = player['person']['id']
            player_name = player['person']['fullName']
            position = player.get('position', {}).get('abbreviation', 'N/A')
            
            # 投手は除外
            if position == 'P':
                continue
            
            # ゲームログ取得
            print(f"  {player_name} のデータ取得中...")
            game_logs = self.get_player_game_logs(player_id, season=season)
            
            # 直近N試合のログを取得
            recent_logs = game_logs[:games] if len(game_logs) >= games else game_logs
            
            if len(recent_logs) > 0:
                obp, slg, ops = self.calculate_ops_from_logs(recent_logs)
                
                results.append({
                    'player_id': player_id,
                    'name': player_name,
                    'position': position,
                    'games': len(recent_logs),
                    'obp': obp,
                    'slg': slg,
                    'ops': ops
                })
                
                print(f"    → OPS={ops} (OBP={obp}, SLG={slg}) - {len(recent_logs)}試合")
                player_count += 1
                
                # API制限対策（5人ごとに少し待機）
                if player_count % 5 == 0:
                    import time
                    time.sleep(1)
        
        # OPSでソート
        results.sort(key=lambda x: x['ops'], reverse=True)
        
        # データ保存
        output_dir = 'data/processed/recent_ops'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/team_{team_id}_last{games}games_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'team_id': team_id,
                'games': games,
                'timestamp': timestamp,
                'players': results
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\n分析結果を保存: {filename}")
        
        # トップ5を表示
        print(f"\n【直近{games}試合 OPSトップ5】")
        for i, player in enumerate(results[:5], 1):
            print(f"{i}. {player['name']} ({player['position']}): OPS={player['ops']}")
        
        # チーム平均OPS計算
        if results:
            avg_ops = sum(p['ops'] for p in results) / len(results)
            print(f"\nチーム平均OPS (直近{games}試合): {round(avg_ops, 3)}")
        
        return results

def main():
    calculator = RecentOPSCalculator()
    
    # テスト用：まず5試合だけ分析
    print("=== 直近5試合のOPS分析 ===")
    calculator.analyze_team_recent_ops(147, games=5, season=2024)  # NYY
    
    # 10試合分析するか確認
    user_input = input("\n10試合の分析も実行しますか？ (y/n): ")
    if user_input.lower() == 'y':
        print("\n=== 直近10試合のOPS分析 ===")
        calculator.analyze_team_recent_ops(147, games=10, season=2024)

if __name__ == "__main__":
    main()