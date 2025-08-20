#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBレポート日本語ラッパー
既存のレポートを実行して、出力を日本語に変換
"""
import subprocess
import sys
import re
from scripts.accurate_name_database import AccurateNameDatabase

# チーム名と選手名の変換辞書を直接定義
TEAM_NAMES_JP = {
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

def convert_to_japanese(text):
    """テキストを日本語に変換"""
    # チーム名を変換
    for eng, jp in TEAM_NAMES_JP.items():
        text = text.replace(f"【{eng}】", f"【{jp}】")
        text = text.replace(f"**{eng} @", f"**{jp} @")
        text = text.replace(f"@ {eng}**", f"@ {jp}**")
    
    # 統計用語を変換
    text = text.replace("ERA:", "防御率:")
    text = text.replace("AVG:", "打率:")
    text = text.replace("Runs:", "得点:")
    text = text.replace("CL:", "守護神:")
    text = text.replace("Team BA:", "チーム打率:")
    
    # 選手名（必要に応じて追加）
    text = text.replace("Shohei Ohtani", "大谷翔平")
    text = text.replace("Yoshinobu Yamamoto", "山本由伸")
    
    return text

def main():
    print("MLB日本語レポートを生成中...")
    print("=" * 50)
    
    # 元のスクリプトを実行
    result = subprocess.run(
        [sys.executable, "-m", "scripts.discord_report_with_table"],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    # 出力を取得
    output = result.stdout
    error = result.stderr
    
    if error:
        print("エラー:", error)
    
    # 日本語に変換
    if output:
        japanese_output = convert_to_japanese(output)
        print(japanese_output)
    
    # Discord送信部分は元のスクリプトが処理済み

if __name__ == "__main__":
    main()