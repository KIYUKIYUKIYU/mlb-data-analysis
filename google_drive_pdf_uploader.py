import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import pytz

class GoogleDrivePDFUploader:
    """Google DriveにPDFをアップロードして共有リンクを取得"""
    
    # Google Drive APIのスコープ
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._authenticate()
        
    def _authenticate(self):
        """Google Drive APIの認証"""
        creds = None
        
        # トークンファイルが存在する場合は読み込む
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # 認証が無効な場合は再認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # トークンを保存
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('drive', 'v3', credentials=creds)
    
    def create_folder_if_not_exists(self, folder_name, parent_id=None):
        """フォルダが存在しない場合は作成"""
        # フォルダを検索
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        else:
            # フォルダを作成
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
    
    def upload_pdf(self, file_path, file_name=None):
        """PDFをアップロードして共有リンクを取得"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_name is None:
            file_name = os.path.basename(file_path)
        
        # 日付フォルダを作成（MLB_Reports/YYYY-MM-DD）
        jst = pytz.timezone('Asia/Tokyo')
        today = datetime.now(jst).strftime('%Y-%m-%d')
        
        # メインフォルダを作成
        main_folder_id = self.create_folder_if_not_exists('MLB_Reports')
        
        # 日付フォルダを作成
        date_folder_id = self.create_folder_if_not_exists(today, main_folder_id)
        
        # ファイルメタデータ
        file_metadata = {
            'name': file_name,
            'parents': [date_folder_id]
        }
        
        # ファイルをアップロード
        media = MediaFileUpload(file_path, mimetype='application/pdf')
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        
        # ファイルを共有設定（リンクを知っている人は誰でも閲覧可能）
        self.service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()
        
        # 共有リンクを返す
        return file.get('webViewLink')
    
    def upload_multiple_pdfs(self, pdf_files):
        """複数のPDFをアップロード"""
        results = {}
        
        for pdf_path in pdf_files:
            try:
                link = self.upload_pdf(pdf_path)
                results[pdf_path] = {
                    'success': True,
                    'link': link
                }
                print(f"Uploaded: {os.path.basename(pdf_path)}")
            except Exception as e:
                results[pdf_path] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"Failed to upload {os.path.basename(pdf_path)}: {e}")
        
        return results


# 設定手順を出力する関数
def print_setup_instructions():
    """Google Drive API設定手順を表示"""
    print("""
=== Google Drive API 設定手順 ===

1. Google Cloud Consoleにアクセス
   https://console.cloud.google.com/

2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）

3. APIとサービス > ライブラリ から「Google Drive API」を検索して有効化

4. APIとサービス > 認証情報 > 認証情報を作成 > OAuth クライアント ID

5. アプリケーションの種類: デスクトップアプリ
   名前: MLB Report Uploader（任意）

6. 作成されたOAuth 2.0クライアントIDをダウンロード

7. ダウンロードしたJSONファイルを「credentials.json」として
   プロジェクトルートに保存

8. 必要なパッケージをインストール:
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

=================================
""")


if __name__ == "__main__":
    # 設定手順を表示
    print_setup_instructions()
    
    # テスト実行
    try:
        uploader = GoogleDrivePDFUploader()
        print("認証成功！")
    except Exception as e:
        print(f"エラー: {e}")
        print("\n上記の設定手順に従ってGoogle Drive APIを設定してください。")