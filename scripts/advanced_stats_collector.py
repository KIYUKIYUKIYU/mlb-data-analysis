"""
MLB高度統計データ収集・分析スクリプト
試合予想のための投手・打撃データを収集し、計算する
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.mlb_api_client import MLBApiClient
import time


class AdvancedStatsCollector:
    def __init__(self):
        self.client = MLBApiClient()
        self.base_path = "data/raw"
        self.processed_path = "data/processed"
        
    def calculate_fip(self, stats: Dict) -> float:
        """FIP (Fielding Independent Pitching) を計算"""
        try:
            hr = stats.get('homeRuns', 0)
            bb = stats.get('baseOnBalls', 0)
            hbp = stats.get('hitByPitch', 0)
            k = stats.get('strikeOuts', 0)
            ip = float(stats.get('inningsPitched', 1))
            
            # FIP定数は通常3.2程度
            fip_constant = 3.2
            fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / ip + fip_constant
            return round(fip, 3)
        except:
            return 0.0
            
    def calculate_rates(self, stats: Dict) -> Dict:
        """各種率を計算（三振率、ゴロ率、フライ率）"""
        try:
            batters_faced = stats.get('battersFaced', 1)
            ground_outs = stats.get('groundOuts', 0)
            air_outs = stats.get('airOuts', 0)
            total_outs = ground_outs + air_outs
            
            return {
                'strikeoutRate': round(stats.get('strikeOuts', 0) / batters_faced, 3),
                'groundBallRate': round(ground_outs / total_outs, 3) if total_outs > 0 else 0,
                'flyBallRate': round(air_outs / total_outs, 3) if total_outs > 0 else 0
            }
        except:
            return {'strikeoutRate': 0, 'groundBallRate': 0, 'flyBallRate': 0}
            
    def calculate_qs_rate(self, game_logs: List[Dict]) -> float:
        """QS率を計算（6イニング以上、3自責点以下）"""
        if not game_logs:
            return 0.0
            
        starts = 0
        quality_starts = 0
        
        for game in game_logs:
            if game.get('isStarter', False):
                starts += 1
                innings = float(game.get('inningsPitched', 0))
                earned_runs = game.get('earnedRuns', 0)
                
                if innings >= 6.0 and earned_runs <= 3:
                    quality_starts += 1
                    
        return round(quality_starts / starts, 3) if starts > 0 else 0.0
        
    def get_pitcher_advanced_stats(self, pitcher_id: int, season: int = 2024) -> Dict:
        """投手の高度な統計情報を取得"""
        print(f"  投手ID {pitcher_id} のデータ取得中...")
        
        # 基本統計
        season_stats = self.client._make_request(f"people/{pitcher_id}/stats?stats=season&season={season}&group=pitching")
        
        # ゲームログ（QS率計算用）
        game_log = self.client._make_request(f"people/{pitcher_id}/stats?stats=gameLog&season={season}&group=pitching")
        
        # 左右別成績
        splits = self.client._make_request(f"people/{pitcher_id}/stats?stats=statSplits&season={season}&group=pitching")
        
        # 投手情報
        player_info = self.client._make_request(f"people/{pitcher_id}")
        
        result = {
            'id': pitcher_id,
            'name': player_info.get('people', [{}])[0].get('fullName', 'Unknown'),
            'handedness': player_info.get('people', [{}])[0].get('pitchHand', {}).get('code', 'R')
        }
        
        # 基本統計の処理
        if season_stats and season_stats.get('stats'):
            stat_data = season_stats['stats'][0].get('splits', [{}])[0].get('stat', {})
            
            result.update({
                'era': stat_data.get('era', '0.00'),
                'whip': stat_data.get('whip', '0.00'),
                'fip': self.calculate_fip(stat_data),
                'strikeouts': stat_data.get('strikeOuts', 0),
                'innings': stat_data.get('inningsPitched', '0.0'),
                'gamesStarted': stat_data.get('gamesStarted', 0)
            })
            
            # 率の計算
            rates = self.calculate_rates(stat_data)
            result.update(rates)
            
        # QS率の計算
        if game_log and game_log.get('stats'):
            game_logs_data = game_log['stats'][0].get('splits', [])
            result['qsRate'] = self.calculate_qs_rate([g.get('stat', {}) for g in game_logs_data])
            
        # 左右別被打率
        if splits and splits.get('stats'):
            vs_left = None
            vs_right = None
            
            for split_group in splits['stats']:
                for split in split_group.get('splits', []):
                    if split.get('split', {}).get('code') == 'vl':  # vs Left
                        vs_left = split.get('stat', {}).get('avg', '.000')
                    elif split.get('split', {}).get('code') == 'vr':  # vs Right
                        vs_right = split.get('stat', {}).get('avg', '.000')
                        
            result['vsLeftAvg'] = vs_left or '.000'
            result['vsRightAvg'] = vs_right or '.000'
            
        time.sleep(0.3)  # API制限対策
        return result
        
    def get_team_pitching_staff(self, team_id: int, season: int = 2024) -> Dict:
        """チームの投手陣データを取得"""
        print(f"\n投手陣データ収集中 (Team ID: {team_id})...")
        
        # ロースター取得
        roster = self.client._make_request(f"teams/{team_id}/roster?season={season}&rosterType=fullRoster")
        
        starters = []
        relievers = []
        
        if roster and roster.get('roster'):
            pitchers = [p for p in roster['roster'] if p.get('position', {}).get('type') == 'Pitcher']
            
            for pitcher in pitchers[:10]:  # デモのため最初の10人のみ
                pitcher_id = pitcher['person']['id']
                pitcher_stats = self.get_pitcher_advanced_stats(pitcher_id, season)
                
                if pitcher_stats.get('gamesStarted', 0) >= 5:  # 5試合以上先発
                    starters.append(pitcher_stats)
                else:
                    relievers.append(pitcher_stats)
                    
        # 中継ぎ陣の総合成績を計算
        bullpen_stats = self.calculate_bullpen_aggregate(relievers)
        
        return {
            'teamId': team_id,
            'season': season,
            'starters': starters,
            'bullpenAggregate': bullpen_stats
        }
        
    def calculate_bullpen_aggregate(self, relievers: List[Dict]) -> Dict:
        """中継ぎ陣の総合成績を計算"""
        if not relievers:
            return {}
            
        total_innings = 0
        total_earned_runs = 0
        total_hits = 0
        total_walks = 0
        
        for reliever in relievers:
            try:
                innings = float(reliever.get('innings', 0))
                era = float(reliever.get('era', 0))
                whip = float(reliever.get('whip', 0))
                
                total_innings += innings
                total_earned_runs += (era * innings / 9)
                total_hits += (whip * innings) * 0.7  # WHIPから推定
                total_walks += (whip * innings) * 0.3
            except:
                continue
                
        if total_innings > 0:
            bullpen_era = round((total_earned_runs * 9) / total_innings, 3)
            bullpen_whip = round((total_hits + total_walks) / total_innings, 3)
        else:
            bullpen_era = 0.0
            bullpen_whip = 0.0
            
        return {
            'era': bullpen_era,
            'whip': bullpen_whip,
            'totalInnings': round(total_innings, 1),
            'pitcherCount': len(relievers)
        }
        
    def get_team_batting_stats(self, team_id: int, season: int = 2024) -> Dict:
        """チームの打撃統計を取得"""
        print(f"\n打撃データ収集中 (Team ID: {team_id})...")
        
        # チーム全体の統計
        team_stats = self.client._make_request(f"teams/{team_id}/stats?season={season}&stats=season&group=hitting")
        
        result = {
            'teamId': team_id,
            'season': season
        }
        
        if team_stats and team_stats.get('stats'):
            hitting_stats = team_stats['stats'][0].get('splits', [{}])[0].get('stat', {})
            
            result.update({
                'avg': hitting_stats.get('avg', '.000'),
                'ops': hitting_stats.get('ops', '.000'),
                'hits': hitting_stats.get('hits', 0),
                'runs': hitting_stats.get('runs', 0),
                'rbi': hitting_stats.get('rbi', 0)
            })
            
        return result
        
    def save_team_analysis(self, team_id: int, team_name: str, season: int = 2024):
        """チームの総合分析データを保存"""
        print(f"\n{'='*50}")
        print(f"📊 {team_name} の分析データ作成中...")
        print(f"{'='*50}")
        
        # 投手陣データ
        pitching_data = self.get_team_pitching_staff(team_id, season)
        
        # 打撃データ
        batting_data = self.get_team_batting_stats(team_id, season)
        
        # 統合データ
        team_analysis = {
            'teamId': team_id,
            'teamName': team_name,
            'season': season,
            'analyzedAt': datetime.now().isoformat(),
            'pitching': pitching_data,
            'batting': batting_data
        }
        
        # 保存
        filepath = os.path.join(self.processed_path, f"team_analysis_{team_id}_{season}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(team_analysis, f, ensure_ascii=False, indent=2)
            
        print(f"\n✅ 分析完了！保存先: {filepath}")
        return team_analysis
        

def main():
    """メイン実行関数"""
    collector = AdvancedStatsCollector()
    
    # デモ: ヤンキースのデータを分析
    print("\n🚀 高度統計分析デモ開始")
    print("（New York Yankeesのデータを分析します）")
    
    analysis = collector.save_team_analysis(147, "New York Yankees", 2024)
    
    # 結果サマリー表示
    print("\n📈 分析結果サマリー:")
    print(f"先発投手数: {len(analysis['pitching']['starters'])}")
    print(f"中継ぎ防御率: {analysis['pitching']['bullpenAggregate'].get('era', 'N/A')}")
    print(f"チーム打率: {analysis['batting'].get('avg', 'N/A')}")
    print(f"チームOPS: {analysis['batting'].get('ops', 'N/A')}")
    
    print("\n💡 次のステップ:")
    print("- 他のチームも分析する")
    print("- 2チーム間の比較機能を追加")
    print("- 過去N試合の成績を追加")
    

if __name__ == "__main__":
    main()