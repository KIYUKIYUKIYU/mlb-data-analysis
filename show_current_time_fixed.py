#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
時刻対応MLBレポートシステム（修正版）
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
import subprocess

def get_next_game_date():
    """次の試合日を取得（日本時間基準）"""
    # 日本時間の現在時刻
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst)
    
    print("=" * 50)
    print(f"現在の日本時間: {now_jst.strftime('%Y年%m月%d日(%a) %H:%M:%S')}")
    print("=" * 50)
    
    # 21:00を基準に判定
    cutoff_time = now_jst.replace(hour=21, minute=0, second=0, microsecond=0)
    
    if now_jst.hour < 9:  # 午前9時前（MLBナイトゲームがまだ終わってない）
        # 昨日の試合結果
        target_date = (now_jst - timedelta(days=1)).date()
        print(f"午前9時前なので、昨日（{target_date.strftime('%m/%d')}）の試合結果を取得します")
    elif now_jst < cutoff_time:
        # 9:00-21:00は今日の試合
        target_date = now_jst.date()
        print(f"本日（{target_date.strftime('%m/%d')}）の試合予定を取得します")
    else:
        # 21:00以降は明日の試合
        target_date = (now_jst + timedelta(days=1)).date()
        print(f"21:00以降なので、明日（{target_date.strftime('%m/%d')}）の試合予定を取得します")
    
    # 日本時間とMLB時間の差を考慮（約13-14時間）
    # 日本の日付から1日引く（MLBの試合は日本時間の翌日早朝に終わる）
    mlb_date = target_date - timedelta(days=1)
    
    print(f"\nMLBスケジュール日付: {mlb_date.strftime('%Y-%m-%d')}")
    
    return mlb_date.strftime('%Y-%m-%d')

def main():
    """メイン処理"""
    # 次の試合日を取得
    target_date = get_next_game_date()
    
    # 環境変数にセット（オプション）
    os.environ['MLB_TARGET_DATE'] = target_date
    
    print(f"\n{target_date}の試合データを取得します...")
    print("\n既存のレポートシステムを実行中...")
    
    # 既存のdiscord_report_with_tableを実行
    try:
        result = subprocess.run([
            sys.executable,
            "-m",
            "scripts.discord_report_with_table"
        ], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("エラー出力:", result.stderr)
            
    except Exception as e:
        print(f"実行エラー: {e}")
        print("\n代替実行方法:")
        print("python -m scripts.discord_report_with_table")

if __name__ == "__main__":
    main()