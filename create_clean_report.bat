@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
python scripts\mlb_complete_report_real.py 2>nul | findstr /v "INFO DEBUG" > MLB_Clean_%date:~0,4%%date:~5,2%%date:~8,2%.txt
notepad MLB_Clean_%date:~0,4%%date:~5,2%%date:~8,2%.txt