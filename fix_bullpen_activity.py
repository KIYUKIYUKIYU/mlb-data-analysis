# fix_bullpen_activity.py
# bullpen_enhanced_stats.py の問題を修正するスクリプト

import re
import os

file_path = r"scripts\bullpen_enhanced_stats.py"
backup_path = f"{file_path}.bak"

try:
    # 元のファイルのバックアップを作成
    if not os.path.exists(backup_path):
        os.rename(file_path, backup_path)
        print(f"バックアップを作成しました: {backup_path}")

    with open(backup_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. _check_recent_activity の定義に 'season' 引数を追加
    content, count1 = re.subn(
        r"def _check_recent_activity\(self, pitcher_id: int, cutoff_date: datetime\)",
        r"def _check_recent_activity(self, pitcher_id: int, cutoff_date: datetime, season: int)",
        content
    )

    # 2. _check_recent_activity の呼び出し箇所に 'season' を渡す
    content, count2 = re.subn(
        r"self\._check_recent_activity\(pitcher_id, cutoff_date\)",
        r"self._check_recent_activity(pitcher_id, cutoff_date, season)",
        content
    )

    # 3. get_player_game_logs の呼び出しでハードコードされた '2025' を 'season' に変更
    content, count3 = re.subn(
        r"self\.api_client\.get_player_game_logs\(pitcher_id, season=2025\)",
        r"self.api_client.get_player_game_logs(pitcher_id, season=season)",
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n=== 修正内容 ===")
    if count1 > 0: print("1. _check_recent_activity の定義を修正しました。")
    if count2 > 0: print("2. _check_recent_activity の呼び出しを修正しました。")
    if count3 > 0: print("3. ゲームログ取得のシーズンを動的に変更しました。")
    print(f"\n修正完了: {file_path} を更新しました。")


except Exception as e:
    print(f"エラーが発生しました: {e}")
    if os.path.exists(backup_path):
        os.rename(backup_path, file_path) # エラー時はバックアップから復元
        print("エラーが発生したため、バックアップからファイルを復元しました。")