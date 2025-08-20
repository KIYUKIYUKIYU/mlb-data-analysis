import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime

class FanGraphsNPBInternationalExplorer:
    """FanGraphs International NPBセクションを探索"""
    
    def __init__(self):
        self.base_url = "https://www.fangraphs.com/leaders/international/npb"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def explore_npb_international(self):
        """NPB Internationalページを詳細に探索"""
        print("=== FanGraphs NPB International データ探索 ===\n")
        print(f"URL: {self.base_url}")
        print("="*60)
        
        try:
            response = self.session.get(self.base_url, timeout=15)
            print(f"\nステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 1. ページタイトルと構造を確認
                title = soup.find('title')
                if title:
                    print(f"ページタイトル: {title.text.strip()}")
                
                # 2. 利用可能なセクション/タブを確認
                print("\n【利用可能なセクション】")
                
                # タブやナビゲーションを探す
                nav_items = soup.find_all(['a', 'button'], class_=['tab', 'nav-link', 'menu-item'])
                if nav_items:
                    for item in nav_items[:10]:
                        text = item.text.strip()
                        if text:
                            print(f"  - {text}")
                
                # 3. データテーブルの探索
                print("\n【データテーブルの探索】")
                
                # 様々な方法でテーブルを探す
                tables = soup.find_all('table')
                print(f"テーブル総数: {len(tables)}")
                
                # React/Vue.jsアプリケーションの可能性をチェック
                if 'react' in response.text.lower() or 'vue' in response.text.lower():
                    print("  ※ ReactまたはVue.jsアプリケーションの可能性があります")
                
                # データを含む可能性のあるdivを探す
                data_containers = soup.find_all('div', class_=['data-table', 'stats-table', 'leaderboard'])
                if data_containers:
                    print(f"  データコンテナ候補: {len(data_containers)}個")
                
                # 4. 統計カテゴリーの確認
                print("\n【統計カテゴリー】")
                
                # セレクトボックスやフィルターを探す
                selects = soup.find_all('select')
                for select in selects:
                    select_id = select.get('id', '')
                    select_name = select.get('name', '')
                    if select_id or select_name:
                        print(f"\n  セレクトボックス: {select_id or select_name}")
                        options = select.find_all('option')
                        for opt in options[:5]:
                            print(f"    - {opt.text.strip()}")
                
                # 5. APIエンドポイントの調査
                print("\n【APIエンドポイントの調査】")
                
                # JavaScriptからAPIエンドポイントを探す
                scripts = soup.find_all('script')
                api_patterns = ['api/', 'endpoint', 'graphql', 'data/', '.json']
                
                for script in scripts:
                    if script.string:
                        for pattern in api_patterns:
                            if pattern in script.string.lower():
                                print(f"  ✓ APIパターン '{pattern}' を検出")
                                # 実際のエンドポイントを抽出する試み
                                lines = script.string.split('\n')
                                for line in lines:
                                    if pattern in line.lower() and ('http' in line or '/' in line):
                                        print(f"    可能性のあるエンドポイント: {line.strip()[:100]}")
                                break
                
                # 6. データ形式の確認
                print("\n【データ形式の確認】")
                
                # JSON-LDやstructured dataを探す
                json_ld = soup.find('script', type='application/ld+json')
                if json_ld:
                    print("  ✓ JSON-LD形式のデータを検出")
                
                # data属性を持つ要素を探す
                data_elements = soup.find_all(attrs={"data-players": True})
                if data_elements:
                    print(f"  ✓ data-players属性を持つ要素: {len(data_elements)}個")
                
                return soup
                
        except Exception as e:
            print(f"\nエラー: {type(e).__name__}: {str(e)}")
            return None
    
    def check_specific_urls(self):
        """NPB関連の可能性のあるURLをチェック"""
        print("\n\n【追加URLパターンのチェック】")
        print("="*60)
        
        # 可能性のあるURLパターン
        test_patterns = [
            "/leaders/international/npb?year=2024",
            "/leaders/international/npb?year=2023",
            "/leaders/international/npb/batting",
            "/leaders/international/npb/pitching",
            "/leaders/international/npb?type=batting",
            "/leaders/international/npb?type=pitching",
            "/api/leaders/international/npb",
            "/graphql"  # GraphQLエンドポイントの可能性
        ]
        
        base = "https://www.fangraphs.com"
        
        for pattern in test_patterns:
            url = base + pattern
            print(f"\nテスト: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                print(f"  ステータス: {response.status_code}")
                
                if response.status_code == 200:
                    # JSONレスポンスかチェック
                    try:
                        data = response.json()
                        print(f"  ✓ JSONデータ: {len(data)}項目" if isinstance(data, list) else "  ✓ JSONオブジェクト")
                    except:
                        # HTMLの場合
                        if '<table' in response.text:
                            print("  ✓ HTMLテーブルを含む")
                        else:
                            print("  △ HTMLページ（テーブルなし）")
                            
            except Exception as e:
                print(f"  × エラー: {type(e).__name__}")
            
            time.sleep(1)
    
    def extract_sample_data(self, soup):
        """サンプルデータの抽出を試みる"""
        print("\n\n【サンプルデータの抽出】")
        print("="*60)
        
        # もしsoupがNoneなら終了
        if not soup:
            print("  × ページデータがありません")
            return
        
        # 開発者ツールで確認する手順を提案
        print("\n推奨される手動確認手順:")
        print("1. Chromeで https://www.fangraphs.com/leaders/international/npb を開く")
        print("2. F12キーで開発者ツールを開く")
        print("3. Networkタブを選択")
        print("4. ページをリロード（F5）")
        print("5. XHRまたはFetchタイプのリクエストを確認")
        print("6. 特に以下を探す:")
        print("   - /api/ で始まるリクエスト")
        print("   - .json で終わるリクエスト")
        print("   - graphql を含むリクエスト")
        print("7. Response タブでデータ形式を確認")
    
    def save_findings(self):
        """調査結果を保存"""
        findings = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'status': 'NPB International section found',
            'notes': [
                'メインURL: https://www.fangraphs.com/leaders/international/npb',
                'データはおそらく動的に読み込まれている（React/Vue.js）',
                '開発者ツールでのネットワーク分析が必要',
                'APIエンドポイントの特定が次のステップ'
            ]
        }
        
        with open('fangraphs_npb_international_findings.json', 'w', encoding='utf-8') as f:
            json.dump(findings, f, ensure_ascii=False, indent=2)
        
        print("\n\n調査結果を保存しました: fangraphs_npb_international_findings.json")

# 実行
if __name__ == "__main__":
    explorer = FanGraphsNPBInternationalExplorer()
    
    # メインページを探索
    soup = explorer.explore_npb_international()
    
    # 追加URLをチェック
    explorer.check_specific_urls()
    
    # サンプルデータ抽出の試み
    explorer.extract_sample_data(soup)
    
    # 結果を保存
    explorer.save_findings()
    
    print("\n" + "="*60)
    print("探索完了！")
    print("\n次のステップ:")
    print("1. ブラウザで実際のページを確認")
    print("2. 開発者ツールでAPIエンドポイントを特定")
    print("3. 見つかったエンドポイントで詳細なデータ取得を実装")