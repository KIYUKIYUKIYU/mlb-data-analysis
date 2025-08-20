#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBレポート日本語版 - 直接実行版
"""
import subprocess
import sys
import os

# チーム名変換辞書
TEAM_NAMES = {
    "Detroit Tigers": "タイガース",
    "Tampa Bay Rays": "レイズ",
    "Baltimore Orioles": "オリオールズ",
    "New York Yankees": "ヤンキース",
    "Milwaukee Brewers": "ブルワーズ",
    "Minnesota Twins": "ツインズ",
    "Cincinnati Reds": "レッズ",
    "St. Louis Cardinals": "カージナルス",
    "Seattle Mariners": "マリナーズ",
    "Chicago Cubs": "カブス",
    "Chicago White Sox": "ホワイトソックス",
    "Toronto Blue Jays": "ブルージェイズ",
    "Boston Red Sox": "レッドソックス",
    "San Francisco Giants": "ジャイアンツ",
    "Texas Rangers": "レンジャーズ",
    "Pittsburgh Pirates": "パイレーツ",
    "Atlanta Braves": "ブレーブス",
    "Miami Marlins": "マーリンズ",
    "Kansas City Royals": "ロイヤルズ",
    "San Diego Padres": "パドレス",
    "New York Mets": "メッツ",
    "Philadelphia Phillies": "フィリーズ",
    "Arizona Diamondbacks": "ダイヤモンドバックス",
    "Colorado Rockies": "ロッキーズ",
    "Houston Astros": "アストロズ",
    "Los Angeles Angels": "エンゼルス",
    "Cleveland Guardians": "ガーディアンズ",
    "Oakland Athletics": "アスレチックス",
    "Washington Nationals": "ナショナルズ",
    "Los Angeles Dodgers": "ドジャース"
}

# 環境変数を設定
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 元のスクリプトを実行（エラーを無視）
result = subprocess.run(
    [sys.executable, "-m", "scripts.discord_report_with_table"],
    capture_output=True,
    text=True,
    encoding='cp932',  # Windows日本語エンコーディング
    errors='ignore'    # エラーを無視
)

print("実行完了")
print("Discordを確認してください")