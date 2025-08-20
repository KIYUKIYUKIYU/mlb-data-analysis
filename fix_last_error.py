import os
import re

# 修正対象のファイルパス
# エラーログから、このファイルで計算されている可能性が高い
file_path = r"scripts\mlb_complete_report_real.py"

print(f"--- {os.path.basename(file_path)} の修正を開始します ---")

try:
    # 念のためバックアップを作成
    backup_path = file_path + ".bak2"
    if not os.path.exists(backup_path):
        if os.path.exists(file_path):
            os.rename(file_path, backup_path)
            print(f"バックアップを作成しました: {backup_path}")
        else:
            print(f"エラー: {file_path} が見つかりません。")
            exit()

    with open(backup_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 'get_team_schedule' を 'get_recent_games' に置換
    if 'get_team_schedule' in content:
        new_content = content.replace('.get_team_schedule(', '.get_recent_games(')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("修正完了: 'get_team_schedule' を 'get_recent_games' に置換しました。")
    else:
        print("修正箇所が見つかりませんでした。ファイルを元に戻します。")
        os.rename(backup_path, file_path)

except Exception as e:
    print(f"修正中にエラーが発生しました: {e}")