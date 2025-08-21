#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTMLレポートをPDFに変換するスクリプト（Chrome指定版）
"""
import os
import sys
from pathlib import Path
import subprocess
import time

def open_with_chrome(html_file_path):
    """ChromeでHTMLファイルを自動的に開く"""
    html_path = Path(html_file_path).resolve()
    
    # 出力ディレクトリを作成
    output_dir = html_path.parent.parent / "pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Chromeの実行パスリスト（一般的な場所）
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    
    # Chromeを探す
    chrome_exe = None
    for path in chrome_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            chrome_exe = expanded_path
            print(f"✅ Chrome found: {chrome_exe}")
            break
    
    if not chrome_exe:
        # デフォルトのchromeコマンドを試す
        chrome_exe = "chrome"
        print("⚠️ Chrome.exeが見つからないため、デフォルトコマンドを使用")
    
    print("=" * 60)
    print("📄 ChromeでHTMLを開いてPDFに変換")
    print("=" * 60)
    print()
    print(f"HTMLファイル: {html_path}")
    print()
    
    try:
        # Chromeで開く
        subprocess.Popen([chrome_exe, str(html_path)])
        print("✅ Chromeでファイルを開きました！")
        print()
        print("📝 PDF保存の手順:")
        print("   1. Chromeが開いたら Ctrl+P を押す")
        print("   2. 送信先で「PDFに保存」を選択")
        print(f"   3. 保存先: {output_dir}")
        print(f"   4. ファイル名: {html_path.stem}.pdf")
        print()
        print("=" * 60)
        
    except FileNotFoundError:
        # startコマンドで試す（Windows）
        try:
            os.system(f'start chrome "{html_path}"')
            print("✅ Chromeで開きました（startコマンド使用）")
        except:
            # 最終手段：デフォルトブラウザで開く
            os.startfile(str(html_path))
            print("✅ デフォルトブラウザで開きました")
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("手動でファイルを開いてください")

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_to_pdf.py <html_file>")
        print("Example: python convert_to_pdf.py daily_reports/html/MLB08月22日(金)レポート.html")
        sys.exit(1)
    
    html_file = sys.argv[1]
    
    if not os.path.exists(html_file):
        print(f"❌ File not found: {html_file}")
        sys.exit(1)
    
    open_with_chrome(html_file)

if __name__ == "__main__":
    main()