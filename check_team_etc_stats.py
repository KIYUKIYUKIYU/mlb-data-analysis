#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NF3のteam_etc.htmページを確認
"""

import requests
from bs4 import BeautifulSoup

def check_team_etc_page():
    """team_etc.htmの内容を確認"""
    url = "https://nf3.sakura.ne.jp/Stats/team_etc.htm"
    
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # タイトルを確認
            title = soup.find('title')
            if title:
                print(f"ページタイトル: {title.text}")
            
            # テーブルを確認
            tables = soup.find_all('table')
            print(f"\nテーブル数: {len(tables)}")
            
            # 各テーブルの内容を確認
            for i, table in enumerate(tables):
                print(f"\n=== テーブル{i} ===")
                
                # ヘッダーを確認
                headers = table.find_all('th')
                if headers:
                    print("ヘッダー:")
                    for j, header in enumerate(headers[:10]):
                        print(f"  [{j}] {header.text.strip()}")
                
                # 最初の数行を確認
                rows = table.find_all('tr')
                print(f"行数: {len(rows)}")
                
                for j, row in enumerate(rows[:5]):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        print(f"行{j}: ", end="")
                        for k, cell in enumerate(cells[:5]):
                            print(f"[{cell.text.strip()}] ", end="")
                        print()
            
            # リンクも確認
            links = soup.find_all('a')
            print(f"\nリンク数: {len(links)}")
            for link in links[:10]:
                href = link.get('href', '')
                text = link.text.strip()
                if text:
                    print(f"  {text} -> {href}")
    
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    check_team_etc_page()