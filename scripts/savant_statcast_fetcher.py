"""
Baseball Savant Statcast データ取得モジュール
全チームのBarrel%とHard-Hit%を取得
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import logging
from io import StringIO

class SavantStatcastFetcher:
    """Baseball SavantからStatcastデータを取得するクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_dir = "cache/statcast_data"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # チームIDとチーム略称のマッピング
        self.team_mapping = {
            108: 'LAA', 109: 'ARI', 110: 'BAL', 111: 'BOS', 112: 'CHC',
            113: 'CIN', 114: 'CLE', 115: 'COL', 116: 'DET', 117: 'HOU',
            118: 'KC', 119: 'LAD', 120: 'WSH', 121: 'NYM', 133: 'OAK',
            134: 'PIT', 135: 'SD', 136: 'SEA', 137: 'SF', 138: 'STL',
            139: 'TB', 140: 'TEX', 141: 'TOR', 142: 'MIN', 143: 'PHI',
            144: 'ATL', 145: 'CWS', 146: 'MIA', 147: 'NYY', 158: 'MIL'
        }
        
        # 逆引き辞書も作成
        self.abbr_to_id = {v: k for k, v in self.team_mapping.items()}
    
    def get_all_teams_statcast_data(self, start_date=None, end_date=None):
        """
        全チームのStatcastデータを取得
        
        Args:
            start_date: 開始日（デフォルト: 30日前）
            end_date: 終了日（デフォルト: 今日）
            
        Returns:
            dict: チームIDをキーとしたBarrel%とHard-Hit%の辞書
        """
        # キャッシュチェック
        cache_file = os.path.join(self.cache_dir, f"all_teams_statcast_2025.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < timedelta(days=1):
                    self.logger.info("Using cached Statcast data")
                    return cache_data['data']
            except Exception as e:
                self.logger.warning(f"Cache read error: {e}")
        
        # 日付の設定
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        self.logger.info(f"Fetching Statcast data from {start_date} to {end_date}")
        
        # Baseball Savant APIから全打球データを取得
        url = "https://baseballsavant.mlb.com/statcast_search/csv"
        
        params = {
            'all': 'true',
            'type': 'details',
            'player_type': 'batter',
            'hfSea': '2025|',
            'hfGT': 'R|',  # レギュラーシーズンのみ
            'game_date_gt': start_date,
            'game_date_lt': end_date,
            'min_results': '0',
            'group_by': 'name',
            'sort_col': 'pitches',
            'sort_order': 'desc'
        }
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            # CSVデータをDataFrameに読み込む
            df = pd.read_csv(StringIO(response.text))
            
            if df.empty:
                self.logger.warning("No data returned from Baseball Savant")
                return self._get_default_data()
            
            # チームごとにデータを集計
            result = {}
            
            # 必要なカラムの確認
            self.logger.info(f"Available columns: {df.columns.tolist()[:20]}...")
            
            # チームごとに集計
            if 'player_name' in df.columns:
                # チーム名でグループ化が必要な場合
                # まず各打球イベントにbarrelフラグを追加
                if 'launch_speed' in df.columns and 'launch_angle' in df.columns:
                    # Barrelの定義: 打球速度98mph以上、打球角度26-30度（簡略版）
                    df['is_barrel'] = (
                        (df['launch_speed'] >= 98) & 
                        (df['launch_angle'] >= 26) & 
                        (df['launch_angle'] <= 30)
                    )
                    
                    # Hard-Hitの定義: 打球速度95mph以上
                    df['is_hard_hit'] = df['launch_speed'] >= 95
                    
                    # チーム別に集計（選手名からチームを推定する必要がある）
                    # これは複雑なので、別のアプローチを試す
            
            # 別のアプローチ: チームごとに個別にリクエスト
            result = self._fetch_by_team(start_date, end_date)
            
            # キャッシュに保存
            cache_data = {
                'data': result,
                'timestamp': datetime.now().isoformat(),
                'start_date': start_date,
                'end_date': end_date
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching Statcast data: {str(e)}")
            return self._get_default_data()
    
    def _fetch_by_team(self, start_date, end_date):
        """チームごとに個別にデータを取得"""
        result = {}
        
        for team_id, team_abbr in self.team_mapping.items():
            self.logger.info(f"Fetching data for {team_abbr}")
            
            try:
                url = "https://baseballsavant.mlb.com/statcast_search/csv"
                
                params = {
                    'all': 'true',
                    'type': 'details',
                    'player_type': 'batter',
                    'hfSea': '2025|',
                    'hfGT': 'R|',
                    'team': team_abbr,
                    'game_date_gt': start_date,
                    'game_date_lt': end_date,
                    'min_results': '0'
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    df = pd.read_csv(StringIO(response.text))
                    
                    if not df.empty and 'launch_speed' in df.columns:
                        # 有効な打球データのみを対象
                        valid_df = df[df['launch_speed'].notna()]
                        
                        if len(valid_df) > 0:
                            # Barrel%の計算
                            # Barrelの簡易定義: 打球速度98mph以上かつ適切な角度
                            if 'launch_angle' in df.columns:
                                barrels = valid_df[
                                    (valid_df['launch_speed'] >= 98) & 
                                    (valid_df['launch_angle'] >= 10) & 
                                    (valid_df['launch_angle'] <= 50)
                                ]
                                barrel_pct = (len(barrels) / len(valid_df)) * 100
                            else:
                                barrel_pct = 8.0  # デフォルト値
                            
                            # Hard-Hit%の計算（95mph以上）
                            hard_hits = valid_df[valid_df['launch_speed'] >= 95]
                            hard_hit_pct = (len(hard_hits) / len(valid_df)) * 100
                            
                            result[team_id] = {
                                'barrel_pct': round(barrel_pct, 1),
                                'hard_hit_pct': round(hard_hit_pct, 1),
                                'sample_size': len(valid_df),
                                'source': 'savant'
                            }
                            
                            self.logger.info(f"  {team_abbr}: Barrel% = {barrel_pct:.1f}, Hard-Hit% = {hard_hit_pct:.1f}")
                        else:
                            result[team_id] = self._get_team_default(team_id)
                    else:
                        result[team_id] = self._get_team_default(team_id)
                else:
                    result[team_id] = self._get_team_default(team_id)
                    
            except Exception as e:
                self.logger.error(f"Error fetching data for {team_abbr}: {str(e)}")
                result[team_id] = self._get_team_default(team_id)
        
        return result
    
    def _get_team_default(self, team_id):
        """チームのデフォルト値を返す"""
        # キャッシュファイルから実データを取得
        cache_file = os.path.join(self.cache_dir, f"all_teams_statcast_2025.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if team_id in cache_data['data']:
                    return cache_data['data'][team_id]
            except Exception:
                pass
        
        # キャッシュがない場合のフォールバック
        return {
            'barrel_pct': 8.0,
            'hard_hit_pct': 40.0,
            'source': 'default'
        }
    
    def _get_default_data(self):
        """全チームのデフォルトデータを返す"""
        result = {}
        for team_id in self.team_mapping.keys():
            result[team_id] = self._get_team_default(team_id)
        return result
    
    def get_team_statcast_data(self, team_id):
        """特定チームのStatcastデータを取得"""
        # まずキャッシュファイルを確認
        cache_file = os.path.join(self.cache_dir, f"all_teams_statcast_2025.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # team_idが文字列か数値か両方チェック
                if str(team_id) in cache_data['data']:
                    return cache_data['data'][str(team_id)]
                elif team_id in cache_data['data']:
                    return cache_data['data'][team_id]
            except Exception as e:
                self.logger.warning(f"Error reading cache: {e}")
        
        # キャッシュがない場合は全データを取得
        all_data = self.get_all_teams_statcast_data()
        return all_data.get(team_id, self._get_team_default(team_id))


# 既存のbatting_quality_stats.pyと統合するための関数
def update_batting_quality_stats_with_savant():
    """batting_quality_stats.pyをSavantデータで更新"""
    fetcher = SavantStatcastFetcher()
    
    # 全チームのデータを取得
    all_teams_data = fetcher.get_all_teams_statcast_data()
    
    # 結果を表示
    print("\n=== Statcast Data Summary ===")
    for team_id, data in sorted(all_teams_data.items()):
        team_abbr = fetcher.team_mapping.get(team_id, f"Team{team_id}")
        print(f"{team_abbr}: Barrel% = {data['barrel_pct']:.1f}, "
              f"Hard-Hit% = {data['hard_hit_pct']:.1f} "
              f"(source: {data['source']})")
    
    return all_teams_data


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    update_batting_quality_stats_with_savant()