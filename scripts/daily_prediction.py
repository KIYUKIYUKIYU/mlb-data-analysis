"""
MLB明日の試合予想スクリプト
翌日の全試合を分析し、予想レポートを生成
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from scripts.matchup_analyzer import MatchupAnalyzer
from scripts.advanced_stats_collector import AdvancedStatsCollector
from src.mlb_api_client import MLBApiClient
import pandas as pd


class DailyPredictionSystem:
    def __init__(self):
        self.client = MLBApiClient()
        self.analyzer = MatchupAnalyzer()
        self.collector = AdvancedStatsCollector()
        self.predictions_path = "data/predictions"
        
        # 予測用フォルダ作成
        if not os.path.exists(self.predictions_path):
            os.makedirs(self.predictions_path)
            
    def get_tomorrow_games_mlb_time(self):
        """MLB時間基準で明日の試合を取得"""
        # 日本時間から米国東部時間を計算
        japan_now = datetime.now()
        et_now = japan_now - timedelta(hours=13)  # 夏時間
        
        # 明日の日付（MLB基準）
        if japan_now.hour < 13:  # 日本の午後1時前なら、MLBはまだ前日
            mlb_tomorrow = et_now.strftime('%Y-%m-%d')
        else:
            mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
            
        print(f"日本時間: {japan_now.strftime('%Y-%m-%d %H:%M')}")
        print(f"MLB基準の明日: {mlb_tomorrow}")
        
        # スケジュール取得
        schedule = self.client._make_request(f"schedule?sportId=1&date={mlb_tomorrow}")
        
        if not schedule.get('dates'):
            return []
            
        return schedule['dates'][0].get('games', [])
        
    def get_probable_starters(self, game: Dict) -> Dict:
        """試合の先発投手情報を取得"""
        result = {
            'away_starter': None,
            'home_starter': None,
            'away_starter_id': None,
            'home_starter_id': None
        }
        
        # まずscheduleデータから確認
        away_pitcher = game['teams']['away'].get('probablePitcher', {})
        home_pitcher = game['teams']['home'].get('probablePitcher', {})
        
        if away_pitcher.get('id'):
            result['away_starter'] = away_pitcher.get('fullName')
            result['away_starter_id'] = away_pitcher.get('id')
            
        if home_pitcher.get('id'):
            result['home_starter'] = home_pitcher.get('fullName')
            result['home_starter_id'] = home_pitcher.get('id')
            
        # もし取得できない場合は、ローテーション予測を実装
        # （ここでは簡略化）
        
        return result
        
    def analyze_matchup_for_prediction(self, game: Dict) -> Dict:
        """試合の対戦分析を実行"""
        away_team = game['teams']['away']['team']
        home_team = game['teams']['home']['team']
        
        print(f"\n分析中: {away_team['name']} @ {home_team['name']}")
        
        # チームデータが存在するか確認、なければ作成
        away_data_path = f"data/processed/team_analysis_{away_team['id']}_2024.json"
        home_data_path = f"data/processed/team_analysis_{home_team['id']}_2024.json"
        
        if not os.path.exists(away_data_path):
            print(f"  {away_team['name']}のデータを作成中...")
            self.collector.save_team_analysis(away_team['id'], away_team['name'], 2024)
            
        if not os.path.exists(home_data_path):
            print(f"  {home_team['name']}のデータを作成中...")
            self.collector.save_team_analysis(home_team['id'], home_team['name'], 2024)
            
        # 対戦分析
        matchup_result = self.analyzer.generate_matchup_report(
            away_team['id'], 
            home_team['id'], 
            2024
        )
        
        # 先発投手情報を追加
        starters = self.get_probable_starters(game)
        
        # 予想結果をまとめる
        prediction = {
            'game_id': game['gamePk'],
            'game_date': game['gameDate'],
            'away_team': away_team['name'],
            'home_team': home_team['name'],
            'away_team_id': away_team['id'],
            'home_team_id': home_team['id'],
            'away_starter': starters['away_starter'] or '未定',
            'home_starter': starters['home_starter'] or '未定',
            'away_points': matchup_result['team1_points'],
            'home_points': matchup_result['team2_points'],
            'prediction': 'away' if matchup_result['team1_points'] > matchup_result['team2_points'] else 'home',
            'confidence': abs(matchup_result['team1_points'] - matchup_result['team2_points'])
        }
        
        return prediction
        
    def generate_daily_predictions(self):
        """明日の全試合の予想を生成"""
        print("\n" + "="*60)
        print("🔮 MLB明日の試合予想システム")
        print("="*60)
        
        # 明日の試合取得
        games = self.get_tomorrow_games_mlb_time()
        
        if not games:
            print("明日は試合がありません。")
            return
            
        print(f"\n明日の試合数: {len(games)}")
        
        predictions = []
        
        # 各試合を分析（デモのため最初の3試合のみ）
        for i, game in enumerate(games[:3], 1):
            print(f"\n[{i}/3] ", end="")
            prediction = self.analyze_matchup_for_prediction(game)
            predictions.append(prediction)
            
        # 予想結果のサマリー作成
        self.create_prediction_summary(predictions)
        
    def create_prediction_summary(self, predictions: List[Dict]):
        """予想結果のサマリーを作成"""
        print("\n" + "="*60)
        print("📊 明日の試合予想サマリー")
        print("="*60)
        
        # データフレーム作成
        df = pd.DataFrame(predictions)
        
        # 予想結果を見やすく整形
        for _, pred in df.iterrows():
            print(f"\n🏟️  {pred['away_team']} @ {pred['home_team']}")
            print(f"   先発: {pred['away_starter']} vs {pred['home_starter']}")
            
            winner = pred['away_team'] if pred['prediction'] == 'away' else pred['home_team']
            confidence_level = '高' if pred['confidence'] >= 3 else '中' if pred['confidence'] >= 2 else '低'
            
            print(f"   予想: {winner} (信頼度: {confidence_level})")
            print(f"   ポイント: {pred['away_team']} {pred['away_points']} - {pred['home_points']} {pred['home_team']}")
            
        # CSV保存
        timestamp = datetime.now().strftime("%Y%m%d")
        csv_path = os.path.join(self.predictions_path, f"predictions_{timestamp}.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"\n📁 予想データ保存: {csv_path}")
        
        # 統計情報
        print(f"\n📈 予想統計:")
        print(f"   ホーム勝利予想: {len(df[df['prediction'] == 'home'])}試合")
        print(f"   アウェイ勝利予想: {len(df[df['prediction'] == 'away'])}試合")
        print(f"   高信頼度予想: {len(df[df['confidence'] >= 3])}試合")
        

def main():
    """メイン実行関数"""
    predictor = DailyPredictionSystem()
    predictor.generate_daily_predictions()
    
    print("\n💡 使い方:")
    print("- 全試合を分析する場合: games[:3] を games に変更")
    print("- 毎日実行して予想精度を追跡可能")
    

if __name__ == "__main__":
    main()