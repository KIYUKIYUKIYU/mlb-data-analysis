 
import requests
import json
from datetime import datetime, timedelta

print("=== Baseball Savant API 確認 ===\n")

# Baseball Savant の可能なエンドポイントをテスト
endpoints = [
    # Statcast Search API
    "https://baseballsavant.mlb.com/statcast_search",
    "https://baseballsavant.mlb.com/statcast_search/csv",
    
    # Team Statistics
    "https://baseballsavant.mlb.com/league",
    "https://baseballsavant.mlb.com/statcast_leaderboard",
    
    # Expected Stats
    "https://baseballsavant.mlb.com/expected_statistics",
    "https://baseballsavant.mlb.com/team"
]

print("1. エンドポイントの可用性チェック:")
for endpoint in endpoints:
    try:
        response = requests.get(endpoint, timeout=5)
        print(f"  {endpoint}: Status {response.status_code}")
    except Exception as e:
        print(f"  {endpoint}: Error - {str(e)[:50]}")

# Statcast Search APIのテスト（2025年のデータ）
print("\n2. Statcast Search API テスト (2025年):")

# 最近7日間のデータを取得
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

params = {
    'all': 'true',
    'hfPT': '',
    'hfAB': '',
    'hfBBT': '',
    'hfPR': '',
    'hfZ': '',
    'stadium': '',
    'hfBBL': '',
    'hfNewZones': '',
    'hfGT': 'R|',
    'hfC': '',
    'hfSea': '2025|',
    'hfSit': '',
    'player_type': 'batter',
    'hfOuts': '',
    'opponent': '',
    'pitcher_throws': '',
    'batter_stands': '',
    'hfSA': '',
    'game_date_gt': start_date,
    'game_date_lt': end_date,
    'hfInfield': '',
    'team': 'NYY',  # Yankees
    'position': '',
    'hfOutfield': '',
    'hfRO': '',
    'home_road': '',
    'hfFlag': '',
    'hfPull': '',
    'metric_1': '',
    'hfInn': '',
    'min_pitches': '0',
    'min_results': '0',
    'group_by': 'team',
    'sort_col': 'pitches',
    'player_event_sort': 'h_launch_speed',
    'sort_order': 'desc',
    'min_pas': '0',
    'type': 'details'
}

try:
    url = "https://baseballsavant.mlb.com/statcast_search"
    response = requests.get(url, params=params, timeout=10)
    print(f"  Status: {response.status_code}")
    print(f"  Response length: {len(response.text)} characters")
    
    # HTMLレスポンスの一部を確認
    if response.status_code == 200:
        if 'barrel' in response.text.lower():
            print("  'barrel' found in response!")
        if 'hard_hit' in response.text.lower() or 'hard-hit' in response.text.lower():
            print("  'hard hit' found in response!")
            
except Exception as e:
    print(f"  Error: {str(e)}")

# CSV形式での取得を試みる
print("\n3. CSV形式でのデータ取得テスト:")
csv_url = "https://baseballsavant.mlb.com/statcast_search/csv"

csv_params = {
    'all': 'true',
    'type': 'details',
    'player_type': 'batter',
    'hfSea': '2025|',
    'hfGT': 'R|',
    'group_by': 'team-year',
    'min_results': '100',
    'game_date_gt': '2025-06-01',
    'game_date_lt': '2025-06-26'
}

try:
    response = requests.get(csv_url, params=csv_params, timeout=10)
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        # CSVの最初の数行を表示
        lines = response.text.split('\n')[:5]
        print("  CSV Headers:")
        for i, line in enumerate(lines):
            if i == 0:  # ヘッダー行
                headers = line.split(',')
                # Barrel関連のカラムを探す
                barrel_cols = [h for h in headers if 'barrel' in h.lower() or 'hard' in h.lower()]
                if barrel_cols:
                    print(f"    Found columns: {barrel_cols}")
                else:
                    print(f"    First few columns: {headers[:10]}")
            else:
                print(f"    Row {i}: {line[:100]}...")
                
except Exception as e:
    print(f"  Error: {str(e)}")

# pybaseballライブラリの使用可能性を確認
print("\n4. pybaseballライブラリの確認:")
try:
    import pybaseball
    print("  pybaseball is installed!")
    print(f"  Version: {pybaseball.__version__ if hasattr(pybaseball, '__version__') else 'Unknown'}")
    
    # チームの統計を取得してみる
    print("\n  Trying to get team stats...")
    # pybaseballのstatcast関数をテスト
    from pybaseball import statcast
    
    # 1日分のデータだけ取得してテスト
    test_date = '2025-06-25'
    df = statcast(start_dt=test_date, end_dt=test_date)
    
    if not df.empty:
        print(f"    Retrieved {len(df)} records")
        print(f"    Columns: {df.columns.tolist()[:10]}...")
        
        # Barrel関連のカラムを確認
        barrel_cols = [col for col in df.columns if 'barrel' in col.lower()]
        if barrel_cols:
            print(f"    Barrel columns: {barrel_cols}")
            
except ImportError:
    print("  pybaseball is NOT installed")
    print("  Install with: pip install pybaseball")
except Exception as e:
    print(f"  Error testing pybaseball: {str(e)}")