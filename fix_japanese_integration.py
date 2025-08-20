#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
discord_report_with_table_jp.pyの修正
"""
import re

def fix_japanese_report():
    """load_dataをload_databaseに修正"""
    
    file_path = "scripts/discord_report_with_table_jp.py"
    
    try:
        # ファイルを読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # load_dataをload_databaseに修正
        content = content.replace('self.name_db.load_data()', 'self.name_db.load_database()')
        
        # ファイルを保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"修正完了: {file_path}")
        print("load_data() → load_database() に変更しました")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    fix_japanese_report()
    print("\n修正後、以下のコマンドで実行してください:")
    print("python -m scripts.discord_report_with_table_jp")