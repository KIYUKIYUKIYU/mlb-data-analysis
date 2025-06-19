"""
MLB Stats API Client
基本的なAPIアクセス機能
"""

import requests
import json

class MLBApiClient:
    """MLB Stats API クライアント"""
    
    BASE_URL = "https://statsapi.mlb.com/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_teams(self, season=2024):
        """チーム一覧を取得"""
        url = f"{self.BASE_URL}/teams"
        params = {'season': season, 'sportId': 1}
        
        response = self.session.get(url, params=params)
        return response.json()

# テスト
if __name__ == "__main__":
    client = MLBApiClient()
    print("MLB API Client created!")