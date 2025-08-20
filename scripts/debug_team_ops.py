 #!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug Team OPS - チームの過去試合OPSをデバッグ

実行: python -m scripts.debug_team_ops
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mlb_api_client import MLBApiClient
from datetime import datetime, timedelta
import json

def debug_team_recent_ops():
    client = MLBApiClient()
    
    # ヤンキース（team_id: 147）でテスト
    team_id = 147
    season = 2025
    games_count = 5
    
    print(f"チーム {team_id} の過去 {games_count} 試合を取得中...\n")
    
    # Step 1: 別の方法でスケジュール取得
    print("Step 1: スケジュール取得（一般的なschedule API）")
    
    # 過去30日間の全試合を取得
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    schedule_url = f"schedule?sportId=1&startDate={start_date.strftime('%Y-%m-%d')}&endDate={end_date.strftime('%Y-%m-%d')}"
    print(f"URL: {schedule_url}")
    
    schedule = client._make_request(schedule_url)
    
    if not schedule:
        print("スケジュール取得失敗")
        return
        
    print(f"スケジュール取得成功: {len(schedule.get('dates', []))} 日分のデータ")
    
    # Step 2: ヤンキースの試合を探す
    print(f"\nStep 2: チームID {team_id} の終了した試合を探す")
    completed_games = []
    
    for date in reversed(schedule.get('dates', [])):
        for game in date.get('games', []):
            # ヤンキースが関わる試合か確認
            if (game['teams']['away']['team']['id'] == team_id or 
                game['teams']['home']['team']['id'] == team_id):
                
                if game['status']['abstractGameState'] == 'Final':
                    game_info = {
                        'gamePk': game['gamePk'],
                        'date': game['gameDate'],
                        'away': game['teams']['away']['team']['name'],
                        'home': game['teams']['home']['team']['name'],
                        'is_home': game['teams']['home']['team']['id'] == team_id
                    }
                    completed_games.append(game_info)
                    print(f"  試合 {len(completed_games)}: {game_info['date'][:10]} {game_info['away']} @ {game_info['home']}")
                
                if len(completed_games) >= games_count:
                    break
                
        if len(completed_games) >= games_count:
            break
            
    print(f"\n見つかった試合数: {len(completed_games)}")
    
    if not completed_games:
        print("終了した試合が見つかりません")
        return
        
    # Step 3: 最初の試合のBoxscoreを詳しく確認
    print("\nStep 3: 最初の試合のBoxscoreを確認")
    first_game = completed_games[0]
    print(f"試合ID: {first_game['gamePk']}")
    print(f"ホーム/アウェイ: {'Home' if first_game['is_home'] else 'Away'}")
    
    boxscore = client._make_request(f"game/{first_game['gamePk']}/boxscore")
    
    if not boxscore:
        print("Boxscore取得失敗")
        return
        
    print("Boxscore取得成功")
    
    # チームのデータを確認
    side = 'home' if first_game['is_home'] else 'away'
    team_data = boxscore['teams'][side]
    
    print(f"\nチームデータ構造:")
    print(f"Available keys: {list(team_data.keys())[:10]}...")  # 最初の10個のキー
    
    # teamStatsを探す
    if 'teamStats' in team_data:
        print("\nteamStats found!")
        team_stats = team_data['teamStats']
        print(f"teamStats keys: {list(team_stats.keys())}")
        
        if 'batting' in team_stats:
            print("\nbatting stats found!")
            batting = team_stats['batting']
            print(f"  打数: {batting.get('atBats', 'N/A')}")
            print(f"  安打: {batting.get('hits', 'N/A')}")
            print(f"  四球: {batting.get('baseOnBalls', 'N/A')}")
            print(f"  本塁打: {batting.get('homeRuns', 'N/A')}")
            print(f"  二塁打: {batting.get('doubles', 'N/A')}")
            print(f"  三塁打: {batting.get('triples', 'N/A')}")
            
            # OPS計算のテスト
            ab = batting.get('atBats', 0)
            h = batting.get('hits', 0)
            bb = batting.get('baseOnBalls', 0)
            hbp = batting.get('hitByPitch', 0)
            sf = batting.get('sacFlies', 0)
            
            print(f"\nOPS計算用データ:")
            print(f"  AB: {ab}, H: {h}, BB: {bb}, HBP: {hbp}, SF: {sf}")
            
            if ab > 0:
                pa = ab + bb + hbp + sf
                obp = (h + bb + hbp) / pa if pa > 0 else 0
                print(f"  OBP: {obp:.3f}")
    else:
        print("\nteamStats NOT found - 別の場所を探す")
        
        # stats配列を確認
        if 'stats' in team_data:
            print("\nstats array found!")
            print(f"stats length: {len(team_data['stats'])}")
            
            if team_data['stats'] and 'batting' in team_data['stats']:
                batting = team_data['stats']['batting']
                print("batting in stats!")
                print(f"  打数: {batting.get('atBats', 'N/A')}")
                
    # Step 4: 別の方法 - players の統計を合計
    print("\nStep 4: 選手個人の統計から合計を計算")
    if 'players' in team_data:
        total_ab = 0
        total_h = 0
        
        for player_id, player_data in team_data['players'].items():
            if 'stats' in player_data and 'batting' in player_data['stats']:
                batting = player_data['stats']['batting']
                total_ab += batting.get('atBats', 0)
                total_h += batting.get('hits', 0)
                
        print(f"選手合計 - AB: {total_ab}, H: {total_h}")

if __name__ == "__main__":
    debug_team_recent_ops()
