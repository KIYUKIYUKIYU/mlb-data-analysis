#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
既存のdiscord_report_with_table.pyに日本語化機能を追加する統合スクリプト
"""
import shutil
from pathlib import Path
import re

def integrate_japanese_to_discord_report():
    """既存のレポートに日本語化を統合"""
    
    # ファイルパス
    original_file = Path("scripts/discord_report_with_table.py")
    backup_file = Path("scripts/discord_report_with_table_backup.py")
    japanese_file = Path("scripts/discord_report_with_table_jp.py")
    
    # バックアップ作成
    if original_file.exists():
        shutil.copy(original_file, backup_file)
        print(f"バックアップ作成: {backup_file}")
    
    # 既存ファイルを読み込み（UTF-8で強制）
    try:
        with open(original_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"エラー: {e}")
        return
    
    # インポート部分を見つけて日本語化モジュールを追加
    import_pattern = r'(from dotenv import load_dotenv)'
    import_addition = r'\1\nfrom scripts.accurate_name_database import AccurateNameDatabase'
    
    content = re.sub(import_pattern, import_addition, content)
    
    # __init__メソッドに日本語化DBの初期化を追加
    init_pattern = r'(def __init__\(self\):.*?self\.pbp_cache = \{\})'
    init_addition = r'\1\n        # 日本語化データベースを初期化\n        self.name_db = AccurateNameDatabase()\n        self.name_db.load_data()'
    
    content = re.sub(init_pattern, init_addition, content, flags=re.DOTALL)
    
    # 日本語変換メソッドを追加
    conversion_methods = '''
    def to_japanese_team(self, team_name):
        """チーム名を日本語に変換"""
        return self.name_db.get_team_name_jp(team_name)
    
    def to_japanese_player(self, player_name):
        """選手名を日本語に変換"""
        return self.name_db.get_player_name_jp(player_name)
    
    def to_japanese_stat(self, stat_name):
        """統計用語を日本語に変換"""
        stat_dict = {
            "ERA": "防御率",
            "FIP": "FIP",
            "WHIP": "WHIP",
            "K%": "奪三振率",
            "BB%": "与四球率",
            "K-BB%": "K-BB%",
            "GB%": "ゴロ率",
            "FB%": "フライ率",
            "QS": "QS",
            "vs L": "対左",
            "vs R": "対右",
            "AVG": "打率",
            "OPS": "OPS",
            "Runs": "得点",
            "HR": "本塁打"
        }
        return stat_dict.get(stat_name, stat_name)
'''
    
    # クラスの最後にメソッドを追加
    class_end_pattern = r'(class DiscordReportWithTable:.*?)(\n\nif __name__)'
    content = re.sub(class_end_pattern, r'\1' + conversion_methods + r'\2', content, flags=re.DOTALL)
    
    # レポート生成部分でチーム名と選手名を変換
    # format_pitcher_line内での変換
    content = re.sub(
        r'(pitcher_name = game.*?get\([\'"]fullName[\'"]\))',
        r'\1\n            pitcher_name = self.to_japanese_player(pitcher_name) if pitcher_name else "未定"',
        content
    )
    
    # チーム名の変換
    content = re.sub(
        r'(home_team = game.*?get\([\'"]name[\'"]\))',
        r'\1\n        home_team = self.to_japanese_team(home_team) if home_team else home_team',
        content
    )
    
    content = re.sub(
        r'(away_team = game.*?get\([\'"]name[\'"]\))',
        r'\1\n        away_team = self.to_japanese_team(away_team) if away_team else away_team',
        content
    )
    
    # 新しいファイルとして保存
    with open(japanese_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"日本語化版を作成: {japanese_file}")
    
    # 簡易実行スクリプトも作成
    create_run_script()

def create_run_script():
    """実行用スクリプトを作成"""
    run_script = '''#!/usr/bin/env python
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
'''
    
    with open("run_tomorrow_jp.py", 'w', encoding='utf-8') as f:
        f.write(run_script)
    
    print("実行スクリプトを作成: run_tomorrow_jp.py")

if __name__ == "__main__":
    print("既存レポートに日本語化を統合します...")
    integrate_japanese_to_discord_report()
    print("\n完了！")
    print("\n実行方法:")
    print("python run_tomorrow_jp.py")