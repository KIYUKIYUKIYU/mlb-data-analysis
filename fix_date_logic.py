#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日付ロジックの修正
"""
from datetime import datetime, timedelta
import pytz

def test_date_logic():
    """現在の日付ロジックをテスト"""
    jst = pytz.timezone('Asia/Tokyo')
    est = pytz.timezone('US/Eastern')
    
    # 現在の日本時間
    now_jst = datetime.now(jst)
    print(f"現在の日本時間: {now_jst.strftime('%Y/%m/%d(%a) %H:%M')}")
    
    # 今日の日付
    today_jst = now_jst.date()
    print(f"日本の今日: {today_jst}")
    
    # アメリカ東部の現在時刻
    now_est = now_jst.astimezone(est)
    print(f"アメリカ東部時間: {now_est.strftime('%Y/%m/%d(%a) %H:%M')}")
    
    # MLBの試合は通常アメリカの日付で行われる
    # 日本時間の17:00は、アメリカ東部の朝4:00頃
    # つまり、アメリカではまだ前日
    
    print("\n正しいロジック:")
    print(f"1. 日本時間で「明日」の試合を見たい場合")
    print(f"   → 日本の明日（6/23）の朝に行われる試合")
    print(f"   → アメリカでは6/22の夜の試合")
    
    # 正しい日付
    tomorrow_jst = today_jst + timedelta(days=1)
    target_date_est = today_jst  # 日本の今日 = アメリカの今日または昨日
    
    print(f"\n取得すべき日付: {target_date_est} (アメリカの試合日)")
    
test_date_logic()