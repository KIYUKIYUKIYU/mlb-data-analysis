 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Team Stats - チーム統計のテスト
チーム打撃統計が正しく取得できるか確認

実行: python -m scripts.test_team_stats
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mlb_api_client import MLBApiClient
import json

def test_team_batting_stats():
    client = MLBApiClient()
    
    # テスト用にヤンキースのチームIDを使用
    team_id = 147  # Yankees
    
    print("チーム打撃統計を取得中...")
    
    # APIリクエスト
    response = client._make_request(
        f"teams/{team_id}/stats?season=2025&stats=season&group=hitting"
    )
    
    if response:
        print("\nAPIレスポンス取得成功!")
        print(json.dumps(response, indent=2)[:500])  # 最初の500文字
        
        # 統計を探す
        if 'stats' in response:
            for stat_group in response['stats']:
                print(f"\nStat Type: {stat_group.get('type', {}).get('displayName', 'Unknown')}")
                
                if stat_group.get('splits'):
                    stats = stat_group['splits'][0].get('stat', {})
                    print(f"AVG: {stats.get('avg', 'N/A')}")
                    print(f"OPS: {stats.get('ops', 'N/A')}")
                    print(f"Runs: {stats.get('runs', 'N/A')}")
                    print(f"HR: {stats.get('homeRuns', 'N/A')}")
    else:
        print("APIレスポンスなし")

if __name__ == "__main__":
    test_team_batting_stats()