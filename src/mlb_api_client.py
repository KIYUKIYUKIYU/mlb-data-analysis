"""
MLB Stats API Client
"""
import requests
import json
from typing import Dict, List, Any


class MLBApiClient:
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com/api/v1"
        self.session = requests.Session()
        
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make API request"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}
            
    def get_teams(self, season: int) -> Dict[str, Any]:
        """Get all teams for a season"""
        endpoint = f"teams?season={season}&sportId=1"
        return self._make_request(endpoint)
        
    def get_team_roster(self, team_id: int, season: int) -> Dict[str, Any]:
        """Get team roster"""
        endpoint = f"teams/{team_id}/roster?season={season}"
        return self._make_request(endpoint)