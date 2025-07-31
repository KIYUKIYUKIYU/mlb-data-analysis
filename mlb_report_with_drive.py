#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLBレポート生成＆Google Driveアップロード統合スクリプト（Discord通知付き）
"""

import os
import sys
from datetime import datetime, timedelta
import pytz
import requests

# プロジェクトのルートディレクトリをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.mlb_complete_report_real import generate_report
from scripts.oauth_drive_uploader import OAuthDriveUploader

def send_discord_notification(webhook_url, title, message, success=True):
    """Discord通知を送信"""
    if not webhook_url:
        return False
    
    # 成功は緑、失敗は赤
    color = 0x00ff00 if success else 0xff0000
    
    data = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "MLB Report System"
            }
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        return response.status_code == 204
    except Exception as e:
        print(f"Discord通知エラー: {e}")
        return False

def main():
    print("=" * 60)
    print("MLBレポート生成＆Google Driveアップロード")
    print("=" * 60)
    
    # Discord Webhook URL（環境変数から取得）
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    # 日本時間で翌日の日付を取得
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst)
    game_date = now_jst + timedelta(days=1)
    
    # 曜日を日本語で
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekday = weekdays[game_date.weekday()]
    
    # ファイル名を日本語形式に（曜日付き）
    filename = f"MLB{game_date.strftime('%m月%d日')}({weekday})レポート.txt"
    
    # 処理開始通知
    start_message = f"🚀 MLBレポート生成を開始します\n📅 対象日: {game_date.strftime('%Y年%m月%d日')}({weekday})"
    send_discord_notification(webhook_url, "処理開始", start_message, True)
    
    print("1. MLBレポートを生成中...")
    
    try:
        # レポートを生成してファイルに保存
        report_content = generate_report()
        
        # ファイルに保存（UTF-8エンコーディング）
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ レポート生成完了: {filename}")
        
    except Exception as e:
        error_message = f"❌ レポート生成エラー: {str(e)}"
        print(error_message)
        
        # エラー通知
        send_discord_notification(webhook_url, "⚠️ エラー発生", error_message, False)
        return 1
    
    print("\n2. Google Driveにアップロード中...")
    
    try:
        # Google Driveアップローダーを初期化
        uploader = OAuthDriveUploader()
        
        # ファイルをアップロード
        file_id = uploader.upload_file(filename)
        
        if file_id:
            print(f"✅ アップロード成功！")
            print(f"📁 ファイル名: {filename}")
            print(f"🔗 ファイルID: {file_id}")
            
            # 成功通知
            success_message = f"✅ レポート生成・アップロード完了！\n\n"
            success_message += f"📁 **ファイル名**: {filename}\n"
            success_message += f"📍 **保存先**: Google Drive/MLB_Reports/\n"
            success_message += f"🔗 **表示リンク**: [Google Driveで開く](https://drive.google.com/file/d/{file_id}/view)"
            
            send_discord_notification(webhook_url, "✨ 処理完了", success_message, True)
        else:
            raise Exception("アップロードに失敗しました")
            
    except Exception as e:
        error_message = f"❌ アップロードエラー: {str(e)}"
        print(error_message)
        
        # トークンエラーの場合は詳細なメッセージ
        if 'token' in str(e).lower() or 'invalid_grant' in str(e).lower():
            error_message += "\n\n⚠️ **認証トークンの更新が必要です**"
            error_message += "\n1. ローカルで `python mlb_report_with_drive.py` を実行"
            error_message += "\n2. ブラウザで再認証"
            error_message += "\n3. 新しいtoken.pickleをGitHub Secretsに更新"
        
        send_discord_notification(webhook_url, "⚠️ エラー発生", error_message, False)
        return 1
    
    print("\n✨ 処理完了！")
    return 0

if __name__ == "__main__":
    sys.exit(main())