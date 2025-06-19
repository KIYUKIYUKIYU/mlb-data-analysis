"""
MLB対戦比較分析スクリプト
2チーム間の投手陣・打撃陣を比較し、試合予想に役立つデータを生成
"""
import json
import os
from datetime import datetime
from typing import Dict, Tuple
import pandas as pd
from scripts.advanced_stats_collector import AdvancedStatsCollector


class MatchupAnalyzer:
    def __init__(self):
        self.collector = AdvancedStatsCollector()
        self.processed_path = "data/processed"
        
    def load_team_data(self, team_id: int, season: int = 2024) -> Dict:
        """保存済みのチームデータを読み込み"""
        filepath = os.path.join(self.processed_path, f"team_analysis_{team_id}_{season}.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # データがない場合は新規作成
            print(f"データが見つかりません。新規作成中...")
            team_info = self._get_team_info(team_id)
            return self.collector.save_team_analysis(team_id, team_info['name'], season)
            
    def _get_team_info(self, team_id: int) -> Dict:
        """チーム情報を取得"""
        teams = self.collector.client._make_request("teams?season=2024&sportId=1")
        for team in teams.get('teams', []):
            if team['id'] == team_id:
                return team
        return {'name': 'Unknown Team'}
        
    def compare_pitching_staffs(self, team1_data: Dict, team2_data: Dict) -> pd.DataFrame:
        """投手陣の比較"""
        pitching1 = team1_data['pitching']
        pitching2 = team2_data['pitching']
        
        # 先発投手の平均成績を計算
        def calc_starters_avg(starters):
            if not starters:
                return {'era': 0, 'fip': 0, 'whip': 0, 'qsRate': 0}
            
            total = len(starters)
            return {
                'era': round(sum(float(s.get('era', 0)) for s in starters) / total, 3),
                'fip': round(sum(s.get('fip', 0) for s in starters) / total, 3),
                'whip': round(sum(float(s.get('whip', 0)) for s in starters) / total, 3),
                'qsRate': round(sum(s.get('qsRate', 0) for s in starters) / total, 3)
            }
            
        starters1_avg = calc_starters_avg(pitching1['starters'])
        starters2_avg = calc_starters_avg(pitching2['starters'])
        
        bullpen1 = pitching1['bullpenAggregate']
        bullpen2 = pitching2['bullpenAggregate']
        
        # 比較データフレーム作成
        comparison_data = {
            '指標': [
                '先発防御率', '先発FIP', '先発WHIP', 'QS率',
                '中継ぎ防御率', '中継ぎWHIP'
            ],
            team1_data['teamName']: [
                starters1_avg['era'],
                starters1_avg['fip'],
                starters1_avg['whip'],
                f"{starters1_avg['qsRate']:.1%}",
                bullpen1.get('era', 'N/A'),
                bullpen1.get('whip', 'N/A')
            ],
            team2_data['teamName']: [
                starters2_avg['era'],
                starters2_avg['fip'],
                starters2_avg['whip'],
                f"{starters2_avg['qsRate']:.1%}",
                bullpen2.get('era', 'N/A'),
                bullpen2.get('whip', 'N/A')
            ]
        }
        
        # 優劣判定（数値が低い方が良い指標）
        better_team = []
        for i, metric in enumerate(comparison_data['指標']):
            if metric == 'QS率':  # QS率は高い方が良い
                val1 = starters1_avg['qsRate']
                val2 = starters2_avg['qsRate']
                better_team.append('→' if val1 > val2 else '←' if val2 > val1 else '＝')
            else:  # その他は低い方が良い
                val1 = comparison_data[team1_data['teamName']][i]
                val2 = comparison_data[team2_data['teamName']][i]
                if isinstance(val1, str) or isinstance(val2, str):
                    better_team.append('＝')
                else:
                    better_team.append('→' if val1 < val2 else '←' if val2 < val1 else '＝')
                    
        comparison_data['優位'] = better_team
        
        return pd.DataFrame(comparison_data)
        
    def compare_batting(self, team1_data: Dict, team2_data: Dict) -> pd.DataFrame:
        """打撃陣の比較"""
        batting1 = team1_data['batting']
        batting2 = team2_data['batting']
        
        comparison_data = {
            '指標': ['打率', 'OPS', '得点', '打点'],
            team1_data['teamName']: [
                batting1.get('avg', 'N/A'),
                batting1.get('ops', 'N/A'),
                batting1.get('runs', 0),
                batting1.get('rbi', 0)
            ],
            team2_data['teamName']: [
                batting2.get('avg', 'N/A'),
                batting2.get('ops', 'N/A'),
                batting2.get('runs', 0),
                batting2.get('rbi', 0)
            ]
        }
        
        # 優劣判定（数値が高い方が良い）
        better_team = []
        for i, val1 in enumerate(comparison_data[team1_data['teamName']]):
            val2 = comparison_data[team2_data['teamName']][i]
            if isinstance(val1, str) or isinstance(val2, str):
                better_team.append('＝')
            else:
                better_team.append('→' if val1 > val2 else '←' if val2 < val1 else '＝')
                
        comparison_data['優位'] = better_team
        
        return pd.DataFrame(comparison_data)
        
    def generate_matchup_report(self, team1_id: int, team2_id: int, season: int = 2024):
        """対戦レポートを生成"""
        print(f"\n{'='*60}")
        print(f"⚾ 対戦分析レポート生成中...")
        print(f"{'='*60}\n")
        
        # データ読み込み
        team1_data = self.load_team_data(team1_id, season)
        team2_data = self.load_team_data(team2_id, season)
        
        print(f"\n🏟️  {team1_data['teamName']} vs {team2_data['teamName']}")
        print("=" * 60)
        
        # 投手陣比較
        print("\n📊 投手陣比較")
        print("-" * 40)
        pitching_comparison = self.compare_pitching_staffs(team1_data, team2_data)
        print(pitching_comparison.to_string(index=False))
        
        # 打撃陣比較
        print("\n\n📊 打撃陣比較")
        print("-" * 40)
        batting_comparison = self.compare_batting(team1_data, team2_data)
        print(batting_comparison.to_string(index=False))
        
        # 総合評価
        print("\n\n🎯 総合評価")
        print("-" * 40)
        
        # ポイント計算
        team1_points = 0
        team2_points = 0
        
        for df in [pitching_comparison, batting_comparison]:
            team1_points += (df['優位'] == '→').sum()
            team2_points += (df['優位'] == '←').sum()
            
        print(f"{team1_data['teamName']}: {team1_points}ポイント")
        print(f"{team2_data['teamName']}: {team2_points}ポイント")
        
        if team1_points > team2_points:
            print(f"\n予想: {team1_data['teamName']}が優位")
        elif team2_points > team1_points:
            print(f"\n予想: {team2_data['teamName']}が優位")
        else:
            print("\n予想: 互角の戦い")
            
        # CSV保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"matchup_{team1_id}_vs_{team2_id}_{timestamp}.csv"
        csv_path = os.path.join(self.processed_path, csv_filename)
        
        # 全データを結合
        all_data = pd.concat([
            pd.DataFrame([['投手陣比較', '', '', '']]),
            pitching_comparison,
            pd.DataFrame([['', '', '', '']]),
            pd.DataFrame([['打撃陣比較', '', '', '']]),
            batting_comparison
        ], ignore_index=True)
        
        all_data.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n📁 詳細データ保存: {csv_path}")
        
        return {
            'pitching': pitching_comparison,
            'batting': batting_comparison,
            'team1_points': team1_points,
            'team2_points': team2_points
        }
        

def main():
    """メイン実行関数"""
    analyzer = MatchupAnalyzer()
    
    print("\n🚀 MLB対戦分析システム")
    print("=" * 60)
    
    # デモ: ヤンキース vs レッドソックス
    print("デモ: Yankees (147) vs Red Sox (111) の分析")
    
    # レッドソックスのデータも必要なので先に取得
    print("\nまずRed Soxのデータを準備中...")
    analyzer.collector.save_team_analysis(111, "Boston Red Sox", 2024)
    
    # 対戦分析実行
    analyzer.generate_matchup_report(147, 111, 2024)
    
    print("\n\n💡 使い方:")
    print("他のチームで分析する場合:")
    print("1. analyzer.collector.save_team_analysis(team_id, 'Team Name', 2024)")
    print("2. analyzer.generate_matchup_report(team1_id, team2_id, 2024)")
    print("\nチームIDは data/raw/teams/teams_2024.json で確認できます")
    

if __name__ == "__main__":
    main()