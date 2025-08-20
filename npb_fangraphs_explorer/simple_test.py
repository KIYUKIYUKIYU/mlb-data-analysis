import requests
from bs4 import BeautifulSoup
import time

def test_fangraphs_npb():
    """FanGraphsのNPBデータが存在するか簡単にテスト"""
    
    print("=== FanGraphs NPBデータ 簡易テスト ===\n")
    
    # テストするURL（これらは推測なので、実際とは異なる可能性があります）
    test_urls = [
        # 一般的なパターン
        "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=jp&qual=0",
        "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=jp&qual=0",
        
        # 2024年シーズン
        "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=jp&qual=0&season=2024",
        "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=jp&qual=0&season=2024",
        
        # 国際リーグとしての可能性
        "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=intl&qual=0",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nテスト {i}: {url}")
        print("-" * 60)
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # ページタイトルを確認
                title = soup.find('title')
                if title:
                    print(f"ページタイトル: {title.text.strip()}")
                
                # テーブルの存在を確認
                tables = soup.find_all('table')
                print(f"テーブル数: {len(tables)}")
                
                # NPBやJapanの文字列を探す
                page_text = response.text.lower()
                if 'japan' in page_text or 'npb' in page_text or 'jp' in page_text:
                    print("✓ 日本野球関連のキーワードを検出")
                else:
                    print("× 日本野球関連のキーワードが見つかりません")
                
                # データテーブルを探す
                data_table = soup.find('table', {'class': 'rgMasterTable'}) or \
                           soup.find('table', {'id': 'LeaderBoard1_dg1'})
                
                if data_table:
                    print("✓ データテーブルを発見")
                    
                    # ヘッダーを取得
                    headers_found = []
                    header_row = data_table.find('thead') or data_table.find('tr')
                    if header_row:
                        for th in header_row.find_all(['th', 'td'])[:10]:  # 最初の10個
                            text = th.text.strip()
                            if text:
                                headers_found.append(text)
                    
                    if headers_found:
                        print(f"カラム例: {', '.join(headers_found)}")
                        
            elif response.status_code == 404:
                print("× ページが存在しません")
            else:
                print(f"× 予期しないステータスコード")
                
        except requests.exceptions.Timeout:
            print("× タイムアウト")
        except requests.exceptions.ConnectionError:
            print("× 接続エラー")
        except Exception as e:
            print(f"× エラー: {type(e).__name__}: {str(e)}")
        
        # サーバーに優しく
        time.sleep(2)
    
    print("\n" + "="*60)
    print("\n次のステップ:")
    print("1. 実際のFanGraphsサイトでNPBデータの場所を確認")
    print("2. ブラウザの開発者ツール(F12)でネットワークタブを確認")
    print("3. 正しいURLパターンを特定したら、詳細な探索を実行")

if __name__ == "__main__":
    test_fangraphs_npb()