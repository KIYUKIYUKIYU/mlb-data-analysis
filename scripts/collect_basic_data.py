"""
MLB基本データ収集スクリプト
チーム、選手、統計情報を取得してJSON形式で保存
"""
import json
import os
from datetime import datetime
from src.mlb_api_client import MLBApiClient
import time


class DataCollector:
    def __init__(self):
        self.client = MLBApiClient()
        self.base_path = "data/raw"
        
    def save_json(self, data, filepath):
        """JSONファイルとして保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 保存完了: {filepath}")
        
    def collect_teams(self, season=2025):
        """チーム情報を収集"""
        print(f"\n🏟️  {season}年のチーム情報を収集中...")
        
        # APIからデータ取得
        teams_data = self.client.get_teams(season)
        teams_list = teams_data['teams']
        
        # 保存先パス
        filepath = os.path.join(self.base_path, "teams", f"teams_{season}.json")
        
        # データ整形
        formatted_teams = []
        for team in teams_list:
            formatted_team = {
                "id": team['id'],
                "name": team['name'],
                "abbreviation": team['abbreviation'],
                "teamName": team['teamName'],
                "locationName": team['locationName'],
                "league": team['league']['name'],
                "division": team['division']['name'],
                "venue": team['venue']['name'],
                "firstYearOfPlay": team['firstYearOfPlay']
            }
            formatted_teams.append(formatted_team)
            
        # 保存
        save_data = {
            "season": season,
            "collected_at": datetime.now().isoformat(),
            "total_teams": len(formatted_teams),
            "teams": formatted_teams
        }
        
        self.save_json(save_data, filepath)
        print(f"📊 {len(formatted_teams)}チームの情報を取得しました")
        
        return formatted_teams
        
    def collect_team_roster(self, team_id, team_name, season=2025):
        """特定チームのロースター（選手一覧）を取得"""
        print(f"\n👥 {team_name}のロースターを取得中...")
        
        try:
            # APIエンドポイント
            endpoint = f"teams/{team_id}/roster?season={season}"
            roster_data = self.client._make_request(endpoint)
            
            if roster_data and 'roster' in roster_data:
                # 保存先パス
                filepath = os.path.join(
                    self.base_path, 
                    "players", 
                    f"roster_{team_id}_{season}.json"
                )
                
                # データ整形
                players = []
                for player in roster_data['roster']:
                    player_info = {
                        "id": player['person']['id'],
                        "fullName": player['person']['fullName'],
                        "jerseyNumber": player.get('jerseyNumber', ''),
                        "position": player['position']['name'],
                        "positionType": player['position']['type'],
                        "positionAbbreviation": player['position']['abbreviation']
                    }
                    players.append(player_info)
                
                # 保存
                save_data = {
                    "team_id": team_id,
                    "team_name": team_name,
                    "season": season,
                    "collected_at": datetime.now().isoformat(),
                    "total_players": len(players),
                    "roster": players
                }
                
                self.save_json(save_data, filepath)
                print(f"✅ {len(players)}人の選手情報を取得しました")
                
                # API制限対策で少し待機
                time.sleep(0.5)
                
                return players
            else:
                print(f"⚠️  {team_name}のロースター取得に失敗しました")
                return []
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            return []
            
    def collect_all_data(self, season=2025):
        """全データを収集するメイン関数"""
        print(f"\n{'='*50}")
        print(f"🚀 MLB {season}年シーズンデータ収集開始")
        print(f"{'='*50}")
        
        # 1. チーム情報を収集
        teams = self.collect_teams(season)
        
        # 2. 各チームのロースターを収集（最初の5チームのみ）
        print(f"\n📋 各チームのロースター情報を収集します")
        print("（デモのため最初の5チームのみ）")
        
        for i, team in enumerate(teams[:5]):  # 最初の5チームのみ
            print(f"\n[{i+1}/5]", end="")
            self.collect_team_roster(
                team['id'], 
                team['name'], 
                season
            )
            
        print(f"\n{'='*50}")
        print(f"✨ データ収集完了！")
        print(f"{'='*50}")
        

def main():
    """メイン実行関数"""
    collector = DataCollector()
    
    # 2025年のデータを収集
    collector.collect_all_data(2025)
    
    print("\n💡 ヒント:")
    print("- data/raw/teams/ フォルダにチーム情報が保存されています")
    print("- data/raw/players/ フォルダに選手情報が保存されています")
    print("- 全チームのデータを収集するには、teams[:5]をteamsに変更してください")
    

if __name__ == "__main__":
    main()