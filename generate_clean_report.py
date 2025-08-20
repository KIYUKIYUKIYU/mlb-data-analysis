#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
クリーンなMLBレポートを生成してGoogle Driveに保存
"""

import subprocess
import sys
import os
from datetime import datetime
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

class CleanReportGenerator:
    def __init__(self):
        self.report_dir = "reports"
        os.makedirs(self.report_dir, exist_ok=True)
        
    def generate_clean_report(self, output_filename=None):
        """クリーンなレポートを生成"""
        if not output_filename:
            date_str = datetime.now().strftime("%Y%m%d")
            output_filename = f"MLB_Report_{date_str}.txt"
        
        output_path = os.path.join(self.report_dir, output_filename)
        
        print(f"レポートを生成中... → {output_filename}")
        
        # レポートを生成（エラー出力を完全に抑制）
        try:
            # mlb_complete_report_real.pyを実行
            result = subprocess.run(
                [sys.executable, "scripts/mlb_complete_report_real.py"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                print(f"エラー: レポート生成に失敗しました")
                print(result.stderr)
                return None
            
            # 出力をクリーンアップ
            clean_content = self.clean_output(result.stdout)
            
            # ファイルに保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            print(f"✓ クリーンレポート生成完了: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"エラー: {e}")
            return None
    
    def clean_output(self, content):
        """デバッグ出力を削除"""
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            # INFO行をスキップ
            if ' - INFO - ' in line:
                continue
            # タイムスタンプで始まる行をスキップ
            if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line):
                continue
            # DEBUG行をスキップ
            if ' - DEBUG - ' in line or 'Debug - ' in line:
                continue
            
            clean_lines.append(line)
        
        # 連続する空行を1つにまとめる
        result = '\n'.join(clean_lines)
        result = re.sub(r'\n\n\n+', '\n\n', result)
        
        return result.strip()
    
    def upload_to_google_drive(self, file_path, folder_id=None):
        """Google Driveにアップロード"""
        try:
            # 認証情報ファイルのパス
            credentials_path = 'credentials/google_drive_credentials.json'
            
            if not os.path.exists(credentials_path):
                print("Google Drive認証ファイルが見つかりません")
                print(f"場所: {credentials_path}")
                self.show_google_drive_setup()
                return None
            
            # 認証
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            # ファイル名
            file_name = os.path.basename(file_path)
            
            # メタデータ
            file_metadata = {
                'name': file_name,
                'mimeType': 'text/plain'
            }
            
            # フォルダIDが指定されている場合
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # アップロード
            media = MediaFileUpload(
                file_path,
                mimetype='text/plain',
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            print(f"\n✓ Google Driveにアップロード完了")
            print(f"  ファイルID: {file.get('id')}")
            print(f"  閲覧リンク: {file.get('webViewLink')}")
            
            return file.get('id')
            
        except HttpError as error:
            print(f"Google Drive APIエラー: {error}")
            return None
        except Exception as e:
            print(f"アップロードエラー: {e}")
            return None
    
    def show_google_drive_setup(self):
        """Google Drive設定方法を表示"""
        print("\n" + "="*60)
        print("Google Drive API設定方法")
        print("="*60)
        print("""
1. Google Cloud Consoleにアクセス
   https://console.cloud.google.com/

2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）

3. Google Drive APIを有効化
   - APIとサービス → ライブラリ
   - "Google Drive API"を検索して有効化

4. サービスアカウントを作成
   - APIとサービス → 認証情報
   - "+ 認証情報を作成" → サービスアカウント
   - 名前を入力して作成

5. キーを作成
   - 作成したサービスアカウントをクリック
   - "キー"タブ → "鍵を追加" → "新しい鍵を作成"
   - JSON形式を選択してダウンロード

6. ダウンロードしたJSONファイルを以下に配置:
   credentials/google_drive_credentials.json

7. （オプション）特定のフォルダにアップロードする場合:
   - Google Driveでフォルダを作成
   - サービスアカウントのメールアドレスに共有権限を付与
   - フォルダIDをコピー（URLの/folders/以降の部分）
""")
        print("="*60)

def main():
    """メイン処理"""
    generator = CleanReportGenerator()
    
    # クリーンレポートを生成
    report_path = generator.generate_clean_report()
    
    if report_path:
        # ローカルで開く
        os.system(f'notepad {report_path}')
        
        # Google Driveにアップロードするか確認
        upload = input("\nGoogle Driveにアップロードしますか？ (y/n): ")
        
        if upload.lower() == 'y':
            # フォルダIDを入力（オプション）
            folder_id = input("フォルダID (Enterでスキップ): ").strip()
            if not folder_id:
                folder_id = None
            
            generator.upload_to_google_drive(report_path, folder_id)

if __name__ == "__main__":
    main()