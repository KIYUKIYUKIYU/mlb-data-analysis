"""
MLB APIの全エンドポイントを詳細確認
GB%/FB%/SwStr%/BABIPが本当にないか確認
"""
import requests
import json

def check_all_pitcher_endpoints():
    """投手関連の全エンドポイントを確認"""
    
    base_url = "https://statsapi.mlb.com/api/v1"
    player_id = 668678  # Zac Gallen
    season = 2025
    
    print("=== MLB API 完全チェック ===\n")
    
    # 利用可能な全ての統計タイプ
    stat_types = [
        'season',
        'seasonAdvanced', 
        'career',
        'careerAdvanced',
        'statsSingleSeason',
        'expectedStatistics',
        'sabermetrics',
        'statcast',
        'pitchingStatsByType',
        'playLog',
        'lastXGames',
        'byDateRange',
        'byDayOfWeek',
        'byMonth',
        'gameLog',
        'winLoss',
        'vsPlayer',
        'vsTeam',
        'homeAndAway',
        'byInning',
        'pitchArsenal',
        'pitchValues',
        'hotColdZones'
    ]
    
    found_fields = set()
    
    for stat_type in stat_types:
        print(f"\n--- {stat_type} ---")
        url = f"{base_url}/people/{player_id}/stats"
        params = {
            'stats': stat_type,
            'season': season,
            'group': 'pitching'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                if 'stats' in data and data['stats']:
                    for stat_group in data['stats']:
                        if 'splits' in stat_group and stat_group['splits']:
                            for split in stat_group['splits']:
                                if 'stat' in split:
                                    stats = split['stat']
                                    
                                    # 探しているフィールドをチェック
                                    for key, value in stats.items():
                                        # 新しいフィールドを記録
                                        if key not in found_fields:
                                            found_fields.add(key)
                                            
                                            # 特に興味のあるフィールド
                                            if any(term in key.lower() for term in 
                                                  ['ground', 'fly', 'line', 'popup', 'ball', 'swing', 
                                                   'miss', 'whiff', 'contact', 'babip', 'batted']):
                                                print(f"  ★ {key}: {value}")
                                
                print(f"  取得成功 - {len(found_fields)}個のフィールド")
            else:
                print(f"  エラー: {response.status_code}")
                
        except Exception as e:
            print(f"  例外: {e}")
    
    # 見つかったフィールドの要約
    print("\n\n=== 発見されたフィールド ===")
    print(f"合計: {len(found_fields)}個")
    
    # 打球関連
    batted_ball_fields = [f for f in found_fields if any(term in f.lower() for term in ['ground', 'fly', 'line', 'popup'])]
    if batted_ball_fields:
        print("\n打球関連フィールド:")
        for field in sorted(batted_ball_fields):
            print(f"  - {field}")
    
    # スイング関連
    swing_fields = [f for f in found_fields if any(term in f.lower() for term in ['swing', 'miss', 'whiff', 'contact'])]
    if swing_fields:
        print("\nスイング関連フィールド:")
        for field in sorted(swing_fields):
            print(f"  - {field}")
    
    # BABIP
    if 'babip' in found_fields:
        print("\n★ BABIPは存在します！")


def check_statcast_search_api():
    """Baseball Savant の Statcast Search API を試す"""
    print("\n\n=== Baseball Savant Statcast Search API ===")
    
    # Statcast Search API（非公式）
    url = "https://baseballsavant.mlb.com/statcast_search/csv"
    
    # パラメータ例（最小限）
    params = {
        'all': 'true',
        'type': 'details',
        'player_id': 668678,  # Zac Gallen
        'player_type': 'pitcher',
        'season': 2025,
        'game_date_gt': '2025-03-20',
        'game_date_lt': '2025-06-26'
    }
    
    print("リクエストURL:", url)
    print("パラメータ:", params)
    
    try:
        # 注意: このAPIは非公式で、レート制限が厳しい
        response = requests.get(url, params=params, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            # CSVデータの最初の数行を確認
            lines = response.text.split('\n')[:5]
            for i, line in enumerate(lines):
                if i == 0:
                    # ヘッダー行
                    headers = line.split(',')
                    print(f"\nカラム数: {len(headers)}")
                    
                    # 重要なカラムを探す
                    important_cols = ['launch_angle', 'launch_speed', 'description', 
                                    'bb_type', 'events', 'pitch_type']
                    found_cols = [h for h in headers if h in important_cols]
                    print(f"発見した重要カラム: {found_cols}")
                else:
                    print(f"データ行{i}: {line[:100]}...")
        else:
            print(f"エラーレスポンス: {response.text[:200]}")
            
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    # MLB API の完全チェック
    check_all_pitcher_endpoints()
    
    # Statcast Search API のテスト
    check_statcast_search_api()