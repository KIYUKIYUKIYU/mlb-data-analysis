import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def detailed_npb_check():
    """FanGraphsのNPBデータを詳細に確認"""
    
    print("=== FanGraphs NPBデータ 詳細確認 ===\n")
    
    # lg=jpが機能しているようなので、詳細を確認
    urls = {
        "投手データ": "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=jp&qual=0&season=2024",
        "打者データ": "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=jp&qual=0&season=2024"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    for data_type, url in urls.items():
        print(f"\n{'='*60}")
        print(f"【{data_type}】")
        print(f"URL: {url}")
        print('='*60)
        
        try:
            response = session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. リーグ選択の確認
            print("\n1. リーグ選択オプションを確認:")
            league_select = soup.find('select', {'id': 'LeaderBoard1_rcbLeague_Input'}) or \
                          soup.find('select', {'name': 'lg'})
            
            if league_select:
                options = league_select.find_all('option')
                for opt in options:
                    value = opt.get('value', '')
                    text = opt.text.strip()
                    selected = '✓' if opt.get('selected') else ' '
                    print(f"  [{selected}] {value}: {text}")
            
            # 2. データテーブルの確認
            print("\n2. データテーブルを探索:")
            
            # 複数のテーブルクラスを試す
            table_classes = ['rgMasterTable', 'sortable', 'stats_table', 'data_grid']
            data_table = None
            
            for class_name in table_classes:
                data_table = soup.find('table', {'class': class_name})
                if data_table:
                    print(f"  ✓ テーブルクラス '{class_name}' で発見")
                    break
            
            # IDでも試す
            if not data_table:
                table_ids = ['LeaderBoard1_dg1_ctl00', 'LeaderBoard1_dg1']
                for table_id in table_ids:
                    data_table = soup.find('table', {'id': table_id})
                    if data_table:
                        print(f"  ✓ テーブルID '{table_id}' で発見")
                        break
            
            if data_table:
                # ヘッダー行を探す
                header_row = data_table.find('thead')
                if not header_row:
                    # theadがない場合は最初のtrを確認
                    first_tr = data_table.find('tr')
                    if first_tr and (first_tr.find('th') or 'headerRow' in first_tr.get('class', [])):
                        header_row = first_tr
                
                if header_row:
                    headers = []
                    for th in header_row.find_all(['th', 'td']):
                        text = th.text.strip()
                        if text and text not in ['', '#']:
                            headers.append(text)
                    
                    print(f"\n  発見された統計カラム ({len(headers)}個):")
                    # 最初の20個を表示
                    for i, header in enumerate(headers[:20], 1):
                        print(f"    {i:2d}. {header}")
                    
                    if len(headers) > 20:
                        print(f"    ... 他 {len(headers) - 20} 個")
                    
                    # 重要な統計の存在確認
                    important_stats = ['ERA', 'FIP', 'xFIP', 'WHIP', 'K-BB%', 'wOBA', 'WAR']
                    print(f"\n  重要統計の確認:")
                    for stat in important_stats:
                        if any(stat in h for h in headers):
                            print(f"    ✓ {stat}")
                        else:
                            print(f"    × {stat}")
                
                # データ行のサンプルを取得
                data_rows = data_table.find_all('tr')[1:6]  # 最初の5行
                if data_rows:
                    print(f"\n  サンプルデータ（最初の5行）:")
                    for i, row in enumerate(data_rows, 1):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) > 2:
                            # 選手名と主要統計を表示
                            player_name = cells[1].text.strip() if len(cells) > 1 else "N/A"
                            print(f"    {i}. {player_name}")
            
            else:
                print("  × データテーブルが見つかりません")
            
            # 3. ページ内のJavaScriptを確認
            print("\n3. JavaScript/APIの確認:")
            scripts = soup.find_all('script')
            api_found = False
            for script in scripts:
                if script.string and ('api' in script.string.lower() or 'endpoint' in script.string.lower()):
                    api_found = True
                    break
            
            if api_found:
                print("  ✓ API関連のJavaScriptを検出")
            else:
                print("  × API関連のJavaScriptは見つかりません")
            
            time.sleep(2)  # サーバーに優しく
            
        except Exception as e:
            print(f"\nエラー: {type(e).__name__}: {str(e)}")
    
    # 4. 高度な統計ページの確認
    print(f"\n{'='*60}")
    print("【高度な統計の確認】")
    print('='*60)
    
    advanced_urls = {
        "投手詳細": "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=jp&qual=0&type=1&season=2024",
        "打者詳細": "https://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=jp&qual=0&type=1&season=2024"
    }
    
    # typeパラメータで異なる統計セットを試す
    stat_types = {
        "0": "Dashboard",
        "1": "Standard", 
        "2": "Advanced",
        "3": "Batted Ball",
        "4": "Win Probability",
        "5": "Pitch Type",
        "6": "Pitch Value",
        "8": "Plate Discipline"
    }
    
    print("\n利用可能な統計タイプを確認:")
    base_url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=jp&qual=0&season=2024&type="
    
    for type_code, type_name in list(stat_types.items())[:3]:  # 最初の3つだけテスト
        test_url = base_url + type_code
        try:
            response = session.get(test_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # タイトルや特定の要素で確認
                print(f"  ✓ Type {type_code} ({type_name}): アクセス可能")
            else:
                print(f"  × Type {type_code} ({type_name}): ステータス {response.status_code}")
        except:
            print(f"  × Type {type_code} ({type_name}): エラー")
        time.sleep(1)

if __name__ == "__main__":
    detailed_npb_check()