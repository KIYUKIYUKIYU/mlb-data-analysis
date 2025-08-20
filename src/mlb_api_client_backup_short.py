import requests

class MLBApiClient:
    BASE_URL = "https://statsapi.mlb.com/api/v1"

    def _make_request(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error for endpoint {endpoint}: {e}")
            return None

    def get_schedule(self, date: str):
        params = {'sportId': 1, 'date': date, 'hydrate': 'team,probablePitcher'}
        return self._make_request("schedule", params)

    def get_team_roster(self, team_id: int):
        return self._make_request(f"teams/{team_id}/roster")

    def get_player_stats(self, person_id: int, season: int):
        params = {'stats': 'season', 'group': 'pitching', 'season': season}
        return self._make_request(f"people/{person_id}", params)

    def get_team_stats(self, team_id: int, season: int):
        params = {'stats': 'season', 'group': 'hitting'}
        return self._make_request(f"teams/{team_id}/stats", params)

    def get_team_hitting_splits(self, team_id: int, season: int):
        params = {'stats': 'vsPlayer', 'group': 'hitting', 'season': season}
        # このエンドポイントは不安定な場合がある
        return self._make_request(f"teams/{team_id}/stats", params)

    def get_game_feed(self, game_pk: int):
        return self._make_request(f"game/{game_pk}/feed/live")