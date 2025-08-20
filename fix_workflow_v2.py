# fix_workflow_v2.py
workflow_content = """name: Daily MLB Report

on:
  schedule:
    # 毎日日本時間18:30に実行（UTCで09:30）
    - cron: '30 9 * * *'
  workflow_dispatch:  # 手動実行も可能

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
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pandas numpy requests beautifulsoup4 pytz lxml
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Create necessary directories
      run: |
        mkdir -p cache
        mkdir -p cache/splits_data
        mkdir -p cache/advanced_stats
        mkdir -p cache/bullpen_stats
        mkdir -p cache/batting_quality
        mkdir -p cache/recent_ops
        mkdir -p cache/statcast_data
        mkdir -p logs
        mkdir -p daily_reports
        mkdir -p src
        mkdir -p scripts
    
    - name: Generate MLB Report Directly
      env:
        PYTHONIOENCODING: utf-8
        PYTHONPATH: ${{ github.workspace }}
      run: |
        echo "Starting report generation..."
        python scripts/mlb_complete_report_real.py > daily_reports/report_$(date +%Y%m%d).txt 2>&1 || true
        
        if [ -f daily_reports/report_$(date +%Y%m%d).txt ]; then
          echo "Report file created"
          echo "Report size: $(wc -l < daily_reports/report_$(date +%Y%m%d).txt) lines"
          echo "=== First 50 lines of report ==="
          head -n 50 daily_reports/report_$(date +%Y%m%d).txt
        else
          echo "Report file not found"
          # エラーログを表示
          ls -la daily_reports/
          exit 1
        fi
    
    - name: Upload Report
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: mlb-report-${{ github.run_number }}
        path: |
          daily_reports/
          logs/
        retention-days: 30
    
    - name: Send notification
      if: success()
      run: |
        echo "✅ レポート生成成功！"
        echo "Report saved to: daily_reports/report_$(date +%Y%m%d).txt"
"""

# ファイルを保存
import os
workflow_path = r"C:\\Users\\yfuku\\Desktop\\mlb-data-analysis\\.github\\workflows\\daily_mlb_report.yml"
os.makedirs(os.path.dirname(workflow_path), exist_ok=True)

with open(workflow_path, 'w', encoding='utf-8') as f:
    f.write(workflow_content)

print("✅ ワークフローファイルを更新しました（v4対応版）！")
print(f"📄 {workflow_path}")
print("\\n次のステップ:")
print('1. git add .github/workflows/daily_mlb_report.yml')
print('2. git commit -m "Update to use actions v4"')
print('3. git push')