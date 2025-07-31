#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive OAuth2認証アップローダー（日本語ファイル名対応版）
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

class OAuthDriveUploader:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Google Drive APIサービスを初期化（自動更新機能付き）"""
        token_path = 'credentials/token.pickle'
        creds_path = 'credentials/oauth_credentials.json'
        
        # 既存のトークンを読み込み
        if os.path.exists(token_path):
            try:
                with open(token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            except Exception as e:
                print(f"トークン読み込みエラー: {e}")
                self.creds = None
        
        # トークンが無効または期限切れの場合
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("トークンの有効期限が切れています。自動更新を試みます...")
                try:
                    self.creds.refresh(Request())
                    print("✅ トークンの自動更新に成功しました")
                    # 更新したトークンを保存
                    with open(token_path, 'wb') as token:
                        pickle.dump(self.creds, token)
                except Exception as e:
                    print(f"❌ トークンの自動更新に失敗: {e}")
                    # GitHub Actions環境では再認証不可
                    if os.environ.get('GITHUB_ACTIONS'):
                        print("GitHub Actions環境では再認証できません。")
                        print("ローカルで新しいトークンを生成してください。")
                        raise e
                    else:
                        # ローカル環境では再認証を試みる
                        self._create_new_token(creds_path, token_path)
            else:
                # 新規認証が必要
                if os.environ.get('GITHUB_ACTIONS'):
                    raise Exception("有効なトークンがありません。ローカルで認証を実行してください。")
                else:
                    self._create_new_token(creds_path, token_path)
        
        # サービスを構築
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def _create_new_token(self, creds_path, token_path):
        """新しいトークンを作成"""
        print("新しい認証が必要です...")
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"認証情報ファイルが見つかりません: {creds_path}")
        
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, self.SCOPES)
        self.creds = flow.run_local_server(port=0)
        
        # トークンを保存
        with open(token_path, 'wb') as token:
            pickle.dump(self.creds, token)
        print("✅ 新しいトークンを保存しました")
    
    def upload_file(self, filepath, folder_id=None, display_name=None):
        """ファイルをGoogle Driveにアップロード（日本語ファイル名対応）"""
        try:
            # フォルダIDを設定ファイルから取得
            if folder_id is None:
                folder_id = self._get_folder_id()
            
            # display_nameが指定されていない場合は、元のファイル名を使用
            if display_name is None:
                display_name = os.path.basename(filepath)
            
            # デバッグ情報
            print(f"アップロード情報:")
            print(f"  - ローカルファイル: {filepath}")
            print(f"  - Google Drive表示名: {display_name}")
            print(f"  - フォルダID: {folder_id}")
            
            file_metadata = {
                'name': display_name,  # Google Driveでの表示名
                'parents': [folder_id] if folder_id else []
            }
            
            # ファイルが存在するか確認
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")
            
            media = MediaFileUpload(
                filepath, 
                resumable=True,
                mimetype='text/plain'  # テキストファイルとして明示的に指定
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            print(f"✅ アップロード成功:")
            print(f"  - ファイルID: {file.get('id')}")
            print(f"  - ファイル名: {file.get('name')}")
            print(f"  - 表示リンク: {file.get('webViewLink')}")
            
            return file.get('id')
            
        except Exception as e:
            print(f"アップロードエラー: {e}")
            # トークンエラーの場合は再試行
            if 'invalid_grant' in str(e) or 'Token has been' in str(e):
                print("トークンエラーを検出。再初期化を試みます...")
                self._initialize_service()
                # 再試行（display_name引数を追加）
                return self.upload_file(filepath, folder_id, display_name)
            raise e
    
    def _get_folder_id(self):
        """設定ファイルからフォルダIDを取得"""
        config_path = 'config/auto_report_config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('google_drive_folder_id')
        # 環境変数から取得
        return os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    
    def list_files(self, folder_id=None):
        """フォルダ内のファイル一覧を取得"""
        try:
            if folder_id is None:
                folder_id = self._get_folder_id()
            
            query = f"'{folder_id}' in parents" if folder_id else ""
            
            results = self.service.files().list(
                q=query,
                pageSize=10,
                fields="nextPageToken, files(id, name, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                print('ファイルが見つかりませんでした。')
            else:
                print('ファイル一覧:')
                for file in files:
                    print(f"  - {file['name']} (ID: {file['id']})")
            
            return files
            
        except Exception as e:
            print(f"ファイル一覧取得エラー: {e}")
            return []