#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NPBデータスクレイピング - テスト版
実際のサービスURLを確認するためのスクリプト
"""

import requests
from bs4 import BeautifulSoup
import os

def test_service_access():
    """サービスへのアクセスをテスト"""
    
    # 各サービスの公開ページをチェック
    services = {
        "1point02": [
            "https://1point02.jp/",
            "https://1point02.jp/op/",
            "https://www.1point02.jp/",
            "https://1point02.jp/login",
        ],
        "Baseball LAB": [
            "https://www.baseball-lab.jp/",
            "https://baseball-lab.jp/",
        ],
        "デルタ": [
            "https://deltagraphs.com/",
            "https://www.deltagraphs.com/",
        ],
        "データスタジアム": [
            "https://www.datastadium.co.jp/",
            "https://baseball.datastadium.jp/",
        ]
    }
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print("=== NPBデータサービス接続テスト ===\n")
    
    for service_name, urls in services.items():
        print(f"【{service_name}】")
        for url in urls:
            try:
                response = session.get(url, timeout=5, allow_redirects=True)
                print(f"  {url}")
                print(f"    ステータス: {response.status_code}")
                print(f"    最終URL: {response.url}")
                
                # ログインフォームを探す
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # ログインフォームの検出
                    login_forms = soup.find_all('form', {'action': lambda x: x and ('login' in x.lower() or 'signin' in x.lower())})
                    if login_forms:
                        print(f"    ログインフォーム: 検出")
                    
                    # パスワードフィールドの検出
                    password_fields = soup.find_all('input', {'type': 'password'})
                    if password_fields:
                        print(f"    パスワードフィールド: {len(password_fields)}個検出")
                
            except Exception as e:
                print(f"  {url}")
                print(f"    エラー: {e}")
        print()

def check_1point02_structure():
    """1point02の構造を詳しく調査"""
    print("\n=== 1point02 詳細調査 ===\n")
    
    # 可能性のあるURL
    test_urls = [
        "https://1point02.jp/",
        "https://1point02.jp/op/",
        "https://1point02.jp/op/gnav/",
        "https://1point02.jp/op/gnav/baseball/",
        "https://1point02.jp/member/",
        "https://1point02.jp/member/login/",
        "https://1point02.jp/users/sign_in",
        "https://1point02.jp/auth/login",
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    for url in test_urls:
        try:
            response = session.get(url, timeout=5, allow_redirects=True)
            print(f"URL: {url}")
            print(f"  ステータス: {response.status_code}")
            print(f"  最終URL: {response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # タイトルを取得
                title = soup.find('title')
                if title:
                    print(f"  タイトル: {title.text.strip()}")
                
                # ログイン関連の要素を探す
                login_elements = []
                
                # ログインリンク
                login_links = soup.find_all('a', href=lambda x: x and 'login' in x.lower())
                for link in login_links[:3]:  # 最初の3つ
                    login_elements.append(f"リンク: {link.get('href')}")
                
                # ログインフォーム
                forms = soup.find_all('form')
                for form in forms:
                    action = form.get('action', '')
                    if 'login' in action.lower() or 'signin' in action.lower():
                        login_elements.append(f"フォーム: {action}")
                
                if login_elements:
                    print("  ログイン要素:")
                    for elem in login_elements:
                        print(f"    - {elem}")
            
            print()
            
        except requests.exceptions.RequestException as e:
            print(f"URL: {url}")
            print(f"  エラー: {type(e).__name__}")
            print()

def create_simple_scraper():
    """シンプルなスクレイパーの例"""
    print("\n=== 手動でのデータ取得例 ===\n")
    print("1. ブラウザで1point02にログイン")
    print("2. F12で開発者ツールを開く")
    print("3. Networkタブを開く")
    print("4. データページにアクセス")
    print("5. リクエストヘッダーからCookieをコピー")
    print("")
    print("以下のようなコードで使用:")
    print("-" * 50)
    print("""
import requests
from bs4 import BeautifulSoup

# ブラウザからコピーしたCookie
cookies = {
    'session_id': 'your_session_id_here',
    # 他のCookieも追加
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://1point02.jp/'
}

# データページにアクセス
url = 'https://1point02.jp/op/gnav/baseball/stats/player/XXX'
response = requests.get(url, cookies=cookies, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    # データ抽出処理
else:
    print(f"アクセス失敗: {response.status_code}")
    """)

def main():
    """メイン処理"""
    print("NPBデータサービス接続テスト\n")
    
    # 各サービスへのアクセステスト
    test_service_access()
    
    # 1point02の詳細調査
    check_1point02_structure()
    
    # 手動取得の案内
    create_simple_scraper()
    
    print("\n" + "=" * 50)
    print("実際のログインURLが分かったら、")
    print("そのURLとログインフォームの構造を教えてください。")
    print("=" * 50)

if __name__ == "__main__":
    main()