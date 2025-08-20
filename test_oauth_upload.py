#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive OAuth認証テスト
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from scripts.oauth_drive_uploader import OAuthDriveUploader

def main():
    print("="*60)
    print("Google Drive OAuth認証テスト")
    print("="*60)
    
    try:
        # OAuth認証でGoogle Drive接続
        print("\n1. Google Drive API接続中（OAuth認証）...")
        uploader = OAuthDriveUploader()
        print("✅ 接続成功！")
        
        # テストファイル作成
        print("\n2. テストファイル作成中...")
        test_content = f"OAuth認証テスト\n実行日時: {datetime.now()}"
        test_file = "oauth_test.txt"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"✅ ファイル作成: {test_file}")
        
        # フォルダID取得
        import json
        with open('config/auto_report_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            folder_id = config.get('google_drive_folder_id')
        
        print(f"\n使用するフォルダID: {folder_id}")
        
        # アップロード
        print("\n3. Google Driveにアップロード中...")
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