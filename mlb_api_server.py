from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import pytz
import json
from pathlib import Path
import threading
import time
import schedule

# 既存のモジュールをインポート
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

# インポートの順序を調整
from scripts.enhanced_stats_collector import EnhancedStatsCollector
from scripts.calculate_gb_fb_stats import GBFBCalculator
from scripts.complete_stats_formatter import CompleteStatsFormatter
from scripts.mlb_complete_report_real import MLBCompleteReportReal

app = Flask(__name__)
CORS(app)  # クロスオリジン対応

# データキャッシュ
CACHE_DIR = Path('api_cache')
CACHE_DIR.mkdir(exist_ok=True)

class MLBDataAPIServer:
    def __init__(self):
        self.reporter = MLBCompleteReportReal()
        self.latest_data = {}
        self.update_data()
    
    def update_data(self):
        """データを更新"""
        try:
            print(f"Updating MLB data at {datetime.now()}")
            
            # 日本時間で明日の試合を取得
            jst = pytz.timezone('Asia/Tokyo')
            now_jst = datetime.now(jst)
            est = pytz.timezone('US/Eastern')
            now_est = now_jst.astimezone(est)
            target_date = now_est.date()
            
            # 試合データを取得
            games_data = self.reporter.get_games_for_date(target_date)
            
            if games_data and 'dates' in games_data and games_data['dates']:
                games = games_data['dates'][0]['games']
                
                # 各試合のデータを処理
                processed_games = []
                for game in games:
                    game_info = self.process_game_for_api(game)
                    processed_games.append(game_info)
                
                self.latest_data = {
                    'updated_at': now_jst.isoformat(),
                    'target_date': (now_jst + timedelta(days=1)).strftime('%Y-%m-%d'),
                    'games_count': len(processed_games),
                    'games': processed_games
                }
                
                # キャッシュに保存
                cache_file = CACHE_DIR / f"mlb_data_{target_date}.json"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.latest_data, f, ensure_ascii=False, indent=2)
                
                print(f"Data updated successfully: {len(processed_games)} games")
            
        except Exception as e:
            print(f"Error updating data: {e}")
    
    def process_game_for_api(self, game):
        """APIレスポンス用にゲームデータを処理"""
        # 基本情報
        away_team = game['teams']['away']['team']
        home_team = game['teams']['home']['team']
        game_date = game['gameDate']
        
        # 日本時間に変換
        game_time_utc = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        game_time_jst = game_time_utc.astimezone(jst)
        
        # 先発投手情報
        away_pitcher = None
        home_pitcher = None
        
        if 'probablePitcher' in game['teams']['away']:
            pitcher = game['teams']['away']['probablePitcher']
            away_pitcher = {
                'id': pitcher['id'],
                'name': pitcher['fullName'],
                'stats': self.get_pitcher_stats(pitcher['id'])
            }
        
        if 'probablePitcher' in game['teams']['home']:
            pitcher = game['teams']['home']['probablePitcher']
            home_pitcher = {
                'id': pitcher['id'],
                'name': pitcher['fullName'],
                'stats': self.get_pitcher_stats(pitcher['id'])
            }
        
        # チーム統計
        away_stats = self.reporter.get_team_stats(away_team['id'])
        home_stats = self.reporter.get_team_stats(home_team['id'])
        
        # 最近のOPS
        away_recent = self.reporter.get_recent_team_ops(away_team['id'])
        home_recent = self.reporter.get_recent_team_ops(home_team['id'])
        
        # 中継ぎ陣
        away_bullpen = self.reporter.get_bullpen_stats(away_team['id'])
        home_bullpen = self.reporter.get_bullpen_stats(home_team['id'])
        
        return {
            'game_id': game['gamePk'],
            'game_time_jst': game_time_jst.isoformat(),
            'game_time_formatted': game_time_jst.strftime('%m/%d %H:%M'),
            'away_team': {
                'id': away_team['id'],
                'name': away_team['name'],
                'abbreviation': away_team.get('abbreviation', ''),
                'pitcher': away_pitcher,
                'batting': away_stats,
                'recent_ops': away_recent,
                'bullpen': away_bullpen
            },
            'home_team': {
                'id': home_team['id'],
                'name': home_team['name'],
                'abbreviation': home_team.get('abbreviation', ''),
                'pitcher': home_pitcher,
                'batting': home_stats,
                'recent_ops': home_recent,
                'bullpen': home_bullpen
            }
        }
    
    def get_pitcher_stats(self, pitcher_id):
        """投手の統計を取得"""
        if not pitcher_id:
            return None
        
        try:
            stats = self.reporter.enhanced_collector.get_pitcher_enhanced_stats(pitcher_id)
            
            # GB%/FB%が0の場合は計算
            if stats['gb_percent'] == 0.0 and stats['fb_percent'] == 0.0:
                gb, fb = self.reporter.gb_fb_calculator.calculate_pitcher_gb_fb(pitcher_id, limit_games=3)
                stats['gb_percent'] = gb
                stats['fb_percent'] = fb
            
            return {
                'wins': stats['wins'],
                'losses': stats['losses'],
                'era': stats['era'],
                'fip': stats['fip'],
                'whip': stats['whip'],
                'k_bb_percent': stats['k_bb_percent'],
                'gb_percent': stats['gb_percent'],
                'fb_percent': stats['fb_percent'],
                'qs_rate': stats['qs_rate'],
                'vs_left': stats['vs_left'],
                'vs_right': stats['vs_right']
            }
        except:
            return None

# APIサーバーインスタンス
api_server = MLBDataAPIServer()

# ルート定義
@app.route('/api/mlb/games/tomorrow', methods=['GET'])
def get_tomorrow_games():
    """明日の試合データを取得"""
    return jsonify(api_server.latest_data)

@app.route('/api/mlb/games/<int:game_id>', methods=['GET'])
def get_game_detail(game_id):
    """特定の試合の詳細を取得"""
    for game in api_server.latest_data.get('games', []):
        if game['game_id'] == game_id:
            return jsonify({'success': True, 'data': game})
    
    return jsonify({'success': False, 'error': 'Game not found'}), 404

@app.route('/api/mlb/teams/<int:team_id>/stats', methods=['GET'])
def get_team_stats(team_id):
    """チームの統計を取得"""
    try:
        stats = api_server.reporter.get_team_stats(team_id)
        recent_ops = api_server.reporter.get_recent_team_ops(team_id)
        bullpen = api_server.reporter.get_bullpen_stats(team_id)
        
        return jsonify({
            'success': True,
            'data': {
                'batting': stats,
                'recent_ops': recent_ops,
                'bullpen': bullpen
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mlb/status', methods=['GET'])
def get_status():
    """APIのステータスを確認"""
    return jsonify({
        'status': 'active',
        'version': '1.0',
        'last_updated': api_server.latest_data.get('updated_at', 'Never'),
        'games_available': len(api_server.latest_data.get('games', []))
    })

# 定期更新の設定
def run_schedule():
    """スケジュールを実行"""
    schedule.every().day.at("21:00").do(api_server.update_data)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# バックグラウンドでスケジュール実行
schedule_thread = threading.Thread(target=run_schedule, daemon=True)
schedule_thread.start()

if __name__ == '__main__':
    # 開発サーバーを起動
    print("Starting Flask server...")
    print("Access the API at: http://localhost:5000/api/mlb/status")
    app.run(host='127.0.0.1', port=5000, debug=False)  # debugをFalseに変更