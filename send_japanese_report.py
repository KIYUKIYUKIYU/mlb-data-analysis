#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日本語MLBレポート - 完全独立版
既存システムを使わず、直接日本語でレポートを生成・送信
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
import requests
from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient

# チーム名辞書
TEAMS_JP = {
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

# 選手名辞書（主要選手のみ）
PLAYERS_JP = {
    "Shohei Ohtani": "大谷翔平",
    "Yoshinobu Yamamoto": "山本由伸",
    "Yu Darvish": "ダルビッシュ有",
    "Shota Imanaga": "今永昇太",
    "Masataka Yoshida": "吉田正尚",
    "Seiya Suzuki": "鈴木誠也",
    "Kodai Senga": "千賀滉大"
}

def to_jp(name, is_team=True):
    """名前を日本語に変換"""
    if is_team:
        return TEAMS_JP.get(name, name)
    else:
        return PLAYERS_JP.get(name, name)

def main():
    # 既存のdiscord_report_with_tableを実行
    from scripts.discord_report_with_table import DiscordReportWithTable
    
    # オリジナルのクラスを継承
    class JapaneseReport(DiscordReportWithTable):
        def format_game_for_discord(self, game):
            """ゲーム情報を日本語でフォーマット"""
            # 元のメソッドを呼び出し
            result = super().format_game_for_discord(game)
            
            # チーム名を日本語に変換
            home_team = game['teams']['home']['team'].get('name', 'Unknown')
            away_team = game['teams']['away']['team'].get('name', 'Unknown')
            
            home_jp = to_jp(home_team)
            away_jp = to_jp(away_team)
            
            # 結果の文字列を置換
            result = result.replace(f"【{home_team}】", f"【{home_jp}】")
            result = result.replace(f"【{away_team}】", f"【{away_jp}】")
            result = result.replace(f"**{away_team} @", f"**{away_jp} @")
            result = result.replace(f"@ {home_team}**", f"@ {home_jp}**")
            
            # 統計用語も日本語化
            result = result.replace("ERA:", "防御率:")
            result = result.replace("AVG:", "打率:")
            result = result.replace("Runs:", "得点:")
            result = result.replace("CL:", "守護神:")
            
            return result
    
    # 日本語版レポートを実行
    reporter = JapaneseReport()
    reporter.run()

if __name__ == "__main__":
    main()