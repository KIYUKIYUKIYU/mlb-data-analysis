# fix_report_script.py
import os
import shutil
from datetime import datetime

# mlb_complete_report_real.pyのバックアップを作成
backup_file = f"scripts/mlb_complete_report_real_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
shutil.copy("scripts/mlb_complete_report_real.py", backup_file)
print(f"✅ バックアップ作成: {backup_file}")

# ファイルを読み込み
with open("scripts/mlb_complete_report_real.py", "r", encoding="utf-8") as f:
    content = f.read()

# 修正1: デバッグメッセージを削除
content = content.replace(
    'print(f"Debug - Advanced stats for pitcher {pitcher_id}: qualityStarts={qs_count}")',
    '# Debug removed'
)
content = content.replace(
    'print(f"Debug - Pitcher {pitcher_id}: GS={games_started}, QS={qs_count}")',
    '# Debug removed'
)
content = content.replace(
    'print(f"Debug - Using API QS rate: {qs_rate:.1f}%")',
    '# Debug removed'
)

# 修正2: Statcastログを完全に抑制
log_suppression = """
# ロギング設定（完全抑制版）
import logging
import sys
import io

# すべてのログを抑制
logging.basicConfig(
    level=logging.CRITICAL,
    handlers=[]
)

# 特定モジュールのログを完全に無効化
for logger_name in [
    'src.mlb_api_client',
    'scripts.batting_quality_stats',
    'scripts.enhanced_stats_collector',
    'scripts.bullpen_enhanced_stats',
    'scripts.savant_statcast_fetcher',
    'urllib3',
    'requests'
]:
    logging.getLogger(logger_name).disabled = True
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).handlers = []

# Statcastフェッチャーの出力を完全に抑制
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        return self
    
    def __exit__(self, *args):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
"""

# ロギング設定部分を置換
import_end = content.find("# ロギング設定")
if import_end != -1:
    next_class = content.find("class DataReliabilityChecker")
    content = content[:import_end] + log_suppression + "\\n\\n" + content[next_class:]

# 修正3: Statcast取得時の出力抑制を追加
statcast_fix = """
    def _display_team_batting_stats(self, team_id):
        \\"\\"\\"チーム打撃統計を表示（改善版）\\"\\"\\"
        try:
            # 必ず2025年のデータを使用
            team_stats = self.client.get_team_stats(team_id, 2025)
            
            # Statcast取得時の出力を抑制
            with SuppressOutput():
                quality_stats = self.batting_quality.get_team_quality_stats(team_id)
"""

# 該当箇所を探して置換
if "_display_team_batting_stats" in content:
    # メソッドの開始位置を探す
    method_start = content.find("def _display_team_batting_stats(self, team_id):")
    if method_start != -1:
        method_end = content.find("quality_stats = self.batting_quality.get_team_quality_stats(team_id)", method_start)
        if method_end != -1:
            # quality_stats行を修正
            line_end = content.find("\\n", method_end)
            content = (content[:method_end - 12] + 
                      "# Statcast取得時の出力を抑制\\n            with SuppressOutput():\\n                quality_stats = self.batting_quality.get_team_quality_stats(team_id)" + 
                      content[line_end:])

# ファイルを保存
with open("scripts/mlb_complete_report_real.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ スクリプトを修正しました")
print("\\n修正内容:")
print("1. デバッグメッセージを削除")
print("2. ログ出力を完全抑制")
print("3. Statcast取得時の出力を抑制")