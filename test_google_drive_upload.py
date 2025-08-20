#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive接続テストスクリプト（簡易版）
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# プロジェクトパスを追加
sys.path.append(str(Path(__file__).parent))

from scripts.google_drive_uploader import GoogleDriveUploader

def main():
    print("="*60)
    print("Google Drive接続テスト")
    print("="*60)
    
    try:
        # Google Drive接続
        print("\n1. Google Drive API接続中...")
        uploader = GoogleDriveUploader()
        print("✅ 接続成功！")
        
        # テストファイル作成
        print("\n2. テストファイル作成中...")
        test_content = f"テスト実行日時: {datetime.now()}"
        test_file = "test_upload.txt"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"✅ ファイル作成: {test_file}")
        
        # アップロード
        print("\n3. Google Driveにアップロード中...")
        import json
        with open('config/auto_report_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            folder_id = config.get('google_drive_folder_id')
        
        result = uploader.upload_file(test_file, folder_id=folder_id)
        print("✅ アップロード成功！")
        print(f"   ファイルID: {result['id']}")
        print(f"   閲覧リンク: {result['webViewLink']}")
        
        # クリーンアップ
        os.remove(test_file)
        print("\n✅ テスト完了！")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()