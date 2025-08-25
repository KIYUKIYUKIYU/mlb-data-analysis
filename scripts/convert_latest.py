#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最新のMLBレポートを自動的に見つけてHTML/PDF変換するスクリプト
"""
import os
import sys
import glob
from datetime import datetime

def find_latest_report():
    """最新のMLBレポートを見つける"""
    reports = glob.glob("daily_reports/MLB*.txt")
    
    if not reports:
        print("❌ エラー: MLBレポートが見つかりません")
        print("まず以下を実行してください:")
        print("python scripts/mlb_complete_report_real.py")
        return None
    
    # 最新のファイルを取得（作成日時でソート）
    latest = max(reports, key=os.path.getctime)
    return latest

def main():
    """メイン処理"""
    print("=" * 60)
    print("最新MLBレポートの自動変換")
    print("=" * 60)
    
    # 最新レポートを探す
    latest_report = find_latest_report()
    
    if not latest_report:
        sys.exit(1)
    
    print(f"\n📄 対象ファイル: {latest_report}")
    print(f"   作成日時: {datetime.fromtimestamp(os.path.getctime(latest_report)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # HTML変換
    print("\n🌐 HTML変換中...")
    os.system(f'python scripts/convert_to_html.py "{latest_report}"')
    
    # HTMLファイルを探す
    html_files = glob.glob("daily_reports/html/MLB*.html")
    if html_files:
        latest_html = max(html_files, key=os.path.getctime)
        print(f"✅ HTML生成完了: {latest_html}")
        
        # PDF変換するか確認
        response = input("\n📑 PDF変換もしますか? (y/n): ")
        if response.lower() == 'y':
            print("\nPDF変換を開始します...")
            os.system(f'python scripts/convert_to_pdf.py "{latest_html}"')
    
    print("\n" + "=" * 60)
    print("処理完了！")
    print("=" * 60)

if __name__ == "__main__":
    main()