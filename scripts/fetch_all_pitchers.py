#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
レポートからすべての投手情報を取得してキャッシュ
"""

import sys
import json
import re
import requests
from pathlib import Path
from datetime import datetime

def get_pitcher_names_from_report(report_path):
    """レポートから投手名を抽出"""
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # パターンマッチング
    pattern = r'\*\*先発\*\*[:：]\s*(.+?)\s*\((\d+勝\d+敗)\)'
    matches = re.findall(pattern, content)
    
    pitcher_names = []
    for match in matches:
        name = match[0].strip()
        if name and name != '未定':
            pitcher_names.append(name)
    
    return pitcher_names

def fetch_pitcher_from_mlb_api(pitcher_name):
    """MLB APIから投手情報を取得"""
    cache_dir = Path("cache/pitcher_info")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"検索中: {pitcher_name}")
    
    # 既存のキャッシュをチェック
    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 名前の完全一致または部分一致
                cached_name = data.get('name', '')
                if pitcher_name.lower() == cached_name.lower() or pitcher_name.lower() in cached_name.lower():
                    print(f"  📂 キャッシュ済み: {cached_name} ({data['hand']}投げ)")
                    return data['hand']
        except:
            pass
    
    # MLB APIで検索
    try:
        # URLエンコード
        search_name = pitcher_name.replace(' ', '%20')
        url = f"https://statsapi.mlb.com/api/v1/people/search?names={search_name}&sportId=1&active=true"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'people' in data and len(data['people']) > 0:
                # 投手を探す
                for person in data['people']:
                    person_name = person.get('fullName', '')
                    position = person.get('primaryPosition', {}).get('abbreviation', '')
                    
                    # 投手で名前が一致
                    if position in ['P', 'SP', 'RP']:
                        # 名前のマッチング（部分一致も許可）
                        if pitcher_name.lower() in person_name.lower() or person_name.lower() in pitcher_name.lower():
                            player_id = person['id']
                            
                            # 詳細情報を取得
                            detail_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
                            detail_response = requests.get(detail_url)
                            
                            if detail_response.status_code == 200:
                                player_data = detail_response.json()['people'][0]
                                
                                # 利き腕情報
                                pitch_hand = player_data.get('pitchHand', {}).get('code', 'R')
                                
                                # キャッシュデータ
                                cache_data = {
                                    'pitcher_id': player_id,
                                    'name': player_data['fullName'],
                                    'hand': pitch_hand,
                                    'updated': datetime.now().isoformat()
                                }
                                
                                # キャッシュファイルに保存
                                cache_file = cache_dir / f"{player_id}.json"
                                with open(cache_file, 'w', encoding='utf-8') as f:
                                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                                
                                print(f"  ✅ {player_data['fullName']}: {pitch_hand}投げ -> 保存済み")
                                return pitch_hand
                
                print(f"  ⚠️ {pitcher_name}: 投手として見つからず")
            else:
                print(f"  ⚠️ {pitcher_name}: 検索結果なし")
                
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    return 'R'  # デフォルト

def main():
    """メイン処理"""
    # 8月22日のレポートを使用
    report_path = Path("daily_reports/MLB08月22日(金)レポート.txt")
    
    if not report_path.exists():
        print(f"ファイルが見つかりません: {report_path}")
        return
    
    print(f"レポート: {report_path}")
    
    # 投手名を抽出
    pitcher_names = get_pitcher_names_from_report(report_path)
    print(f"見つかった投手: {len(pitcher_names)}人")
    print("-" * 50)
    
    # 各投手の情報を取得
    results = {}
    for name in pitcher_names:
        hand = fetch_pitcher_from_mlb_api(name)
        results[name] = hand
    
    # 結果表示
    print("\n" + "=" * 50)
    print("最終結果:")
    print("-" * 50)
    
    left_count = 0
    right_count = 0
    
    for name, hand in results.items():
        hand_text = "左投げ" if hand == 'L' else "右投げ"
        print(f"{name:20} : {hand_text}")
        if hand == 'L':
            left_count += 1
        else:
            right_count += 1
    
    print("-" * 50)
    print(f"合計: 左投げ {left_count}人, 右投げ {right_count}人")

if __name__ == "__main__":
    main()