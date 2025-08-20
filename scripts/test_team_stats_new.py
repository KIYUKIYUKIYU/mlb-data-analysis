#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Team Stats - チーム統計のテスト
チーム打撃統計が正しく取得できるか確認
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mlb_api_client import MLBApiClient
import json

def test_team_stats_api():
    """MLB APIから直接チーム統計を取得してテスト"""
    client = MLBApiClient()
    
    # Athletics (team_id: 133)でテスト
    team_id = 133
    print(f"=== Team ID {team_id} (Athletics) のテスト ===\n")
    
    # 1. 基本的なチーム統計
    print("1. get_team_stats()メソッドのテスト:")
    try:
        team_stats = client.get_team_stats(team_id, 2025)
        print(f"結果: {type(team_stats)}")
        if team_stats:
            print(f"AVG: {team_stats.get('avg', 'なし')}")
            print(f"OPS: {team_stats.get('ops', 'なし')}")
            print(f"Runs: {team_stats.get('runs', 'なし')}")
            print(f"Home Runs: {team_stats.get('homeRuns', 'なし')}")
        else:
            print("空の結果が返されました")
    except Exception as e:
        print(f"エラー: {e}")
    
    # 2. 直接APIを呼んでレスポンス構造を確認
    print("\n2. 直接APIコール:")
    url = f"{client.base_url}/teams/{team_id}/stats"
    params = {
        'season': 2025,
        'stats': 'season',
        'group': 'hitting'
    }
    
    try:
        response = client.session.get(url, params=params)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nレスポンス構造:")
            print(json.dumps(data, indent=2)[:1000])  # 最初の1000文字
            
            # データ構造を解析
            if 'stats' in data:
                print(f"\nstats配列の長さ: {len(data['stats'])}")
                for i, stat_group in enumerate(data['stats']):
                    print(f"\n--- Stats[{i}] ---")
                    print(f"Type: {stat_group.get('type', {}).get('displayName', 'Unknown')}")
                    
                    if 'splits' in stat_group:
                        print(f"Splits数: {len(stat_group['splits'])}")
                        if stat_group['splits']:
                            first_split = stat_group['splits'][0]
                            if 'stat' in first_split:
                                stats = first_split['stat']
                                print(f"AVG: {stats.get('avg', 'なし')}")
                                print(f"OPS: {stats.get('ops', 'なし')}")
                                print(f"Games: {stats.get('gamesPlayed', 'なし')}")
        else:
            print(f"エラーレスポンス: {response.text[:500]}")
            
    except Exception as e:
        print(f"APIコールエラー: {e}")
    
    # 3. 対左右投手成績のテスト
    print("\n\n3. get_team_splits_vs_pitchers()のテスト:")
    try:
        splits = client.get_team_splits_vs_pitchers(team_id, 2025)
        print(f"結果: {splits}")
    except Exception as e:
        print(f"エラー: {e}")
    
    # 4. 過去のOPSテスト
    print("\n4. calculate_team_recent_ops()のテスト:")
    try:
        recent_ops_5 = client.calculate_team_recent_ops(team_id, 5)
        recent_ops_10 = client.calculate_team_recent_ops(team_id, 10)
        print(f"過去5試合OPS: {recent_ops_5}")
        print(f"過去10試合OPS: {recent_ops_10}")
    except Exception as e:
        print(f"エラー: {e}")

def test_alternate_endpoints():
    """代替エンドポイントのテスト"""
    client = MLBApiClient()
    team_id = 133
    
    print("\n\n=== 代替エンドポイントのテスト ===")
    
    # 1. stats/season エンドポイント
    print("\n1. /stats エンドポイント (2024年データ):")
    url = f"{client.base_url}/teams/{team_id}/stats"
    params = {
        'season': 2024,  # 2024年で試す
        'stats': 'season',
        'group': 'hitting'
    }
    
    try:
        response = client.session.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'stats' in data and data['stats']:
                print("2024年データ取得成功!")
                stat = data['stats'][0]['splits'][0]['stat'] if data['stats'][0].get('splits') else {}
                print(f"AVG: {stat.get('avg')}, OPS: {stat.get('ops')}")
        else:
            print(f"エラー: {response.status_code}")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    test_team_stats_api()
    test_alternate_endpoints()