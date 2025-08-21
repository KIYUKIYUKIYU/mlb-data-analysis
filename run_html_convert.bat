@echo off
echo ========================================
echo MLB HTML Report Converter
echo ========================================

cd /d C:\Users\yfuku\Desktop\mlb-data-analysis

:: HTMLディレクトリ作成
if not exist daily_reports\html mkdir daily_reports\html

:: 最新のMLBレポートを探す
for /f "delims=" %%i in ('dir /b /od MLB*.txt 2^>nul') do set LATEST=%%i

if "%LATEST%"=="" (
    echo エラー: MLBレポートが見つかりません
    pause
    exit /b 1
)

echo 変換中: %LATEST%
python scripts\convert_to_html.py "%LATEST%"

:: 生成されたHTMLを開く
for /f "delims=" %%i in ('dir /b /od daily_reports\html\*.html 2^>nul') do set HTML=%%i
if not "%HTML%"=="" (
    start daily_reports\html\%HTML%
)

echo ========================================
echo 完了！
echo ========================================
pause