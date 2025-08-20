import re
import os

file_path = r"scripts\mlb_complete_report_real.py"
backup_path = file_path + ".final.bak"

print(f"--- {os.path.basename(file_path)} の過去試合OPS計算を最終修正します ---")

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修正対象の間違ったコードブロックを特定
    #（コメントから呼び出しの終わりまで）
    buggy_code_pattern = re.compile(
        r"""(# 驕主悉縺ｮ隧ｦ蜷育ｵ先棡繧貞叙蠕・.*?games = self\.api_client\.get_recent_games\([^)]*\))""",
        re.DOTALL
    )

    # 正しいコード（過去10試合分のデータを取得する）
    correct_code = """# 過去10試合の完了した試合データを取得
        games = self.api_client.get_recent_games(team_id, limit=10)"""

    # コードを置換
    new_content, count = buggy_code_pattern.subn(correct_code, content)

    if count > 0:
        # 念のため最終バックアップを作成
        if not os.path.exists(backup_path):
             os.rename(file_path, backup_path)

        # 修正内容を書き込み
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("修正完了: 過去試合OPSの計算ロジックを修正しました。")
    else:
        print("修正箇所が見つかりませんでした。ファイルは変更されていません。")

except Exception as e:
    print(f"修正中にエラーが発生しました: {e}")