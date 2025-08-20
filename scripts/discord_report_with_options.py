 #!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Discord Report with Options - オプション付きレポート
高速版（過去OPSなし）か完全版（過去OPSあり）を選択可能

実行: 
  高速版: python -m scripts.discord_report_with_options --fast
  完全版: python -m scripts.discord_report_with_options --full
"""

import sys
sys.path.append('..')

from scripts.discord_complete_report import DiscordCompleteReport

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--fast', action='store_true', help='高速版（過去OPSなし）')
    parser.add_argument('--full', action='store_true', help='完全版（過去OPSあり）')
    args = parser.parse_args()
    
    system = DiscordCompleteReport()
    
    if args.fast:
        print("高速版で実行（過去5/10試合OPSは省略）")
        # _get_team_recent_opsをオーバーライド
        system._get_team_recent_ops = lambda team_id, season, games_count: 'N/A'
    else:
        print("完全版で実行（過去5/10試合OPSを計算）")
        print("※ 処理に時間がかかります")
        
    system.run_discord_report()
