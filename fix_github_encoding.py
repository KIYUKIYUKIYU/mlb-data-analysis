# fix_github_encoding.py
workflow_content = """name: Daily MLB Report

on:
  schedule:
    - cron: '30 9 * * *'
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    
    - name: Setup locale for Japanese
      run: |
        sudo apt-get update
        sudo apt-get install -y locales
        sudo locale-gen ja_JP.UTF-8
        echo "LANG=ja_JP.UTF-8" >> $GITHUB_ENV
        echo "LC_ALL=ja_JP.UTF-8" >> $GITHUB_ENV
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pandas numpy requests beautifulsoup4 pytz lxml
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Create necessary directories
      run: |
        mkdir -p cache cache/splits_data cache/advanced_stats
        mkdir -p cache/bullpen_stats cache/batting_quality
        mkdir -p cache/recent_ops cache/statcast_data
        mkdir -p logs daily_reports src scripts
    
    - name: Generate MLB Report with UTF-8
      env:
        PYTHONIOENCODING: utf-8
        LANG: ja_JP.UTF-8
        LC_ALL: ja_JP.UTF-8
        LC_CTYPE: ja_JP.UTF-8
        PYTHONPATH: ${{ github.workspace }}
      run: |
        echo "🚀 レポート生成開始..."
        echo "Locale: $(locale)"
        
        # UTF-8でレポート生成
        python -u scripts/mlb_complete_report_real.py > daily_reports/report_$(date +%Y%m%d).txt 2>/dev/null
        
        # ファイル確認
        if [ -f daily_reports/report_$(date +%Y%m%d).txt ]; then
          echo "✅ レポート生成成功"
          # 文字コード確認
          file -bi daily_reports/report_$(date +%Y%m%d).txt
          # 行数確認
          wc -l daily_reports/report_$(date +%Y%m%d).txt
          # 最初の10行を表示（文字化け確認用）
          echo "=== Report Preview ==="
          head -n 10 daily_reports/report_$(date +%Y%m%d).txt
        fi
    
    - name: Upload Report
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: mlb-report-${{ github.run_number }}
        path: daily_reports/
        retention-days: 30
    
    - name: Summary
      if: always()
      run: |
        echo "## 📊 MLB Daily Report" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "- Date: $(date +%Y-%m-%d)" >> $GITHUB_STEP_SUMMARY
        echo "- Status: Complete" >> $GITHUB_STEP_SUMMARY
        if [ -f daily_reports/report_$(date +%Y%m%d).txt ]; then
          echo "- Lines: $(wc -l < daily_reports/report_$(date +%Y%m%d).txt)" >> $GITHUB_STEP_SUMMARY
        fi
"""

import os
workflow_path = r"C:\Users\yfuku\Desktop\mlb-data-analysis\.github\workflows\daily_mlb_report.yml"
with open(workflow_path, 'w', encoding='utf-8') as f:
    f.write(workflow_content)

print("✅ ワークフローを更新しました（日本語ロケール対応版）")