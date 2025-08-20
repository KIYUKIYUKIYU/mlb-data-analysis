@echo off 
python generate_clean_report.py 
for /f "delims=" %%i in ('dir /b /od MLB_Report_*.txt') do set newest=%%i 
notepad %%newest%% 
