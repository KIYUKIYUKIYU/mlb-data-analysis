#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBレポート生成＆Google Driveアップロード統合スクリプト
"""

import os
import sys
from datetime import datetime, timedelta
import pytz

# プロジェクトのルートディレクトリをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.mlb_complete_report_real import generate_report
from scripts.oauth_drive_uploader import OAuthDriveUploader

def main():
    print("=" * 60)
    print("MLBレポート生成＆Google Driveアップロード")
    print("=" * 60)
    
    # 日本時間で翌日の日付を取得
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst)
    # 翌日の日付（試合開催日）
    game_date = now_jst + timedelta(days=1)
    
    # 曜日を日本語で
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekday = weekdays[game_date.weekday()]
    
    # ファイル名を日本語形式に（曜日付き）
    filename = f"MLB{game_date.strftime('%m月%d日')}({weekday})レポート.txt"
    
    print("1. MLBレポートを生成中...")
    
    try:
        # レポートを生成してファイルに保存
        report_content = generate_report()
        
        # ファイルに保存（UTF-8エンコーディング）
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ レポート生成完了: {filename}")
        
        # レポートの最初の5行を表示
        lines = report_content.split('\n')[:5]
        print("--- レポートプレビュー ---")
        for line in lines:
            print(line)
        print("...")
        
    except Exception as e:
        print(f"❌ レポート生成エラー: {e}")
        return 1
    
    print("\n2. Google Driveにアップロード中...")
    
    try:
        # Google Driveアップローダーを初期化
        uploader = OAuthDriveUploader()
        
        # ファイルをアップロード
        file_id = uploader.upload_file(filename)
        
        if file_id:
            print(f"✅ アップロード成功！")
            print(f"📁 ファイル名: {filename}")
            print(f"🔗 ファイルID: {file_id}")
            print(f"📍 保存先: Google Drive/MLB_Reports/")
        else:
            print("❌ アップロードに失敗しました")
            return 1
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1
    
    print("\n✨ 処理完了！")
    return 0

if __name__ == "__main__":
    sys.exit(main())