@echo off
cd /d C:\Users\yfuku\Desktop\mlb-data-analysis
call venv\Scripts\activate
python -m scripts.discord_report_with_table
exit