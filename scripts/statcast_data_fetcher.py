"""
Baseball SaventからStatcastデータを取得するモジュール
"""
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import logging
import csv
import io

logger = logging.getLogger(__name__)

class StatcastDataFetcher:
    """Baseball SaventのStatcastデータを取得するクラス"""
    
    def __init__(self, cache_dir: str = "cache/statcast"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Baseball Savant API endpoints
        self.base_url = "https://baseballsavant.mlb.com"
        
    def get_team_statcast_data(self, team_name: str, season: int = 2025) -> Dict[str, Any]:
        """チームのStatcastデータを取得"""
        
        # キャッシュチェック
        cache_file = os.path.join(self.cache_dir, f"{team_name}_{season}_statcast.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    # キャッシュが24時間以内なら使用
                    cache_time = datetime.fromisoformat(cached_data['timestamp'])
                    if datetime.now() - cache_time < timedelta(hours=24):
                        logger.info(f"Using cached Statcast data for {team_name}")
                        return cached_data['data']
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        try:
            # Baseball Savant Team Leaderboard API
            # このエンドポイントは実際のStatcastデータを返す
            url = f"{self.base_url}/leaderboard/statcast"
            
            params = {
                'type': 'team',
                'year': season,
                'team': team_name,
                'min_pa': 1
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # データ形式を確認してパース
                team_data = self._parse_statcast_response(data, team_name)
                
                # キャッシュに保存
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'data': team_data
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False)
                
                return team_data
            else:
                logger.error(f"Failed to fetch Statcast data: {response.status_code}")
                return self._get_default_statcast_data()
                
        except Exception as e:
            logger.error(f"Error fetching Statcast data: {e}")
            return self._get_default_statcast_data()
    
    def get_team_statcast_by_id(self, team_id: int, season: int = 2025) -> Dict[str, Any]:
        """チームIDからStatcastデータを取得"""
        # チームIDから名前への変換
        team_mapping = {
            147: "NYY",  # Yankees
            110: "BAL",  # Orioles
            # 他のチームも必要に応じて追加
        }
        
        team_name = team_mapping.get(team_id, "")
        if not team_name:
            logger.warning(f"Unknown team ID: {team_id}")
            return self._get_default_statcast_data()
        
        return self.get_team_statcast_data(team_name, season)
    
    def _parse_statcast_response(self, data: Any, team_name: str) -> Dict[str, Any]:
        """Statcastレスポンスをパース"""
        # レスポンス形式に応じて調整が必要
        # 実際のレスポンス形式を確認して実装
        
        # デフォルト値
        result = {
            'barrel_pct': 0.0,
            'hard_hit_pct': 0.0,
            'avg_exit_velocity': 0.0,
            'avg_launch_angle': 0.0,
            'sweet_spot_pct': 0.0,
            'xba': 0.0,
            'xslg': 0.0,
            'xwoba': 0.0,
            'xwobacon': 0.0
        }
        
        # データから実際の値を抽出
        if isinstance(data, list) and len(data) > 0:
            for item in data:
                if item.get('team_name') == team_name or item.get('team_abbrev') == team_name:
                    result['barrel_pct'] = float(item.get('barrel_batted_rate', 0))
                    result['hard_hit_pct'] = float(item.get('hard_hit_percent', 0))
                    result['avg_exit_velocity'] = float(item.get('avg_exit_velocity', 0))
                    result['avg_launch_angle'] = float(item.get('avg_launch_angle', 0))
                    result['sweet_spot_pct'] = float(item.get('sweet_spot_percent', 0))
                    result['xba'] = float(item.get('xba', 0))
                    result['xslg'] = float(item.get('xslg', 0))
                    result['xwoba'] = float(item.get('xwoba', 0))
                    result['xwobacon'] = float(item.get('xwobacon', 0))
                    break
        
        return result
    
    def _get_default_statcast_data(self) -> Dict[str, Any]:
        """デフォルトのStatcastデータ"""
        return {
            'barrel_pct': 8.0,
            'hard_hit_pct': 40.0,
            'avg_exit_velocity': 88.0,
            'avg_launch_angle': 12.0,
            'sweet_spot_pct': 33.0,
            'xba': .250,
            'xslg': .420,
            'xwoba': .320,
            'xwobacon': .370
        }


class StatcastCSVFetcher:
    """Baseball SaventのCSVデータを取得"""
    
    def __init__(self):
        # CSVエクスポートURL
        self.csv_url = "https://baseballsavant.mlb.com/leaderboard/statcast?type=team&year=2025&position=&team=&min=q&csv=true"
    
    def get_all_teams_statcast(self, season: int = 2025) -> Dict[str, Dict[str, Any]]:
        """全チームのStatcastデータを取得"""
        try:
            url = self.csv_url.replace("year=2025", f"year={season}")
            print(f"Fetching CSV from: {url}")
            
            response = requests.get(url)
            
            if response.status_code == 200:
                # デバッグ：最初の500文字を表示
                print(f"Response preview: {response.text[:500]}")
                
                # CSVをパース
                csv_data = io.StringIO(response.text)
                reader = csv.DictReader(csv_data)
                
                # デバッグ：ヘッダーを表示
                print(f"CSV Headers: {reader.fieldnames}")
                
                teams_data = {}
                for row in reader:
                    # デバッグ：最初の行を表示
                    if len(teams_data) == 0:
                        print(f"First row: {row}")
                    
                    team = row.get('team_name', row.get('entity_name', row.get('team', '')))
                    if team:
                        # カラム名のバリエーションに対応
                        teams_data[team] = {
                            'barrel_pct': float(row.get('barrel_batted_rate', row.get('barrel%', row.get('barrel_rate', 0)))),
                            'hard_hit_pct': float(row.get('hard_hit_percent', row.get('hard_hit%', row.get('hard_hit_rate', 0)))),
                            'avg_exit_velocity': float(row.get('exit_velocity_avg', row.get('avg_ev', row.get('ev', 0)))),
                            'avg_launch_angle': float(row.get('launch_angle_avg', row.get('avg_la', row.get('la', 0)))),
                            'sweet_spot_pct': float(row.get('sweet_spot_percent', row.get('sweet_spot%', 0))),
                            'xba': float(row.get('bacon', row.get('xba', 0))),
                            'xslg': float(row.get('slgcon', row.get('xslg', 0))),
                            'xwoba': float(row.get('wobacon', row.get('xwoba', 0)))
                        }
                
                print(f"Successfully fetched data for {len(teams_data)} teams")
                return teams_data
            else:
                print(f"Failed to fetch CSV: {response.status_code}")
                return {}
            
        except Exception as e:
            logger.error(f"Error fetching CSV data: {e}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return {}


# テスト用
if __name__ == "__main__":
    # CSV取得のテスト
    csv_fetcher = StatcastCSVFetcher()
    all_teams = csv_fetcher.get_all_teams_statcast()
    if all_teams:
        print("\nAll teams data available:")
        for team, data in list(all_teams.items())[:5]:
            print(f"{team}: Barrel={data['barrel_pct']}%, Hard-Hit={data['hard_hit_pct']}%")