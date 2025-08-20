# fix_encoding.py
import sys
import io

# UTF-8を強制
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# テスト実行
exec(open("scripts/mlb_complete_report_real.py", encoding="utf-8").read())