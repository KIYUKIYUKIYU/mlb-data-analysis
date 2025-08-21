#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive アップロードスクリプト（既存ファイル更新版）
"""
import os
import sys
import json
import glob
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def upload_to_drive(file_path):
    """Google Driveの既存ファイルを更新"""
    
    # 環境変数から認証情報を取得
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    
    if not creds_json:
        print("❌ Error: GOOGLE_CREDENTIALS not found")
        return False
    
    if not folder_id:
        print("❌ Error: GOOGLE_DRIVE_FOLDER_ID not found")
        return False
    
    try:
        # 認証情報をパース
        creds_dict = json.loads(creds_json)
        
        # サービスアカウント認証
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        # Drive APIサービスを構築
        service = build('drive', 'v3', credentials=creds)
        
        # ファイル名を取得
        file_name = os.path.basename(file_path)
        
        print(f"🔍 Searching for existing file: {file_name}")
        
        # 既存ファイルを検索
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            # 既存ファイルを更新
            file_id = files[0]['id']
            print(f"📝 Updating existing file: {file_name} (ID: {file_id})")
            
            media = MediaFileUpload(
                file_path,
                mimetype='text/plain',
                resumable=True
            )
            
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True,
                fields='id, name, webViewLink'
            ).execute()
            
            print(f"✅ File updated successfully!")
            print(f"   Name: {updated_file.get('name')}")
            print(f"   Link: {updated_file.get('webViewLink')}")
            return True
            
        else:
            # ファイルが見つからない場合
            print(f"⚠️ File not found: {file_name}")
            print("📋 Please create the file manually in Google Drive first:")
            print(f"   1. Go to MLB_Reports folder")
            print(f"   2. Create a new text file named: {file_name}")
            print(f"   3. Share it with: mlb-report-uploader@mlb-report-system.iam.gserviceaccount.com")
            print(f"   4. Run this script again")
            
            # 固定ファイル名の代替案を試す
            fixed_name = "MLB_Latest_Report.txt"
            print(f"\n🔄 Trying fixed filename: {fixed_name}")
            
            query_fixed = f"name='{fixed_name}' and '{folder_id}' in parents and trashed=false"
            results_fixed = service.files().list(
                q=query_fixed,
                fields="files(id, name)",
                supportsAllDrives=True
            ).execute()
            
            files_fixed = results_fixed.get('files', [])
            
            if files_fixed:
                file_id = files_fixed[0]['id']
                print(f"📝 Found fixed file, updating: {fixed_name}")
                
                media = MediaFileUpload(
                    file_path,
                    mimetype='text/plain',
                    resumable=True
                )
                
                updated_file = service.files().update(
                    fileId=file_id,
                    media_body=media,
                    supportsAllDrives=True,
                    fields='id, name, webViewLink'
                ).execute()
                
                print(f"✅ Fixed file updated successfully!")
                print(f"   Link: {updated_file.get('webViewLink')}")
                return True
            
            return False
            
    except HttpError as e:
        print(f"❌ HTTP Error: {e}")
        if "storageQuotaExceeded" in str(e):
            print("💡 This is a service account limitation.")
            print("   Please create the file manually in Google Drive first.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("Google Drive Upload Script (Update Mode)")
    print("=" * 60)
    
    # daily_reportsフォルダの最新ファイルを取得
    reports = glob.glob("daily_reports/MLB*.txt")
    
    if not reports:
        print("❌ No MLB report files found")
        sys.exit(1)
    
    # 最新のファイルを選択
    latest_report = max(reports, key=os.path.getctime)
    print(f"📄 Found report: {latest_report}")
    
    # アップロード実行
    if upload_to_drive(latest_report):
        print("\n🎉 Upload completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Upload failed - manual intervention needed")
        sys.exit(1)

if __name__ == "__main__":
    main()