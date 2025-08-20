# check_structure.py として保存して実行
import os

def show_directory_structure(path, indent=""):
    """ディレクトリ構造を表示"""
    try:
        items = []
        for item in os.listdir(path):
            if item.startswith('.'):  # 隠しフォルダも表示
                items.append(item)
            else:
                items.append(item)
        
        for item in sorted(items):
            item_path = os.path.join(path, item)
            print(f"{indent}{item}")
            if os.path.isdir(item_path) and not item.startswith('.git') and item != '__pycache__':
                show_directory_structure(item_path, indent + "  ")
    except PermissionError:
        pass

# プロジェクトのルートディレクトリを確認
project_path = r"C:\\Users\\yfuku\\Desktop\\mlb-data-analysis"
print(f"プロジェクト構造: {project_path}\\n")
print("=" * 50)
show_directory_structure(project_path)