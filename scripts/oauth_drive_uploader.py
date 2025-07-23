#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive OAuth2認証版アップローダー
"""

import os
import sys
from pathlib import Path
import pickle
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("必要なライブラリをインストールしてください:")
    print("pip install google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

logger = logging.getLogger(__name__)

class OAuthDriveUploader:
    """OAuth2認証を使用したGoogle Driveアップローダー"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_path='credentials/oauth_credentials.json'):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path('credentials/token.pickle')
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Google Drive APIサービスを初期化"""
        creds = None
        
        # トークンファイルが存在する場合は読み込み
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # 認証が無効または存在しない場合
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"認証ファイルが見つかりません: {self.credentials_path}\n"
                        "Google Cloud ConsoleでOAuth2クライアントIDを作成してください。"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.SCOPES)
                creds = flow.run_local_server(port=8080)
            
            # トークンを保存
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive API初期化成功（OAuth2）")
    
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
            logger.info(f"ファイルID: {file.get('id')}")
            logger.info(f"閲覧リンク: {file.get('webViewLink')}")
            
            return file
            
        except Exception as e:
            logger.error(f"アップロードエラー: {e}")
            raise