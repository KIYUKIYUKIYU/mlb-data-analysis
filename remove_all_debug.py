# remove_all_debug.py
import os
import glob

# すべてのPythonファイルからDebug出力を削除
files_to_check = [
    "scripts/mlb_complete_report_real.py",
    "scripts/enhanced_stats_collector.py",
    "scripts/bullpen_enhanced_stats.py",
    "scripts/batting_quality_stats.py"
]

for filepath in files_to_check:
    if not os.path.exists(filepath):
        print(f"⚠️ {filepath} が見つかりません")
        continue
    
    # ファイルを読み込み
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Debug行を削除
    cleaned_lines = []
    removed_count = 0
    for line in lines:
        # Debug出力を含む行をスキップ
        if 'print(f"Debug' in line or 'print("Debug' in line or "print('Debug" in line:
            removed_count += 1
            continue
        cleaned_lines.append(line)
    
    # 変更があった場合のみ保存
    if removed_count > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        print(f"✅ {filepath}: {removed_count} 個のDebug行を削除")
    else:
        print(f"📝 {filepath}: Debug行なし")

print("\\n✅ すべてのDebug出力を削除しました")