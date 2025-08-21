#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBの全投手情報を一括取得
"""

import json
import requests
from pathlib import Path
from datetime import datetime
import time

def fetch_all_mlb_pitchers():
    """2024-2025シーズンの全投手を取得"""
    cache_dir = Path("cache/pitcher_info")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 全チームを取得
    print("MLBの全チーム情報を取得中...")
    teams_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    teams_response = requests.get(teams_url)
    
    if teams_response.status_code != 200:
        print("チーム情報の取得に失敗")
        return
    
    teams = teams_response.json()['teams']
    print(f"チーム数: {len(teams)}")
    print("=" * 60)
    
    all_pitchers = []
    
    for i, team in enumerate(teams, 1):
        team_id = team['id']
        team_name = team['name']
        print(f"\n[{i}/{len(teams)}] {team_name}")
        print("-" * 40)
        
        # チームのロースターを取得
        roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active"
        
        try:
            roster_response = requests.get(roster_url)
            
            if roster_response.status_code == 200:
                roster = roster_response.json().get('roster', [])
                team_pitchers = []
                
                for player in roster:
                    # 投手のみ
                    if player['position']['abbreviation'] in ['P', 'SP', 'RP', 'CP']:
                        player_id = player['person']['id']
                        player_name = player['person']['fullName']
                        
                        # キャッシュチェック
                        cache_file = cache_dir / f"{player_id}.json"
                        if cache_file.exists():
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                cache_data = json.load(f)
                                hand = cache_data.get('hand', 'R')
                                hand_text = "左" if hand == 'L' else "右"
                                print(f"  ✓ {player_name} ({hand_text}) - キャッシュ済み")
                                all_pitchers.append(cache_data)
                                team_pitchers.append(cache_data)
                                continue
                        
                        # 詳細情報を取得
                        detail_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
                        detail_response = requests.get(detail_url)
                        
                        if detail_response.status_code == 200:
                            player_data = detail_response.json()['people'][0]
                            pitch_hand = player_data.get('pitchHand', {}).get('code', 'R')
                            
                            cache_data = {
                                'pitcher_id': player_id,
                                'name': player_data['fullName'],
                                'team': team_name,
                                'team_id': team_id,
                                'hand': pitch_hand,
                                'position': player['position']['abbreviation'],
                                'updated': datetime.now().isoformat()
                            }
                            
                            # キャッシュ保存
                            with open(cache_file, 'w', encoding='utf-8') as f:
                                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                            
                            all_pitchers.append(cache_data)
                            team_pitchers.append(cache_data)
                            hand_text = "左" if pitch_hand == 'L' else "右"
                            print(f"  + {player_name} ({hand_text}) - 新規取得")
                            
                            # API制限対策
                            time.sleep(0.1)
                
                # チーム統計
                team_left = sum(1 for p in team_pitchers if p['hand'] == 'L')
                team_right = sum(1 for p in team_pitchers if p['hand'] == 'R')
                print(f"  小計: 投手{len(team_pitchers)}人 (左{team_left}, 右{team_right})")
                
        except Exception as e:
            print(f"  エラー: {e}")
            continue
    
    # 全体統計
    print(f"\n" + "=" * 60)
    print(f"【最終結果】")
    print(f"合計: {len(all_pitchers)}人の投手情報を取得")
    
    left_count = sum(1 for p in all_pitchers if p['hand'] == 'L')
    right_count = sum(1 for p in all_pitchers if p['hand'] == 'R')
    
    print(f"左投げ: {left_count}人 ({left_count*100/len(all_pitchers):.1f}%)")
    print(f"右投げ: {right_count}人 ({right_count*100/len(all_pitchers):.1f}%)")
    
    # マスターファイルも保存
    master_file = cache_dir / "all_pitchers.json"
    with open(master_file, 'w', encoding='utf-8') as f:
        json.dump(all_pitchers, f, ensure_ascii=False, indent=2)
    
    print(f"\nマスターファイル保存: {master_file}")
    print(f"個別キャッシュ: {cache_dir}/*.json")
    
    # チーム別左投手ランキング
    print(f"\n" + "=" * 60)
    print("【チーム別左投手数ランキング】")
    
    team_stats = {}
    for p in all_pitchers:
        team = p['team']
        if team not in team_stats:
            team_stats[team] = {'left': 0, 'right': 0}
        if p['hand'] == 'L':
            team_stats[team]['left'] += 1
        else:
            team_stats[team]['right'] += 1
    
    sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['left'], reverse=True)
    for i, (team, stats) in enumerate(sorted_teams[:10], 1):
        total = stats['left'] + stats['right']
        print(f"{i:2}. {team:25} 左{stats['left']:2}人 (全{total}人中)")

if __name__ == "__main__":
    print("MLB全投手情報取得スクリプト")
    print("=" * 60)
    print("約400人の投手情報を取得します。")
    print("所要時間: 約5-10分")
    print()
    
    fetch_all_mlb_pitchers()