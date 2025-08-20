@echo off
echo === MLBレポート生成（最新データ版） ===
echo.

REM キャッシュクリア
echo キャッシュをクリア中...
del cache\*.json /s /q >nul 2>&1
echo キャッシュクリア完了
echo.

REM Python仮想環境を有効化
call venv\Scripts\activate

REM 文字化け対策
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

REM 今日の試合レポート生成
echo 今日の試合レポートを生成中...
python mlb_today_report.py > MLB_Report_Today.txt 2>nul
echo 完了: MLB_Report_Today.txt
echo.

REM 明日の試合レポート生成
echo 明日の試合レポートを生成中...
python scripts\mlb_complete_report_real.py > MLB_Report_Tomorrow.txt 2>nul
echo 完了: MLB_Report_Tomorrow.txt
echo.

REM メモ帳で開く
echo レポートを開きます...
start notepad MLB_Report_Today.txt
start notepad MLB_Report_Tomorrow.txt

echo.
echo 処理完了！
pause