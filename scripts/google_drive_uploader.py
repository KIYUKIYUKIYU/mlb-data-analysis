#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive自動アップロードモジュール（簡易版）
"""

import os
import sys
from pathlib import Path
import logging

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("Google APIライブラリをインストールしてください:")
    print("pip install google-api-python-client google-auth")
    sys.exit(1)

logger = logging.getLogger(__name__)

class GoogleDriveUploader:
    """Google Driveアップロードクラス"""
    
    def __init__(self, credentials_path=None):
        if credentials_path is None:
            project_root = Path(__file__).parent.parent
            credentials_path = project_root / "credentials" / "google_drive_credentials.json"
        
        self.credentials_path = Path(credentials_path)
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Google Drive APIサービスを初期化"""
        try:
            if not self.credentials_path.exists():
                raise FileNotFoundError(f"認証ファイルが見つかりません: {self.credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive API初期化成功")
            
        except Exception as e:
            logger.error(f"Google Drive API初期化エラー: {e}")
            raise
    
    def upload_file(self, file_path, folder_id=None, file_name=None):
        """ファイルをGoogle Driveにアップロード"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
            if file_name is None:
                file_name = file_path.name
            
            mime_type = 'text/plain' if file_path.suffix == '.txt' else 'application/octet-stream'
            
            file_metadata = {
                'name': file_name,
                'mimeType': mime_type
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True
            )
            
            logger.info(f"アップロード開始: {file_name}")
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            ).execute()
            
            logger.info(f"アップロード成功: {file_name}")
            
            return file
            
        except Exception as e:
            logger.error(f"アップロードエラー: {e}")
            raise