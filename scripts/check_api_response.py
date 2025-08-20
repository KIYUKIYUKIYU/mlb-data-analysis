"""
MLB APIレスポンス確認スクリプト
どんなデータが取得できるか詳細に確認
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime

def check_player_stats_endpoints():
    """選手統計の各エンドポイントを確認"""
    
    base_url = "https://statsapi.mlb.com/api/v1"
    
    # Zac Gallen (ID: 668678)を例に使用
    player_id = 668678
    season = 2025
    
    print("=== MLB API レスポンス確認 ===")
    print(f"選手ID: {player_id} (Zac Gallen)")
    print(f"シーズン: {season}")
    print("=" * 50)
    
    # 1. 基本的なシーズン統計
    print("\n【1. 基本シーズン統計】")
    print("エンドポイント: /people/{id}/stats?stats=season&season={year}")
    url = f"{base_url}/people/{player_id}/stats"
    params = {
        'stats': 'season',
        'season': season,
        'group': 'pitching'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print_available_fields(data)
    else:
        print(f"エラー: {response.status_code}")
    
    # 2. 詳細統計（Advanced）
    print("\n【2. 詳細統計】")
    print("エンドポイント: /people/{id}/stats?stats=advanced&season={year}")
    params['stats'] = 'advanced'
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print_available_fields(data)
    
    # 3. Sabermetrics統計
    print("\n【3. Sabermetrics統計】")
    print("エンドポイント: /people/{id}/stats?stats=sabermetrics&season={year}")
    params['stats'] = 'sabermetrics'
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print_available_fields(data)
    
    # 4. StatCast統計
    print("\n【4. StatCast統計】")
    print("エンドポイント: /people/{id}/stats?stats=statcast&season={year}")
    params['stats'] = 'statcast'
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print_available_fields(data)
    
    # 5. 利用可能な全統計タイプを確認
    print("\n【5. 利用可能な統計タイプ一覧】")
    meta_url = f"{base_url}/statTypes"
    response = requests.get(meta_url)
    if response.status_code == 200:
        stat_types = response.json()
        print("\n投手用統計タイプ:")
        for st in stat_types[:20]:  # 最初の20個
            if 'pitching' in st.get('name', '').lower() or st.get('isCounting') == False:
                print(f"- {st.get('name')}: {st.get('description', '')}")

def print_available_fields(data):
    """APIレスポンスから利用可能なフィールドを表示"""
    if 'stats' in data:
        for stat_group in data['stats']:
            print(f"\nグループ: {stat_group.get('group', {}).get('displayName', 'Unknown')}")
            
            if 'splits' in stat_group and stat_group['splits']:
                split = stat_group['splits'][0]
                if 'stat' in split:
                    stats = split['stat']
                    print(f"利用可能なフィールド数: {len(stats)}")
                    print("\nフィールド一覧:")
                    
                    # フィールドを分類して表示
                    basic_stats = {}
                    rate_stats = {}
                    advanced_stats = {}
                    
                    for key, value in stats.items():
                        if key in ['era', 'wins', 'losses', 'games', 'gamesStarted', 'saves']:
                            basic_stats[key] = value
                        elif 'percentage' in key.lower() or 'rate' in key.lower():
                            rate_stats[key] = value
                        else:
                            advanced_stats[key] = value
                    
                    if basic_stats:
                        print("\n[基本統計]")
                        for k, v in sorted(basic_stats.items()):
                            print(f"  {k}: {v}")
                    
                    if rate_stats:
                        print("\n[レート統計]")
                        for k, v in sorted(rate_stats.items()):
                            print(f"  {k}: {v}")
                    
                    if advanced_stats:
                        print("\n[その他の統計]")
                        for k, v in sorted(advanced_stats.items()):
                            print(f"  {k}: {v}")

def check_specific_fields():
    """特定のフィールドを詳しく確認"""
    print("\n\n=== 特定フィールドの確認 ===")
    
    base_url = "https://statsapi.mlb.com/api/v1"
    player_id = 668678  # Zac Gallen
    
    # いくつかの統計タイプを試す
    stat_types = [
        'season',
        'career', 
        'statsSingleSeason',
        'pitchingStatsByType',
        'sabermetrics',
        'expectedStatistics'
    ]
    
    for stat_type in stat_types:
        print(f"\n--- {stat_type} ---")
        url = f"{base_url}/people/{player_id}/stats"
        params = {
            'stats': stat_type,
            'season': 2025,
            'group': 'pitching'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            # GB%, FB%に関連しそうなフィールドを探す
            if 'stats' in data and data['stats']:
                for stat_group in data['stats']:
                    if 'splits' in stat_group and stat_group['splits']:
                        stats = stat_group['splits'][0].get('stat', {})
                        
                        # 打球関連のフィールドを探す
                        for key in stats.keys():
                            if any(term in key.lower() for term in ['ground', 'fly', 'ball', 'batted', 'contact']):
                                print(f"  発見: {key} = {stats[key]}")

if __name__ == "__main__":
    # メイン実行
    check_player_stats_endpoints()
    
    # 追加の詳細確認
    check_specific_fields()
    
    print("\n\n完了！")