#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
明日の全試合を日本語でDiscordに送信
"""
import os
import sys

# DISCORD_WEBHOOK_URLの確認
webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
if not webhook_url:
    print("エラー: DISCORD_WEBHOOK_URL が設定されていません")
    print("set DISCORD_WEBHOOK_URL=YOUR_WEBHOOK_URL")
    sys.exit(1)

print("日本語版レポートを実行中...")
print("=" * 50)

# 日本語化版を実行
from scripts.discord_report_with_table_jp import main

if __name__ == "__main__":
    main()
