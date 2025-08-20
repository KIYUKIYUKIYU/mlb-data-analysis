#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NPB選手データスクレイピング（認証付き）
有料サービスからNPB選手のセイバーメトリクスデータを取得
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import os
from typing import Dict, List, Optional
import pickle

class NPBDataScraper:
    """NPB選手データのスクレイピングクラス（認証対応）"""
    
    def __init__(self, service_name: str = "1point02"):
        self.service_name = service_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.cache_dir = f"cache/npb_{service_name}"
        self.cookie_file = f"{self.cache_dir}/cookies.pkl"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.is_logged_in = False
        
        # サービス別の設定
        self.services = {
            "1point02": {
                "login_url": "https://1point02.jp/op/login",
                "base_url": "https://1point02.jp/op/gnav/baseball/",
                "data_url": "https://1point02.jp/op/gnav/baseball/stats/",
            },
            "deltagraphs": {
                "login_url": "https://deltagraphs.com/login",
                "base_url": "https://deltagraphs.com/",
                "data_url": "https://deltagraphs.com/npb/",
            }
        }
        
        # 使用するサービスの設定を取得
        self.config = self.services.get(service_name, self.services["1point02"])
    
    def load_cookies(self) -> bool:
        """保存されたクッキーを読み込む"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                    self.session.cookies.update(cookies)
                    print("保存されたクッキーを読み込みました")
                    return True
            except Exception as e:
                print(f"クッキーの読み込みに失敗: {e}")
        return False
    
    def save_cookies(self):
        """現在のクッキーを保存"""
        with open(self.cookie_file, 'wb') as f:
            pickle.dump(self.session.cookies, f)
            print("クッキーを保存しました")
    
    def login(self, username: str, password: str) -> bool:
        """サービスにログイン"""
        try:
            # まず保存されたクッキーを試す
            if self.load_cookies():
                # クッキーが有効か確認
                test_response = self.session.get(self.config["data_url"])
                if test_response.status_code == 200 and "ログアウト" in test_response.text:
                    print("保存されたセッションで認証済み")
                    self.is_logged_in = True
                    return True
            
            print(f"{self.service_name}にログイン中...")
            
            # ログインページを取得（CSRFトークンなどを取得）
            login_page = self.session.get(self.config["login_url"])
            soup = BeautifulSoup(login_page.text, 'html.parser')
            
            # CSRFトークンを探す（サイトによって異なる）
            csrf_token = None
            csrf_input = soup.find('input', {'name': 'csrf_token'}) or \
                        soup.find('input', {'name': '_csrf'}) or \
                        soup.find('input', {'name': 'authenticity_token'})
            
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            # ログインデータを準備
            login_data = {
                'username': username,
                'password': password
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            # ログイン実行
            response = self.session.post(
                self.config["login_url"],
                data=login_data,
                headers={'Referer': self.config["login_url"]}
            )
            
            # ログイン成功の確認
            if response.status_code == 200:
                if "ログアウト" in response.text or "マイページ" in response.text:
                    print("ログイン成功")
                    self.is_logged_in = True
                    self.save_cookies()
                    return True
                else:
                    print("ログイン失敗: 認証情報を確認してください")
                    return False
            else:
                print(f"ログイン失敗: ステータスコード {response.status_code}")
                return False
                
        except Exception as e:
            print(f"ログインエラー: {e}")
            return False
    
    def get_pitcher_data(self, pitcher_id: str) -> Optional[Dict]:
        """投手の詳細データを取得"""
        if not self.is_logged_in:
            print("ログインが必要です")
            return None
        
        try:
            # キャッシュ確認
            cache_file = f"{self.cache_dir}/pitcher_{pitcher_id}_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # データ取得
            url = f"{self.config['data_url']}pitcher/{pitcher_id}"
            response = self.session.get(url)
            
            if response.status_code != 200:
                print(f"データ取得失敗: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # データをパース（実際の構造に合わせて調整が必要）
            data = {
                'id': pitcher_id,
                'name': '',
                'team': '',
                'basic_stats': {},
                'sabermetrics': {},
                'splits': {},
                'recent_games': []
            }
            
            # 選手名
            name_elem = soup.find('h1', class_='player-name') or soup.find('div', class_='name')
            if name_elem:
                data['name'] = name_elem.text.strip()
            
            # 基本成績
            basic_table = soup.find('table', class_='basic-stats') or soup.find('table', id='basic')
            if basic_table:
                data['basic_stats'] = self._parse_basic_stats_table(basic_table)
            
            # セイバーメトリクス
            saber_table = soup.find('table', class_='sabermetrics') or soup.find('table', id='advanced')
            if saber_table:
                data['sabermetrics'] = self._parse_sabermetrics_table(saber_table)
            
            # 対左右成績
            splits_table = soup.find('table', class_='splits') or soup.find('table', id='splits')
            if splits_table:
                data['splits'] = self._parse_splits_table(splits_table)
            
            # キャッシュに保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # アクセス間隔を空ける
            time.sleep(1)
            
            return data
            
        except Exception as e:
            print(f"データ取得エラー: {e}")
            return None
    
    def get_batter_data(self, batter_id: str) -> Optional[Dict]:
        """打者の詳細データを取得"""
        if not self.is_logged_in:
            print("ログインが必要です")
            return None
        
        try:
            # キャッシュ確認
            cache_file = f"{self.cache_dir}/batter_{batter_id}_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # データ取得
            url = f"{self.config['data_url']}batter/{batter_id}"
            response = self.session.get(url)
            
            if response.status_code != 200:
                print(f"データ取得失敗: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # データをパース
            data = {
                'id': batter_id,
                'name': '',
                'team': '',
                'basic_stats': {},
                'sabermetrics': {},
                'quality_stats': {},
                'splits': {},
                'recent_games': []
            }
            
            # パース処理（実装は実際のHTML構造に依存）
            
            # キャッシュに保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            time.sleep(1)
            
            return data
            
        except Exception as e:
            print(f"データ取得エラー: {e}")
            return None
    
    def _parse_basic_stats_table(self, table) -> Dict:
        """基本成績テーブルをパース"""
        stats = {}
        try:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    
                    # 数値変換
                    try:
                        if '.' in value:
                            stats[key] = float(value)
                        else:
                            stats[key] = int(value)
                    except:
                        stats[key] = value
        except Exception as e:
            print(f"テーブルパースエラー: {e}")
        
        return stats
    
    def _parse_sabermetrics_table(self, table) -> Dict:
        """セイバーメトリクステーブルをパース"""
        # 実装は_parse_basic_stats_tableと同様
        return self._parse_basic_stats_table(table)
    
    def _parse_splits_table(self, table) -> Dict:
        """対左右成績テーブルをパース"""
        splits = {
            'vs_left': {},
            'vs_right': {}
        }
        
        try:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells and '対左' in cells[0].text:
                    # 対左投手成績
                    for i, cell in enumerate(cells[1:]):
                        # 実際の列構造に応じて調整
                        pass
                elif cells and '対右' in cells[0].text:
                    # 対右投手成績
                    pass
        except Exception as e:
            print(f"対左右成績パースエラー: {e}")
        
        return splits
    
    def get_team_roster(self, team_code: str) -> List[Dict]:
        """チームの選手一覧を取得"""
        if not self.is_logged_in:
            print("ログインが必要です")
            return []
        
        try:
            url = f"{self.config['data_url']}team/{team_code}/roster"
            response = self.session.get(url)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            roster = []
            
            # 選手リストをパース（実際の構造に依存）
            player_rows = soup.find_all('tr', class_='player-row')
            
            for row in player_rows:
                player = {
                    'id': '',
                    'name': '',
                    'position': '',
                    'number': ''
                }
                
                # データ抽出
                # ...
                
                roster.append(player)
            
            return roster
            
        except Exception as e:
            print(f"ロスター取得エラー: {e}")
            return []
    
    def create_game_report(self, home_team: str, away_team: str, 
                          home_pitcher_id: str, away_pitcher_id: str) -> str:
        """試合レポートを生成"""
        report = []
        report.append("=" * 60)
        report.append(f"NPB試合分析レポート - {datetime.now().strftime('%Y/%m/%d')}")
        report.append(f"{away_team} @ {home_team}")
        report.append("=" * 60)
        
        # 先発投手データを取得
        away_pitcher = self.get_pitcher_data(away_pitcher_id)
        home_pitcher = self.get_pitcher_data(home_pitcher_id)
        
        if away_pitcher:
            report.append(f"\n【{away_team}】先発: {away_pitcher['name']}")
            # 統計を追加
            
        if home_pitcher:
            report.append(f"\n【{home_team}】先発: {home_pitcher['name']}")
            # 統計を追加
        
        return "\n".join(report)

def main():
    """使用例"""
    # 認証情報（環境変数から取得することを推奨）
    USERNAME = os.environ.get('NPB_SERVICE_USER', '')
    PASSWORD = os.environ.get('NPB_SERVICE_PASS', '')
    
    if not USERNAME or not PASSWORD:
        print("環境変数 NPB_SERVICE_USER と NPB_SERVICE_PASS を設定してください")
        return
    
    # スクレイパーの初期化
    scraper = NPBDataScraper(service_name="1point02")
    
    # ログイン
    if not scraper.login(USERNAME, PASSWORD):
        print("ログインに失敗しました")
        return
    
    # 投手データの取得例
    pitcher_data = scraper.get_pitcher_data("pitcher_123")
    if pitcher_data:
        print(json.dumps(pitcher_data, ensure_ascii=False, indent=2))
    
    # 試合レポートの生成例
    report = scraper.create_game_report(
        home_team="読売ジャイアンツ",
        away_team="阪神タイガース",
        home_pitcher_id="pitcher_123",
        away_pitcher_id="pitcher_456"
    )
    print(report)

if __name__ == "__main__":
    main()