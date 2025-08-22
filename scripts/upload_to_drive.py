#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive アップロードスクリプト（既存ファイル更新版）
テキスト、HTML、PDF全形式対応
"""
import os
import sys
import json
import glob
import argparse
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

def get_mime_type(file_path):
    """ファイル拡張子からMIMEタイプを取得"""
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.txt': 'text/plain',
        '.html': 'text/html',
        '.pdf': 'application/pdf'
    }
    return mime_types.get(ext, 'application/octet-stream')

def upload_file_to_drive(service, file_path, folder_id, fixed_filename=None):
    """個別ファイルをGoogle Driveにアップロード"""
    
    file_name = os.path.basename(file_path)
    mime_type = get_mime_type(file_path)
    
    print(f"🔍 Searching for existing file: {file_name}")
    
    # 既存ファイルを検索（日付付きファイル名）
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
            mimetype=mime_type,
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
        
    elif fixed_filename:
        # 固定ファイル名で再試行
        print(f"⚠️ File not found: {file_name}")
        print(f"🔄 Trying fixed filename: {fixed_filename}")
        
        query_fixed = f"name='{fixed_filename}' and '{folder_id}' in parents and trashed=false"
        results_fixed = service.files().list(
            q=query_fixed,
            fields="files(id, name)",
            supportsAllDrives=True
        ).execute()
        
        files_fixed = results_fixed.get('files', [])
        
        if files_fixed:
            file_id = files_fixed[0]['id']
            print(f"📝 Found fixed file, updating: {fixed_filename}")
            
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
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
    
    # ファイルが見つからない場合
    print(f"❌ File not found in Google Drive")
    print(f"📋 Please create the file manually first:")
    print(f"   1. Go to MLB_Reports folder")
    print(f"   2. Create a file named: {fixed_filename or file_name}")
    print(f"   3. Share it with: mlb-report-uploader@mlb-report-system.iam.gserviceaccount.com")
    return False

def upload_all_formats(service, folder_id):
    """全形式のレポートをアップロード"""
    
    success_count = 0
    total_count = 0
    
    # 1. テキストレポート
    print("\n" + "="*60)
    print("📄 Uploading Text Report")
    print("="*60)
    
    txt_reports = glob.glob("daily_reports/MLB*.txt")
    if txt_reports:
        latest_txt = max(txt_reports, key=os.path.getctime)
        print(f"Found: {latest_txt}")
        total_count += 1
        if upload_file_to_drive(service, latest_txt, folder_id, "MLB_Latest_Report.txt"):
            success_count += 1
    else:
        print("No text report found")
    
    # 2. HTMLレポート
    print("\n" + "="*60)
    print("🌐 Uploading HTML Report")
    print("="*60)
    
    html_reports = glob.glob("daily_reports/html/MLB*.html")
    if html_reports:
        latest_html = max(html_reports, key=os.path.getctime)
        print(f"Found: {latest_html}")
        total_count += 1
        if upload_file_to_drive(service, latest_html, folder_id, "MLB_Latest_Report.html"):
            success_count += 1
    else:
        print("No HTML report found")
    
    # 3. PDFレポート
    print("\n" + "="*60)
    print("📑 Uploading PDF Report")
    print("="*60)
    
    pdf_reports = glob.glob("daily_reports/pdf/MLB*.pdf")
    if pdf_reports:
        latest_pdf = max(pdf_reports, key=os.path.getctime)
        print(f"Found: {latest_pdf}")
        total_count += 1
        if upload_file_to_drive(service, latest_pdf, folder_id, "MLB_Latest_Report.pdf"):
            success_count += 1
    else:
        print("No PDF report found")
    
    return success_count, total_count

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='Upload MLB reports to Google Drive')
    parser.add_argument('--txt-only', action='store_true', help='Upload only text file')
    parser.add_argument('--html-only', action='store_true', help='Upload only HTML file')
    parser.add_argument('--pdf-only', action='store_true', help='Upload only PDF file')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Google Drive Upload Script (Multi-Format)")
    print("=" * 60)
    
    # 環境変数から認証情報を取得
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    
    if not creds_json:
        print("❌ Error: GOOGLE_CREDENTIALS not found")
        sys.exit(1)
    
    if not folder_id:
        print("❌ Error: GOOGLE_DRIVE_FOLDER_ID not found")
        sys.exit(1)
    
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
        
        # 特定形式のみアップロードする場合
        if args.txt_only or args.html_only or args.pdf_only:
            success = False
            
            if args.txt_only:
                txt_reports = glob.glob("daily_reports/MLB*.txt")
                if txt_reports:
                    latest = max(txt_reports, key=os.path.getctime)
                    success = upload_file_to_drive(service, latest, folder_id, "MLB_Latest_Report.txt")
            
            elif args.html_only:
                html_reports = glob.glob("daily_reports/html/MLB*.html")
                if html_reports:
                    latest = max(html_reports, key=os.path.getctime)
                    success = upload_file_to_drive(service, latest, folder_id, "MLB_Latest_Report.html")
            
            elif args.pdf_only:
                pdf_reports = glob.glob("daily_reports/pdf/MLB*.pdf")
                if pdf_reports:
                    latest = max(pdf_reports, key=os.path.getctime)
                    success = upload_file_to_drive(service, latest, folder_id, "MLB_Latest_Report.pdf")
            
            sys.exit(0 if success else 1)
        
        # デフォルト: 全形式をアップロード
        success_count, total_count = upload_all_formats(service, folder_id)
        
        print("\n" + "="*60)
        print(f"🎯 Upload Summary: {success_count}/{total_count} files uploaded")
        print("="*60)
        
        if success_count == total_count and total_count > 0:
            print("🎉 All uploads completed successfully!")
            sys.exit(0)
        elif success_count > 0:
            print("⚠️ Some uploads completed")
            sys.exit(0)
        else:
            print("❌ No files uploaded")
            sys.exit(1)
            
    except HttpError as e:
        print(f"❌ HTTP Error: {e}")
        if "storageQuotaExceeded" in str(e):
            print("💡 This is a service account limitation.")
            print("   Please create the file manually in Google Drive first.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()