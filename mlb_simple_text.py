import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 既存のスクリプトを実行
if __name__ == "__main__":
    # 環境変数をダミーに設定（Discord送信を防ぐ）
    os.environ['DISCORD_WEBHOOK_URL'] = 'dummy'
    
    # 既存のスクリプトをインポートして実行
    from scripts import discord_report_with_table
    
    # asyncioで実行
    import asyncio
    
    # メイン関数を直接呼び出す
    asyncio.run(discord_report_with_table.main())