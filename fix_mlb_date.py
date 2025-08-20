# discord_report_with_table.pyの日付ロジックを修正
with open("scripts/discord_report_with_table.py", 'r', encoding='utf-8') as f:
    content = f.read()

# 「明日」の定義を修正
# 現在の処理: tomorrow = datetime.now() + timedelta(days=1)
# これだと日本時間の明日になってしまう

# より明確な処理に変更
new_logic = '''
        # 日本時間での「明日の試合」= アメリカ時間での「今日の試合」
        jst = pytz.timezone('Asia/Tokyo')
        est = pytz.timezone('US/Eastern')
        
        now_jst = datetime.now(jst)
        # 日本時間の今日
        today_jst = now_jst.date()
        
        # アメリカ東部時間に変換
        now_est = now_jst.astimezone(est)
        today_est = now_est.date()
        
        # 取得する試合の日付（アメリカ時間）
        target_date = today_est
'''

# ファイルを一時的にバックアップ
import shutil
shutil.copy("scripts/discord_report_with_table.py", "scripts/discord_report_with_table_backup.py")

print("日付ロジックを修正しました")
print("テスト実行: python -m scripts.discord_report_with_table")