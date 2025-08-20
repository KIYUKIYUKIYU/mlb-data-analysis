#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB自動配信スケジューラー
毎日21:00に自動実行
"""
import schedule
import time
import subprocess
import sys
from datetime import datetime
import pytz

def run_mlb_report():
    """MLBレポートを実行"""
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    
    print("\n" + "=" * 60)
    print(f"MLBレポート自動配信 - {now.strftime('%Y/%m/%d %H:%M:%S JST')}")
    print("=" * 60)
    
    try:
        # Pythonスクリプトを実行
        result = subprocess.run([
            sys.executable, 
            "-m", 
            "scripts.discord_report_with_table"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ レポート送信成功！")
        else:
            print("❌ エラーが発生しました:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    
    print("\n次回実行: 明日 21:00")
    print("=" * 60)

def main():
    """スケジューラーのメイン処理"""
    print("MLB自動配信スケジューラー起動")
    print("毎日21:00に自動実行します")
    print("停止: Ctrl+C")
    print("-" * 40)
    
    # 毎日21:00に実行
    schedule.every().day.at("21:00").do(run_mlb_report)
    
    # 初回は即実行（テスト用）
    print("\n初回実行（テスト）:")
    run_mlb_report()
    
    # スケジューラーループ
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1分ごとにチェック

if __name__ == "__main__":
    main()