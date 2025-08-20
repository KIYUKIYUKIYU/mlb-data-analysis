import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.enhanced_stats_collector import EnhancedStatsCollector
import requests

def find_active_pitchers():
    """6月22日の試合から投手IDを取得"""
    url = "https://statsapi.mlb.com/api/v1/schedule?date=2025-06-22&sportId=1&hydrate=probablePitcher"
    response = requests.get(url)
    data = response.json()
    
    pitchers = []
    if 'dates' in data and data['dates']:
        for game in data['dates'][0]['games'][:3]:  # 最初の3試合
            # Away pitcher
            if 'probablePitcher' in game['teams']['away']:
                pitcher = game['teams']['away']['probablePitcher']
                pitchers.append({
                    'id': pitcher['id'],
                    'name': pitcher['fullName'],
                    'team': game['teams']['away']['team']['name']
                })
            
            # Home pitcher  
            if 'probablePitcher' in game['teams']['home']:
                pitcher = game['teams']['home']['probablePitcher']
                pitchers.append({
                    'id': pitcher['id'],
                    'name': pitcher['fullName'],
                    'team': game['teams']['home']['team']['name']
                })
    
    return pitchers

def test_pitcher_stats():
    """投手統計のテスト"""
    collector = EnhancedStatsCollector()
    
    print("=== 拡張統計テスト ===\n")
    
    # アクティブな投手を検索
    pitchers = find_active_pitchers()
    
    if not pitchers:
        print("投手が見つかりません")
        return
    
    # 最初の2人の投手をテスト
    for pitcher_info in pitchers[:2]:
        print(f"\n投手: {pitcher_info['name']} ({pitcher_info['team']})")
        print(f"ID: {pitcher_info['id']}")
        print("-" * 60)
        
        # 拡張統計を取得
        stats = collector.get_pitcher_enhanced_stats(pitcher_info['id'])
        
        # 基本統計
        print(f"成績: {stats['wins']}勝{stats['losses']}敗")
        print(f"ERA: {stats['era']:.2f} | FIP: {stats['fip']:.2f} | WHIP: {stats['whip']:.2f}")
        print(f"K%: {stats['k_percent']}% | BB%: {stats['bb_percent']}% | K-BB%: {stats['k_bb_percent']}%")
        print(f"GB%: {stats['gb_percent']}% | FB%: {stats['fb_percent']}%")
        
        # 対左右成績
        print(f"\n対左打者: {stats['vs_left']['avg']} (OPS {stats['vs_left']['ops']})")
        print(f"対右打者: {stats['vs_right']['avg']} (OPS {stats['vs_right']['ops']})")
        
        print("=" * 60)

def test_team_stats():
    """チーム統計のテスト"""
    collector = EnhancedStatsCollector()
    
    print("\n\n=== チーム対左右投手成績テスト ===\n")
    
    # Yankees (ID: 147) でテスト
    team_id = 147
    team_name = "New York Yankees"
    
    print(f"チーム: {team_name}")
    print("-" * 60)
    
    # 対左右投手成績を取得
    vs_stats = collector.get_team_vs_pitching_stats(team_id)
    
    print(f"対左投手: {vs_stats['vs_lhp']['avg']} (OPS {vs_stats['vs_lhp']['ops']})")
    print(f"対右投手: {vs_stats['vs_rhp']['avg']} (OPS {vs_stats['vs_rhp']['ops']})")

if __name__ == "__main__":
    test_pitcher_stats()
    test_team_stats()