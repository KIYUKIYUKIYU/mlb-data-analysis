#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
時刻対応MLBレポートシステム
現在時刻を確認して、適切な日付の試合を取得
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz

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
    
    if now_jst < cutoff_time:
        # 21:00前なら今日の試合（アメリカ時間では昨日）
        target_date = now_jst.date()
        print(f"21:00前なので、今日（{target_date.strftime('%m/%d')}）の試合を取得します")
    else:
        # 21:00以降なら明日の試合
        target_date = (now_jst + timedelta(days=1)).date()
        print(f"21:00以降なので、明日（{target_date.strftime('%m/%d')}）の試合を取得します")
    
    # MLBはアメリカ東部時間なので、適切な日付に変換
    est = pytz.timezone('US/Eastern')
    
    # 日本の日付をアメリカ東部時間に変換
    jst_midnight = jst.localize(datetime.combine(target_date, datetime.min.time()))
    est_date = jst_midnight.astimezone(est)
    
    # アメリカの日付を取得
    mlb_date = est_date.date()
    
    print(f"\nMLB APIに渡す日付: {mlb_date.strftime('%Y-%m-%d')}")
    print(f"（アメリカ東部時間の{mlb_date.strftime('%m/%d')}の試合）")
    
    return mlb_date.strftime('%Y-%m-%d')

def main():
    """メイン処理"""
    # 次の試合日を取得
    target_date = get_next_game_date()
    
    # 既存のレポートシステムを実行
    print(f"\n{target_date}の試合データを取得中...")
    
    # discord_report_with_tableを日付指定で実行
    from scripts.discord_report_with_table import DiscordReportWithTable
    
    class DateAwareReport(DiscordReportWithTable):
        def run_discord_report(self):
            """指定日付でレポートを実行"""
            # 元のメソッドをオーバーライド
            games = self.client.get_schedule(target_date)
            
            if not games:
                print(f"{target_date}の試合はありません")
                return
                
            # 以降は元の処理を実行
            super().run_discord_report()
    
    # 実行
    system = DateAwareReport()
    system.run_discord_report()

if __name__ == "__main__":
    main()