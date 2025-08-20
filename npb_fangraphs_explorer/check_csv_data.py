import pandas as pd
import os
import glob

def check_npb_csv_files():
    """保存されたNPB CSVファイルの内容を確認"""
    
    print("=== NPB CSVファイル確認 ===\n")
    
    # CSVファイルを検索
    csv_files = glob.glob("npb_*.csv")
    
    if not csv_files:
        print("CSVファイルが見つかりません。")
        print("\n現在のディレクトリのファイル:")
        for file in os.listdir('.'):
            if file.endswith('.csv'):
                print(f"  - {file}")
        return
    
    print(f"発見されたCSVファイル: {len(csv_files)}個\n")
    
    for csv_file in csv_files:
        print(f"\n{'='*60}")
        print(f"ファイル: {csv_file}")
        print('='*60)
        
        try:
            # CSVを読み込む
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            # 基本情報
            print(f"\n行数: {len(df)}")
            print(f"列数: {len(df.columns)}")
            
            # カラム名を表示
            print("\nカラム一覧:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i:2d}. {col}")
            
            # データ型を確認
            print("\nデータ型:")
            print(df.dtypes)
            
            # 最初の5行を表示
            print("\nサンプルデータ（最初の5行）:")
            print(df.head())
            
            # 統計の詳細分析
            print("\n統計分析:")
            
            # 数値カラムを特定
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            print(f"数値カラム数: {len(numeric_cols)}")
            
            # カラム名から統計タイプを推測
            stat_categories = {
                '基本打撃': ['AVG', 'HR', 'RBI', 'H', '2B', '3B', 'SB'],
                '率系統計': ['OBP', 'SLG', 'OPS', 'ISO'],
                '高度統計': ['wOBA', 'wRC+', 'WAR', 'BABIP'],
                '投手基本': ['ERA', 'W', 'L', 'SV', 'IP', 'SO', 'BB'],
                '投手高度': ['FIP', 'xFIP', 'WHIP', 'K/9', 'BB/9']
            }
            
            for category, stats in stat_categories.items():
                found = []
                for stat in stats:
                    # 大文字小文字を無視して検索
                    matching_cols = [col for col in df.columns if stat.upper() in col.upper()]
                    if matching_cols:
                        found.extend(matching_cols)
                
                if found:
                    print(f"\n{category}: {', '.join(set(found))}")
            
            # 実際のデータが入っているか確認（空でないか）
            non_null_counts = df.count()
            print("\n非NULL値の数（各カラム）:")
            for col in df.columns[:10]:  # 最初の10カラム
                print(f"  {col}: {non_null_counts[col]}/{len(df)}")
            
        except Exception as e:
            print(f"エラー: {type(e).__name__}: {str(e)}")
    
    # 追加の分析提案
    print("\n\n=== 分析提案 ===")
    print("1. カラム名が日本語の可能性があります")
    print("2. FanGraphsのページで言語設定を確認してください")
    print("3. ブラウザで実際のテーブルヘッダーを確認してください")

def analyze_fangraphs_html_directly():
    """FanGraphsのHTMLを直接分析"""
    print("\n\n=== FanGraphs HTML直接分析 ===")
    
    import requests
    from bs4 import BeautifulSoup
    
    url = "https://www.fangraphs.com/leaders/international/npb?year=2024"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # より詳細なテーブル検索
        print("\nテーブル検索（詳細）:")
        
        # 様々なセレクタでテーブルを探す
        selectors = [
            'table.table',
            'table.data-table',
            'table.leaderboard',
            'table#LeaderBoard1_dg1_ctl00',
            'div.table-container table',
            'div.data-table table'
        ]
        
        for selector in selectors:
            tables = soup.select(selector)
            if tables:
                print(f"\n✓ セレクタ '{selector}' で {len(tables)} 個のテーブル発見")
                
                # 最初のテーブルのヘッダーを確認
                table = tables[0]
                headers = []
                
                # thead内のth/tdを探す
                thead = table.find('thead')
                if thead:
                    header_cells = thead.find_all(['th', 'td'])
                    headers = [cell.text.strip() for cell in header_cells if cell.text.strip()]
                
                # theadがない場合は最初のtrを確認
                if not headers:
                    first_row = table.find('tr')
                    if first_row:
                        header_cells = first_row.find_all(['th', 'td'])
                        headers = [cell.text.strip() for cell in header_cells if cell.text.strip()]
                
                if headers:
                    print(f"  ヘッダー: {headers[:15]}...")  # 最初の15個
        
        # JavaScriptで動的に生成されている可能性を確認
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'data' in script.string.lower():
                if 'json' in script.string.lower() or 'array' in script.string.lower():
                    print("\n✓ データを含む可能性のあるJavaScriptを検出")
                    break
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    # CSVファイルの確認
    check_npb_csv_files()
    
    # HTML直接分析
    analyze_fangraphs_html_directly()
    
    print("\n\n推奨アクション:")
    print("1. ブラウザでページを開き、実際のテーブルを確認")
    print("2. テーブル上で右クリック→「検証」でHTML構造を確認")
    print("3. Network タブで XHR/Fetch リクエストを確認")