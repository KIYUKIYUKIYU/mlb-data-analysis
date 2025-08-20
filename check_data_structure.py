#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
データ構造を確認
"""
import sys
sys.path.append('.')

from scripts.discord_report_with_table_jp import DiscordReportWithTable

# インスタンスを作成
reporter = DiscordReportWithTable()

# 明日の試合を取得
from datetime import datetime, timedelta
tomorrow = datetime.now() + timedelta(days=1)
games = reporter.client.get_games_by_date(tomorrow.strftime('%Y-%m-%d'))

if games:
    # 最初の試合のデータ構造を確認
    game = games[0]
    print("元のゲームデータ構造:")
    print(f"away team: {game['teams']['away']['team']['name']}")
    print(f"home team: {game['teams']['home']['team']['name']}")
    
    # to_japanese_teamメソッドが存在するか確認
    if hasattr(reporter, 'to_japanese_team'):
        print("\nto_japanese_teamメソッドあり")
        print(f"変換後 away: {reporter.to_japanese_team(game['teams']['away']['team']['name'])}")
        print(f"変換後 home: {reporter.to_japanese_team(game['teams']['home']['team']['name'])}")
    else:
        print("\nto_japanese_teamメソッドなし！")