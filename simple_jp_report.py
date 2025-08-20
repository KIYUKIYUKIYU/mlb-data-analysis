#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
シンプル日本語変換スクリプト
"""
import subprocess
import sys

# チーム名辞書
TEAMS = {
    "Tigers": "タイガース",
    "Rays": "レイズ", 
    "Orioles": "オリオールズ",
    "Yankees": "ヤンキース",
    "Brewers": "ブルワーズ",
    "Twins": "ツインズ",
    "Reds": "レッズ",
    "Cardinals": "カージナルス",
    "Mariners": "マリナーズ",
    "Cubs": "カブス",
    "White Sox": "ホワイトソックス",
    "Blue Jays": "ブルージェイズ",
    "Red Sox": "レッドソックス",
    "Giants": "ジャイアンツ",
    "Rangers": "レンジャーズ",
    "Pirates": "パイレーツ",
    "Braves": "ブレーブス",
    "Marlins": "マーリンズ",
    "Royals": "ロイヤルズ",
    "Padres": "パドレス",
    "Mets": "メッツ",
    "Phillies": "フィリーズ",
    "Diamondbacks": "ダイヤモンドバックス",
    "Rockies": "ロッキーズ",
    "Astros": "アストロズ",
    "Angels": "エンゼルス",
    "Guardians": "ガーディアンズ",
    "Athletics": "アスレチックス",
    "Nationals": "ナショナルズ",
    "Dodgers": "ドジャース"
}

print("MLBレポートを実行中...")
print("完了後、Discordで日本語チーム名を確認してください")
print("=" * 50)

# 元のスクリプトを実行
subprocess.run([sys.executable, "-m", "scripts.discord_report_with_table"])

print("\n実行完了！")
print("Discordをチェックしてください")