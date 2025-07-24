#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBレポート生成＆Google Drive自動アップロード
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess

sys.path.append(str(Path(__file__).parent))

from scripts.oauth_drive_uploader import OAuthDriveUploader

def main():
    print("="*60)
    print("MLBレポート生成＆Google Driveアップロード")
    print("="*60)
    
    try:
        # 1. MLBレポート生成
        print("\n1. MLBレポートを生成中...")
        report_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"MLB_Report_{report_date}.txt"
        
        # レポート生成コマンド実行
        import platform
        encoding = 'cp932' if platform.system() == 'Windows' else 'utf-8'
        
        result = subprocess.run(
            [sys.executable, "scripts/mlb_complete_report_real.py"],
            capture_output=True,
            text=True,
            encoding=encoding
        )
        
        if result.returncode != 0:
            print(f"❌ レポート生成エラー")
            if result.stderr:
                print(f"エラー内容: {result.stderr}")
            return
        
        # 出力が空でないか確認
        if not result.stdout:
            print("❌ レポート生成結果が空です")
            return
        
        # クリーンなレポートを保存
        clean_content = result.stdout
        # ログ行を除去
        lines = clean_content.split('\n')
        clean_lines = []
        for line in lines:
            if ' - INFO - ' not in line and ' - DEBUG - ' not in line and not (line.strip().startswith('20') and ' - ' in line):
                clean_lines.append(line)
        clean_content = '\n'.join(clean_lines).strip()
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(clean_content)
        
        print(f"✅ レポート生成完了: {report_filename}")
        
        # レポートの最初の数行を表示
        preview_lines = clean_content.split('\n')[:10]
        print("\n--- レポートプレビュー ---")
        for line in preview_lines:
            print(line)
        print("...\n")
        
        # 2. Google Driveにアップロード
        print("2. Google Driveにアップロード中...")
        uploader = OAuthDriveUploader()
        
        # 設定からフォルダID取得
        import json
        with open('config/auto_report_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            folder_id = config.get('google_drive_folder_id')
        
        result = uploader.upload_file(report_filename, folder_id=folder_id)
        
        print("✅ アップロード成功！")
        print(f"   ファイル名: {result['name']}")
        print(f"   閲覧リンク: {result['webViewLink']}")
        
        # 3. ローカルファイルを保持（後で確認できるように）
        print(f"\n📁 ローカルファイル: {report_filename}")
        print("   （確認後、手動で削除してください）")
        
        print("\n✅ 全ての処理が完了しました！")
        print("Google Driveで確認してください。")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()