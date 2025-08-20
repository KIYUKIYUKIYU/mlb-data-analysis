import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

class FanGraphsNPBTableExtractor:
    """FanGraphs NPBのテーブルデータを抽出"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def extract_tables(self, year=2024):
        """指定年のNPBデータテーブルを抽出"""
        url = f"https://www.fangraphs.com/leaders/international/npb?year={year}"
        print(f"=== FanGraphs NPB {year}年 データ抽出 ===")
        print(f"URL: {url}\n")
        
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # すべてのテーブルを取得
            tables = soup.find_all('table')
            print(f"発見されたテーブル数: {len(tables)}\n")
            
            extracted_data = {}
            
            for i, table in enumerate(tables):
                print(f"--- テーブル {i+1} ---")
                
                # テーブルのクラスやIDを確認
                table_class = table.get('class', [])
                table_id = table.get('id', '')
                print(f"クラス: {table_class}")
                print(f"ID: {table_id}")
                
                # pandasでテーブルを読み込む
                try:
                    df = pd.read_html(str(table))[0]
                    
                    # データフレームの情報
                    print(f"行数: {len(df)}")
                    print(f"列数: {len(df.columns)}")
                    print(f"カラム: {list(df.columns)[:20]}")  # 最初の20列
                    
                    # データが実際に含まれているか確認
                    if len(df) > 0:
                        # 最初の5行を表示
                        print("\nサンプルデータ（最初の5行）:")
                        print(df.head())
                        
                        # 重要な統計の存在確認
                        columns_str = ' '.join(str(col).upper() for col in df.columns)
                        
                        # 投手統計のチェック
                        pitcher_stats = ['ERA', 'FIP', 'XFIP', 'WHIP', 'K/9', 'BB/9', 'K-BB%', 'WAR']
                        pitcher_found = [stat for stat in pitcher_stats if stat in columns_str]
                        
                        # 打者統計のチェック
                        batter_stats = ['AVG', 'OBP', 'SLG', 'OPS', 'WOBA', 'WRC+', 'WAR']
                        batter_found = [stat for stat in batter_stats if stat in columns_str]
                        
                        if pitcher_found:
                            print(f"\n投手統計を検出: {pitcher_found}")
                            extracted_data['pitching'] = df
                        elif batter_found:
                            print(f"\n打者統計を検出: {batter_found}")
                            extracted_data['batting'] = df
                        
                        # データタイプを判定
                        if any(col in columns_str for col in ['ERA', 'IP', 'SO', 'BB']):
                            table_type = "投手"
                        elif any(col in columns_str for col in ['AVG', 'HR', 'RBI', 'SB']):
                            table_type = "打者"
                        else:
                            table_type = "不明"
                        
                        print(f"テーブルタイプ: {table_type}")
                        
                        # CSVとして保存
                        if table_type != "不明" and len(df) > 5:
                            filename = f"npb_{table_type}_{year}_table{i+1}.csv"
                            df.to_csv(filename, index=False, encoding='utf-8-sig')
                            print(f"保存: {filename}")
                    
                except Exception as e:
                    print(f"テーブル解析エラー: {e}")
                
                print()
            
            return extracted_data
            
        except Exception as e:
            print(f"エラー: {type(e).__name__}: {str(e)}")
            return None
    
    def check_multiple_years(self):
        """複数年のデータ可用性をチェック"""
        print("\n=== 複数年データチェック ===\n")
        
        years = [2024, 2023, 2022, 2021, 2020]
        available_years = []
        
        for year in years:
            url = f"https://www.fangraphs.com/leaders/international/npb?year={year}"
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tables = soup.find_all('table')
                    
                    # 実際のデータテーブルがあるか確認
                    data_tables = 0
                    for table in tables:
                        try:
                            df = pd.read_html(str(table))[0]
                            if len(df) > 5:  # 5行以上のデータがある
                                data_tables += 1
                        except:
                            pass
                    
                    if data_tables > 0:
                        print(f"✓ {year}年: {data_tables}個のデータテーブル")
                        available_years.append(year)
                    else:
                        print(f"× {year}年: データテーブルなし")
                else:
                    print(f"× {year}年: ステータス {response.status_code}")
                    
            except Exception as e:
                print(f"× {year}年: エラー")
            
            time.sleep(1)
        
        return available_years
    
    def analyze_column_mapping(self, df):
        """カラム名とMLBレポートの対応を分析"""
        print("\n=== カラムマッピング分析 ===")
        
        # MLBレポートで使用される指標とFanGraphsカラムの対応
        mapping = {
            # 投手基本
            'ERA': ['ERA', 'era'],
            'FIP': ['FIP', 'fip'],
            'xFIP': ['xFIP', 'xfip', 'XFIP'],
            'WHIP': ['WHIP', 'whip'],
            'K-BB%': ['K-BB%', 'K-BB', 'k-bb%'],
            
            # 投手詳細
            'GB%': ['GB%', 'gb%', 'GB'],
            'FB%': ['FB%', 'fb%', 'FB'],
            'SwStr%': ['SwStr%', 'swstr%', 'SwStr'],
            'BABIP': ['BABIP', 'babip'],
            
            # 打者基本
            'AVG': ['AVG', 'avg', 'BA'],
            'OBP': ['OBP', 'obp'],
            'SLG': ['SLG', 'slg'],
            'OPS': ['OPS', 'ops'],
            'wOBA': ['wOBA', 'woba', 'WOBA'],
            
            # 打者詳細
            'Barrel%': ['Barrel%', 'barrel%', 'Barrels'],
            'Hard%': ['Hard%', 'hard%', 'HardHit%'],
            'ISO': ['ISO', 'iso'],
            'WAR': ['WAR', 'war', 'fWAR']
        }
        
        found_mappings = {}
        columns = list(df.columns)
        
        for mlb_stat, possible_names in mapping.items():
            for col in columns:
                if any(name.lower() in col.lower() for name in possible_names):
                    found_mappings[mlb_stat] = col
                    break
        
        print("\n発見されたマッピング:")
        for mlb_stat, fangraphs_col in found_mappings.items():
            print(f"  {mlb_stat} → {fangraphs_col}")
        
        print("\n不足している統計:")
        missing = [stat for stat in mapping.keys() if stat not in found_mappings]
        for stat in missing:
            print(f"  × {stat}")
        
        return found_mappings

# 実行
if __name__ == "__main__":
    extractor = FanGraphsNPBTableExtractor()
    
    # 2024年のデータを抽出
    print("1. 2024年データの詳細抽出\n")
    data = extractor.extract_tables(2024)
    
    # 複数年のチェック
    print("\n2. 複数年のデータ可用性チェック")
    available_years = extractor.check_multiple_years()
    
    # カラムマッピング分析（データがある場合）
    if data:
        for data_type, df in data.items():
            print(f"\n3. {data_type}データのカラムマッピング")
            extractor.analyze_column_mapping(df)
    
    print("\n=== 完了 ===")
    print("\n次のステップ:")
    print("1. 保存されたCSVファイルを確認")
    print("2. 必要な統計が含まれているか検証")
    print("3. 不足している統計の代替案を検討")