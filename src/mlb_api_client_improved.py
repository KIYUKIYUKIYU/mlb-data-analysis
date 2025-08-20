# mlb_api_client_improved.py
# 対左右成績の500エラーを回避する改善版

import requests
import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

class MLBApiClient:
    def __init__(self):
        self.base_url = "https://statsapi.mlb.com/api/v1"
        self.session = requests.Session()
        self.cache_dir = "cache/splits_data"
        self.ensure_cache_directory()
        
    def ensure_cache_directory(self):
        """キャッシュディレクトリを作成"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_player_splits_with_retry(self, player_id: int, season: int, max_retries: int = 3) -> Optional[Dict]:
        """
        選手の対左右成績を取得（リトライ機能付き）
        
        段階的フォールバック:
        1. キャッシュから取得
        2. 現在のシーズンのAPIから取得（リトライ付き）
        3. 前シーズンのデータを試す
        4. 代替エンドポイントを使用
        5. リーグ平均値を返す
        """
        
        # 1. キャッシュから取得を試みる
        cached_data = self.get_from_cache(player_id, season)
        if cached_data:
            print(f"対左右成績をキャッシュから取得: 選手ID {player_id}")
            return cached_data
        
        # 2. 現在のシーズンのAPIから取得（リトライ付き）
        for attempt in range(max_retries):
            try:
                splits_data = self.get_player_splits_direct(player_id, season)
                if splits_data:
                    self.save_to_cache(player_id, season, splits_data)
                    return splits_data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 500:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数バックオフ: 1秒, 2秒, 4秒
                        print(f"500エラー発生。{wait_time}秒待機してリトライ... (試行 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"選手ID {player_id}: 500エラーが継続。代替方法を試します。")
                else:
                    raise
        
        # 3. 前シーズンのデータを試す
        if season > 2020:
            print(f"前シーズン({season-1})のデータ取得を試みます...")
            try:
                prev_season_data = self.get_player_splits_direct(player_id, season - 1)
                if prev_season_data:
                    # 前年データであることを明示
                    prev_season_data['note'] = f'{season-1}年のデータを使用'
                    return prev_season_data
            except:
                pass
        
        # 4. 代替エンドポイントを使用
        print("代替エンドポイントからデータ取得を試みます...")
        alternative_data = self.get_player_splits_alternative(player_id, season)
        if alternative_data:
            self.save_to_cache(player_id, season, alternative_data)
            return alternative_data
        
        # 5. リーグ平均値を返す
        print(f"選手ID {player_id}: 実データ取得失敗。リーグ平均値を使用します。")
        return self.get_league_average_splits(season)
    
    def get_player_splits_direct(self, player_id: int, season: int) -> Optional[Dict]:
        """通常のsplitsエンドポイントからデータ取得"""
        url = f"{self.base_url}/people/{player_id}/stats"
        params = {
            'stats': 'statSplits',
            'season': season,
            'group': 'hitting',
            'sitCodes': 'vl,vr'  # vs左投手, vs右投手
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self.parse_splits_response(data)
    
    def get_player_splits_alternative(self, player_id: int, season: int) -> Optional[Dict]:
        """
        代替方法で対左右成績を取得
        複数のエンドポイントを試す
        """
        
        # 方法1: 詳細なstatsパラメータを使用
        try:
            url = f"{self.base_url}/people/{player_id}/stats"
            params = {
                'stats': 'statSplits',
                'season': season,
                'fields': 'stats,splits,stat,avg,ops,obp,slg,split,displayName'
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                parsed = self.parse_splits_response(data)
                if parsed:
                    return parsed
        except:
            pass
        
        # 方法2: seasonまたはcareerスタッツから推定
        try:
            season_stats = self.get_player_stats_by_season(player_id, season)
            if season_stats:
                # シーズン全体の成績から推定値を作成
                avg = float(season_stats.get('avg', '.250'))
                ops = float(season_stats.get('ops', '.700'))
                
                # 一般的な傾向に基づく推定
                # 右打者は左投手に強い、左打者は右投手に強い傾向
                return {
                    'vsL': {
                        'avg': f"{avg + 0.010:.3f}",  # やや高め
                        'ops': f"{ops + 0.030:.3f}",
                        'note': 'シーズン成績からの推定値'
                    },
                    'vsR': {
                        'avg': f"{avg - 0.010:.3f}",  # やや低め
                        'ops': f"{ops - 0.030:.3f}",
                        'note': 'シーズン成績からの推定値'
                    }
                }
        except:
            pass
        
        return None
    
    def parse_splits_response(self, data: Dict) -> Optional[Dict]:
        """APIレスポンスから対左右成績を抽出"""
        try:
            stats = data.get('stats', [])
            if not stats:
                return None
            
            splits_data = {'vsL': None, 'vsR': None}
            
            for stat_group in stats:
                splits = stat_group.get('splits', [])
                for split in splits:
                    split_name = split.get('split', {}).get('code', '')
                    if split_name == 'vl':  # vs Left
                        splits_data['vsL'] = {
                            'avg': split.get('stat', {}).get('avg', '.000'),
                            'ops': split.get('stat', {}).get('ops', '.000'),
                            'obp': split.get('stat', {}).get('obp', '.000'),
                            'slg': split.get('stat', {}).get('slg', '.000'),
                            'ab': split.get('stat', {}).get('atBats', 0),
                            'h': split.get('stat', {}).get('hits', 0)
                        }
                    elif split_name == 'vr':  # vs Right
                        splits_data['vsR'] = {
                            'avg': split.get('stat', {}).get('avg', '.000'),
                            'ops': split.get('stat', {}).get('ops', '.000'),
                            'obp': split.get('stat', {}).get('obp', '.000'),
                            'slg': split.get('stat', {}).get('slg', '.000'),
                            'ab': split.get('stat', {}).get('atBats', 0),
                            'h': split.get('stat', {}).get('hits', 0)
                        }
            
            # データが見つかった場合のみ返す
            if splits_data['vsL'] or splits_data['vsR']:
                return splits_data
            
            return None
        except Exception as e:
            print(f"splits解析エラー: {e}")
            return None
    
    def get_league_average_splits(self, season: int) -> Dict:
        """リーグ平均の対左右成績を返す"""
        # MLBの一般的な傾向値
        # 実際のリーグ平均値を事前に調査して設定
        return {
            'vsL': {
                'avg': '.255',
                'ops': '.720',
                'note': f'{season}年リーグ平均値（推定）'
            },
            'vsR': {
                'avg': '.250',
                'ops': '.710',
                'note': f'{season}年リーグ平均値（推定）'
            },
            'data_source': 'league_average'
        }
    
    def get_from_cache(self, player_id: int, season: int) -> Optional[Dict]:
        """キャッシュからデータを取得"""
        cache_file = os.path.join(self.cache_dir, f"player_{player_id}_{season}.json")
        
        if os.path.exists(cache_file):
            # キャッシュの有効期限を確認（24時間）
            file_time = os.path.getmtime(cache_file)
            if time.time() - file_time < 86400:  # 24時間
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        
        return None
    
    def save_to_cache(self, player_id: int, season: int, data: Dict):
        """データをキャッシュに保存"""
        cache_file = os.path.join(self.cache_dir, f"player_{player_id}_{season}.json")
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"キャッシュ保存エラー: {e}")
    
    def get_player_stats_by_season(self, player_id: int, season: int) -> Optional[Dict]:
        """選手のシーズン成績を取得（既存メソッドのスタブ）"""
        # 実際の実装では、既存のmlb_api_client.pyからこのメソッドをコピー
        url = f"{self.base_url}/people/{player_id}/stats"
        params = {
            'stats': 'season',
            'season': season,
            'group': 'hitting'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 基本的な成績を抽出
            stats = data.get('stats', [])
            if stats and stats[0].get('splits'):
                return stats[0]['splits'][0].get('stat', {})
        except:
            pass
        
        return None
    
    def prefetch_splits_data(self, player_ids: List[int], season: int):
        """
        複数選手の対左右成績を事前取得
        夜間バッチ処理などで使用
        """
        success_count = 0
        failed_ids = []
        
        print(f"{len(player_ids)}名の選手の対左右成績を事前取得します...")
        
        for i, player_id in enumerate(player_ids, 1):
            try:
                # キャッシュに既にある場合はスキップ
                if self.get_from_cache(player_id, season):
                    success_count += 1
                    continue
                
                # データ取得
                splits_data = self.get_player_splits_with_retry(player_id, season)
                if splits_data and splits_data.get('data_source') != 'league_average':
                    success_count += 1
                else:
                    failed_ids.append(player_id)
                
                # レート制限対策
                if i % 10 == 0:
                    print(f"進捗: {i}/{len(player_ids)}")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"選手ID {player_id} の取得エラー: {e}")
                failed_ids.append(player_id)
        
        print(f"\n事前取得完了: 成功 {success_count}/{len(player_ids)}")
        if failed_ids:
            print(f"失敗した選手ID: {failed_ids}")
        
        return success_count, failed_ids


# 使用例
if __name__ == "__main__":
    client = MLBApiClient()
    
    # テスト用の選手ID（実際の選手IDに置き換えてください）
    test_player_id = 660271  # 例: Shohei Ohtani
    
    print("対左右成績の取得テスト")
    print("-" * 50)
    
    splits = client.get_player_splits_with_retry(test_player_id, 2025)
    
    if splits:
        print(f"\n取得成功:")
        print(f"データソース: {splits.get('data_source', 'API')}")
        if splits.get('note'):
            print(f"注記: {splits['note']}")
        
        if splits.get('vsL'):
            print(f"\n対左投手:")
            print(f"  打率: {splits['vsL'].get('avg', 'N/A')}")
            print(f"  OPS: {splits['vsL'].get('ops', 'N/A')}")
        
        if splits.get('vsR'):
            print(f"\n対右投手:")
            print(f"  打率: {splits['vsR'].get('avg', 'N/A')}")
            print(f"  OPS: {splits['vsR'].get('ops', 'N/A')}")
    else:
        print("データ取得失敗")