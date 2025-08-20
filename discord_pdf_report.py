import os
import sys
import subprocess
from datetime import datetime, timedelta
import pytz
import requests

def main():
    """メイン実行関数"""
    
    # 1. まず既存のdiscord_report_with_tableを実行
    print("Starting MLB report generation...")
    result = subprocess.run([sys.executable, "-m", "scripts.discord_report_with_table"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running discord_report_with_table: {result.stderr}")
        return
    
    print("Discord reports sent successfully!")
    
    # 2. PDFを生成してGoogle Driveにアップロード
    try:
        from google_drive_pdf_uploader import GoogleDrivePDFUploader
        
        print("\nGenerating PDF reports...")
        
        # PDFを生成
        pdf_files = generate_daily_pdf_reports()
        
        if pdf_files:
            print(f"Generated {len(pdf_files)} PDF files")
            
            # Google Driveにアップロード
            try:
                uploader = GoogleDrivePDFUploader()
                print("Uploading PDFs to Google Drive...")
                
                results = uploader.upload_multiple_pdfs(pdf_files)
                
                # 成功したアップロードのリンクを収集
                pdf_links = []
                for pdf_path, result in results.items():
                    if result['success']:
                        pdf_links.append({
                            'filename': os.path.basename(pdf_path),
                            'link': result['link']
                        })
                
                # PDFリンクをDiscordに送信
                if pdf_links:
                    send_pdf_links_to_discord(pdf_links)
                    
            except Exception as e:
                print(f"Google Drive upload failed: {e}")
                print("PDFs are saved locally in the reports folder.")
                
    except Exception as e:
        print(f"PDF generation failed: {e}")


def generate_daily_pdf_reports():
    """日次PDFレポートを生成"""
    
    # generate_pdf_reports.pyを実行
    result = subprocess.run([sys.executable, "generate_pdf_reports.py"], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error generating PDFs: {result.stderr}")
        return []
    
    # 生成されたPDFファイルのパスを取得
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.now(jst)
    
    # アメリカの試合日を計算
    if today.hour >= 21:
        target_date = today.date()
    else:
        target_date = (today - timedelta(days=1)).date()
    
    reports_dir = f"reports/{target_date.strftime('%Y%m%d')}"
    
    if os.path.exists(reports_dir):
        pdf_files = [os.path.join(reports_dir, f) for f in os.listdir(reports_dir) if f.endswith('.pdf')]
        return pdf_files
    
    return []


def send_pdf_links_to_discord(pdf_links):
    """PDFリンクをDiscordに送信"""
    
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("Discord webhook URL not set")
        return
    
    # PDFリンクメッセージを作成
    message = "📄 **詳細レポート（PDF）が利用可能です**\n\n"
    
    for pdf_info in pdf_links:
        message += f"• [{pdf_info['filename']}]({pdf_info['link']})\n"
    
    # Discordに送信
    payload = {
        "content": message
    }
    
    response = requests.post(webhook_url, json=payload)
    
    if response.status_code in [200, 204]:
        print("PDF links sent to Discord successfully!")
    else:
        print(f"Failed to send PDF links: {response.status_code}")


if __name__ == "__main__":
    # Discord Webhook URLが設定されているか確認
    if not os.environ.get('DISCORD_WEBHOOK_URL'):
        print("Error: DISCORD_WEBHOOK_URL environment variable not set")
        print("Please set it using: set DISCORD_WEBHOOK_URL=your_webhook_url")
        sys.exit(1)
    
    main()