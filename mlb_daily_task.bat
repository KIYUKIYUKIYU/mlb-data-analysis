@echo off
REM MLB日次レポート自動実行バッチ
REM Windowsタスクスケジューラーで毎日21:00に実行

cd /d C:\Users\yfuku\Desktop\mlb-data-analysis

REM ログファイル名（日付付き）
set LOG_FILE=logs\mlb_report_%date:~0,4%%date:~5,2%%date:~8,2%.log

REM ログディレクトリ作成
if not exist logs mkdir logs

echo ===================================== >> %LOG_FILE%
echo MLBレポート自動配信 >> %LOG_FILE%
echo 実行時刻: %date% %time% >> %LOG_FILE%
echo ===================================== >> %LOG_FILE%

REM 仮想環境をアクティベート
call venv\Scripts\activate

REM 現在時刻を表示して実行
python show_current_time.py >> %LOG_FILE% 2>&1

echo. >> %LOG_FILE%
echo 実行完了: %time% >> %LOG_FILE%
echo ===================================== >> %LOG_FILE%