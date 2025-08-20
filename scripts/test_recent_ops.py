 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Recent OPS - 過去N試合OPS計算のテスト

実行: python -m scripts.test_recent_ops
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mlb_api_client import MLBApiClient
from datetime import datetime, timedelta

def get_team_recent_ops(team_id, games_count):
    """チームの最近N試合のOPSを計算"""
    client = MLBApiClient()
    
    print(f"チーム {team_id} の過去 {games_count} 試合OPSを計算中...\n")
    
    try:
        # 過去30日間の全試合を取得
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"期間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        schedule = client._make_request(
            f"schedule?sportId=1&startDate={start_date.strftime('%Y-%m-%d')}&endDate={end_date.strftime('%Y-%m-%d')}"
        )
        
        if not schedule or not schedule.get('dates'):
            print("スケジュール取得失敗")
            return 'N/A'
            
        # 終了した試合を新しい順に取得
        completed_games = []
        for date in reversed(schedule.get('dates', [])):
            for game in date.get('games', []):
                # 指定チームが関わる試合か確認
                if (game['teams']['away']['team']['id'] == team_id or 
                    game['teams']['home']['team']['id'] == team_id):
                    
                    if game['status']['abstractGameState'] == 'Final':
                        completed_games.append({
                            'gamePk': game['gamePk'],
                            'date': game['gameDate'][:10],
                            'is_home': game['teams']['home']['team']['id'] == team_id
                        })
                        
                    if len(completed_games) >= games_count:
                        break
                        
            if len(completed_games) >= games_count:
                break
                
        print(f"\n見つかった試合数: {len(completed_games)}")
        
        if not completed_games:
            print("終了した試合が見つかりません")
            return 'N/A'
            
        # 各試合のチーム打撃成績を集計
        total_ab = 0
        total_h = 0
        total_bb = 0
        total_hbp = 0
        total_sf = 0
        total_2b = 0
        total_3b = 0
        total_hr = 0
        
        for i, game_info in enumerate(completed_games[:games_count]):
            print(f"\n試合 {i+1}: {game_info['date']} (Game ID: {game_info['gamePk']})")
            
            boxscore = client._make_request(f"game/{game_info['gamePk']}/boxscore")
            
            if boxscore and 'teams' in boxscore:
                # 自チームのデータを取得
                side = 'home' if game_info['is_home'] else 'away'
                team_data = boxscore['teams'][side]
                
                if 'teamStats' in team_data and 'batting' in team_data['teamStats']:
                    batting = team_data['teamStats']['batting']
                    
                    ab = batting.get('atBats', 0)
                    h = batting.get('hits', 0)
                    bb = batting.get('baseOnBalls', 0)
                    hbp = batting.get('hitByPitch', 0)
                    sf = batting.get('sacFlies', 0)
                    doubles = batting.get('doubles', 0)
                    triples = batting.get('triples', 0)
                    hr = batting.get('homeRuns', 0)
                    
                    print(f"  AB: {ab}, H: {h}, 2B: {doubles}, 3B: {triples}, HR: {hr}")
                    print(f"  BB: {bb}, HBP: {hbp}, SF: {sf}")
                    
                    total_ab += ab
                    total_h += h
                    total_bb += bb
                    total_hbp += hbp
                    total_sf += sf
                    total_2b += doubles
                    total_3b += triples
                    total_hr += hr
                else:
                    print("  teamStats.batting が見つかりません")
                    
        # OPS計算
        print(f"\n合計統計:")
        print(f"AB: {total_ab}, H: {total_h}, 2B: {total_2b}, 3B: {total_3b}, HR: {total_hr}")
        print(f"BB: {total_bb}, HBP: {total_hbp}, SF: {total_sf}")
        
        if total_ab > 0:
            # 単打数 = 安打 - (二塁打 + 三塁打 + 本塁打)
            singles = total_h - (total_2b + total_3b + total_hr)
            # 塁打数
            total_bases = singles + (2 * total_2b) + (3 * total_3b) + (4 * total_hr)
            
            # 打席数
            pa = total_ab + total_bb + total_hbp + total_sf
            
            if pa > 0:
                obp = (total_h + total_bb + total_hbp) / pa
                slg = total_bases / total_ab
                ops = obp + slg
                
                print(f"\nOBP: {obp:.3f}")
                print(f"SLG: {slg:.3f}")
                print(f"OPS: {ops:.3f}")
                
                return f"{ops:.3f}"
                
        return 'N/A'
            
    except Exception as e:
        print(f"エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return 'N/A'

if __name__ == "__main__":
    # ヤンキースでテスト
    team_id = 147
    
    # 過去5試合
    print("="*50)
    ops_5 = get_team_recent_ops(team_id, 5)
    print(f"\n過去5試合OPS: {ops_5}")
    
    print("\n" + "="*50)
    
    # 過去10試合
    ops_10 = get_team_recent_ops(team_id, 10)
    print(f"\n過去10試合OPS: {ops_10}")