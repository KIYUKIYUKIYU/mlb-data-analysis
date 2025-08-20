"""
MLB明日の試合予想スクリプト（先発投手取得修正版）
hydrate=probablePitcherを使用して確実に先発投手を取得
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from scripts.matchup_analyzer import MatchupAnalyzer
from scripts.advanced_stats_collector import AdvancedStatsCollector
from scripts.complete_data_collector import CompleteDataCollector
from src.mlb_api_client import MLBApiClient
import pandas as pd


class UpdatedDailyPredictionSystem:
    def __init__(self):
        self.client = MLBApiClient()
        self.analyzer = MatchupAnalyzer()
        self.collector = AdvancedStatsCollector()
        self.complete_collector = CompleteDataCollector()
        self.predictions_path = "data/predictions"
        
        if not os.path.exists(self.predictions_path):
            os.makedirs(self.predictions_path)
            
    def get_tomorrow_games_with_pitchers(self):
        """先発投手情報を含む明日の試合を取得"""
        # 日本時間から米国東部時間を計算
        japan_now = datetime.now()
        et_now = japan_now - timedelta(hours=13)
        
        # 明日の日付（MLB基準）
        if japan_now.hour < 13:
            mlb_tomorrow = et_now.strftime('%Y-%m-%d')
        else:
            mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
            
        print(f"日本時間: {japan_now.strftime('%Y-%m-%d %H:%M')}")
        print(f"MLB基準の明日: {mlb_tomorrow}")
        
        # hydrate=probablePitcherを使用してスケジュール取得
        schedule = self.client._make_request(
            f"schedule?sportId=1&date={mlb_tomorrow}&hydrate=probablePitcher"
        )
        
        if not schedule.get('dates'):
            return []
            
        return schedule['dates'][0].get('games', [])
        
    def create_complete_matchup_data(self, game: Dict) -> Dict:
        """完全な対戦データを作成（N/Aを最小限に）"""
        away_team = game['teams']['away']['team']
        home_team = game['teams']['home']['team']
        
        print(f"\n分析中: {away_team['name']} @ {home_team['name']}")
        
        # 先発投手情報（hydrateで取得済み）
        away_pitcher = game['teams']['away'].get('probablePitcher', {})
        home_pitcher = game['teams']['home'].get('probablePitcher', {})
        
        # 投手の詳細成績を取得
        away_pitcher_stats = {}
        home_pitcher_stats = {}
        
        if away_pitcher.get('id'):
            away_pitcher_stats = self.complete_collector._get_pitcher_current_stats(away_pitcher['id'])
        if home_pitcher.get('id'):
            home_pitcher_stats = self.complete_collector._get_pitcher_current_stats(home_pitcher['id'])
            
        # チーム成績（過去N試合含む）
        away_season = self.complete_collector._get_team_season_stats(away_team['id'])
        home_season = self.complete_collector._get_team_season_stats(home_team['id'])
        
        # 過去N試合のOPS
        print("  過去試合のOPS計算中...")
        away_recent = self.complete_collector.get_recent_games_stats(away_team['id'], 10)
        home_recent = self.complete_collector.get_recent_games_stats(home_team['id'], 10)
        
        # 投手陣成績
        away_pitching = self.complete_collector._get_team_pitching_stats(away_team['id'])
        home_pitching = self.complete_collector._get_team_pitching_stats(home_team['id'])
        
        return {
            'game_id': game['gamePk'],
            'game_date': game['gameDate'],
            'game_time_jp': self._convert_to_japan_time(game['gameDate']),
            'away': {
                'team': away_team['name'],
                'team_id': away_team['id'],
                'pitcher': {
                    'name': away_pitcher.get('fullName', '未定'),
                    'id': away_pitcher.get('id'),
                    'era': away_pitcher_stats.get('era', 'N/A'),
                    'whip': away_pitcher_stats.get('whip', 'N/A'),
                    'wins': away_pitcher_stats.get('wins', 0),
                    'losses': away_pitcher_stats.get('losses', 0)
                },
                'batting': {
                    'avg': away_season.get('avg', '.000'),
                    'ops': away_season.get('ops', '.000'),
                    'runs': away_season.get('runs', 0),
                    'last5_ops': f"{away_recent['last5']:.3f}" if away_recent['last5'] else 'N/A',
                    'last10_ops': f"{away_recent['last10']:.3f}" if away_recent['last10'] else 'N/A'
                },
                'pitching': {
                    'era': away_pitching.get('era', 'N/A'),
                    'whip': away_pitching.get('whip', 'N/A')
                }
            },
            'home': {
                'team': home_team['name'],
                'team_id': home_team['id'],
                'pitcher': {
                    'name': home_pitcher.get('fullName', '未定'),
                    'id': home_pitcher.get('id'),
                    'era': home_pitcher_stats.get('era', 'N/A'),
                    'whip': home_pitcher_stats.get('whip', 'N/A'),
                    'wins': home_pitcher_stats.get('wins', 0),
                    'losses': home_pitcher_stats.get('losses', 0)
                },
                'batting': {
                    'avg': home_season.get('avg', '.000'),
                    'ops': home_season.get('ops', '.000'),
                    'runs': home_season.get('runs', 0),
                    'last5_ops': f"{home_recent['last5']:.3f}" if home_recent['last5'] else 'N/A',
                    'last10_ops': f"{home_recent['last10']:.3f}" if home_recent['last10'] else 'N/A'
                },
                'pitching': {
                    'era': home_pitching.get('era', 'N/A'),
                    'whip': home_pitching.get('whip', 'N/A')
                }
            }
        }
        
    def _convert_to_japan_time(self, utc_time_str: str) -> str:
        """UTC時間を日本時間に変換"""
        try:
            utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
            japan_time = utc_time + timedelta(hours=9)
            return japan_time.strftime('%m/%d %H:%M')
        except:
            return 'N/A'
            
    def generate_comparison_report(self):
        """データ比較レポートを生成（予想判定なし）"""
        print("\n" + "="*60)
        print("🔍 MLB明日の試合データ比較システム")
        print("="*60)
        
        # 明日の試合取得（先発投手情報付き）
        games = self.get_tomorrow_games_with_pitchers()
        
        if not games:
            print("明日は試合がありません。")
            return
            
        print(f"\n明日の試合数: {len(games)}")
        
        comparisons = []
        
        # 各試合を分析（デモのため最初の3試合）
        for i, game in enumerate(games[:3], 1):
            print(f"\n[{i}/3] ", end="")
            matchup_data = self.create_complete_matchup_data(game)
            comparisons.append(matchup_data)
            
        # 比較レポート作成
        self.create_comparison_summary(comparisons)
        
        return comparisons
        
    def create_comparison_summary(self, comparisons: List[Dict]):
        """比較データのサマリーを作成"""
        print("\n" + "="*60)
        print("📊 明日の試合データ比較")
        print("="*60)
        
        for comp in comparisons:
            print(f"\n🏟️  {comp['away']['team']} @ {comp['home']['team']}")
            print(f"   日本時間: {comp['game_time_jp']}")
            print(f"\n   【先発投手】")
            print(f"   {comp['away']['pitcher']['name']} ({comp['away']['pitcher']['wins']}-{comp['away']['pitcher']['losses']}, ERA {comp['away']['pitcher']['era']})")
            print(f"   vs")
            print(f"   {comp['home']['pitcher']['name']} ({comp['home']['pitcher']['wins']}-{comp['home']['pitcher']['losses']}, ERA {comp['home']['pitcher']['era']})")
            
            print(f"\n   【打撃成績】")
            print(f"   {comp['away']['team']}: AVG {comp['away']['batting']['avg']} | OPS {comp['away']['batting']['ops']} | Last5 {comp['away']['batting']['last5_ops']} | Last10 {comp['away']['batting']['last10_ops']}")
            print(f"   {comp['home']['team']}: AVG {comp['home']['batting']['avg']} | OPS {comp['home']['batting']['ops']} | Last5 {comp['home']['batting']['last5_ops']} | Last10 {comp['home']['batting']['last10_ops']}")
            
            print(f"\n   【チーム投手陣】")
            print(f"   {comp['away']['team']}: ERA {comp['away']['pitching']['era']} | WHIP {comp['away']['pitching']['whip']}")
            print(f"   {comp['home']['team']}: ERA {comp['home']['pitching']['era']} | WHIP {comp['home']['pitching']['whip']}")
            
        # CSV保存
        timestamp = datetime.now().strftime("%Y%m%d")
        csv_path = os.path.join(self.predictions_path, f"comparison_{timestamp}.csv")
        
        # DataFrameに変換して保存
        df_data = []
        for comp in comparisons:
            df_data.append({
                'Game': f"{comp['away']['team']} @ {comp['home']['team']}",
                'Time_JP': comp['game_time_jp'],
                'Away_Pitcher': comp['away']['pitcher']['name'],
                'Away_ERA': comp['away']['pitcher']['era'],
                'Home_Pitcher': comp['home']['pitcher']['name'],
                'Home_ERA': comp['home']['pitcher']['era'],
                'Away_AVG': comp['away']['batting']['avg'],
                'Away_OPS': comp['away']['batting']['ops'],
                'Away_Last5': comp['away']['batting']['last5_ops'],
                'Home_AVG': comp['home']['batting']['avg'],
                'Home_OPS': comp['home']['batting']['ops'],
                'Home_Last5': comp['home']['batting']['last5_ops']
            })
            
        df = pd.DataFrame(df_data)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"\n📁 データ保存: {csv_path}")
        

def main():
    """メイン実行関数"""
    predictor = UpdatedDailyPredictionSystem()
    predictor.generate_comparison_report()
    
    print("\n💡 使い方:")
    print("- 全試合を分析する場合: games[:3] を games に変更")
    print("- データは純粋な比較のみ（予想判定なし）")
    

if __name__ == "__main__":
    main()