import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 既存のdiscord_report_with_tableから必要な部分だけ抽出
from scripts.discord_report_with_table import DiscordReportWithTable

class TextOnlyReport(DiscordReportWithTable):
    """テキストのみ出力版"""
    
    def __init__(self):
        super().__init__()
    
    async def send_all_games_text_only(self):
        """全試合のテキストレポートを出力"""
        # 日本時間で本日の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        
        # アメリカ東部時間に変換して前日の日付を取得
        est = pytz.timezone('US/Eastern')
        now_est = now_jst.astimezone(est)
        
        # 21時以降なら今日、それ以前なら昨日の試合を取得
        if now_jst.hour >= 21:
            # 今日の試合（明日のアメリカの試合）
            tomorrow_est = now_est.date()
        else:
            # 昨日の試合（今日のアメリカの試合）
            tomorrow_est = (now_est - timedelta(days=1)).date()
        
        print(f"取得日: {tomorrow_est} (アメリカ東部時間)")
        
        # 試合データを取得
        games_data = self._get_games_data(tomorrow_est)
        
        if not games_data:
            print("試合データが見つかりません。")
            return
        
        print(f"見つかった試合数: {len(games_data)}")
        print("=" * 80)
        
        # 各試合を処理
        for i, (game_pk, game_data) in enumerate(games_data.items(), 1):
            print(f"\n【試合 {i}/{len(games_data)}】")
            
            try:
                # チーム情報
                away_team = game_data['teams']['away']['team']['name']
                home_team = game_data['teams']['home']['team']['name']
                
                # 日時
                game_datetime = datetime.fromisoformat(game_data['gameDate'].replace('Z', '+00:00'))
                game_time_jst = game_datetime.astimezone(jst)
                
                print(f"{away_team} @ {home_team}")
                print(f"開始時刻: {game_time_jst.strftime('%m/%d %H:%M')} (日本時間)")
                print("=" * 50)
                
                # 統計データを収集
                stats_data = await self._collect_all_stats(game_pk, game_data)
                
                # Away Team
                print(f"**【{away_team}】**")
                
                # 先発投手
                if stats_data.get('away_pitcher'):
                    p = stats_data['away_pitcher']
                    print(f"**先発**: {p['name']} ({p['wins']}勝{p['losses']}敗)")
                    print(f"ERA: {p['era']:.2f} | FIP: {p['fip']:.2f} | WHIP: {p['whip']:.2f} | K-BB%: {p['k_bb_percent']:.1f}%")
                else:
                    print("**先発**: TBA")
                
                # 中継ぎ陣
                if stats_data.get('away_bullpen'):
                    b = stats_data['away_bullpen']
                    print(f"**中継ぎ陣** ({b['reliever_count']}名):")
                    print(f"ERA: {b['era']:.2f} | FIP: {b['fip']:.2f} | WHIP: {b['whip']:.2f}")
                    if b.get('closer_name'):
                        print(f"CL: {b['closer_name']}")
                
                # チーム打撃
                if stats_data.get('away_team_batting'):
                    t = stats_data['away_team_batting']
                    print("**チーム打撃**:")
                    print(f"AVG: .{t['batting_avg']} | OPS: .{t['ops']} | 得点: {t['runs']} | 本塁打: {t['home_runs']}")
                
                # 最近のOPS
                if stats_data.get('away_recent_ops'):
                    r = stats_data['away_recent_ops']
                    print(f"過去5試合OPS: {r['last_5_ops']:.3f} | 過去10試合OPS: {r['last_10_ops']:.3f}")
                
                print()
                
                # Home Team
                print(f"**【{home_team}】**")
                
                # 先発投手
                if stats_data.get('home_pitcher'):
                    p = stats_data['home_pitcher']
                    print(f"**先発**: {p['name']} ({p['wins']}勝{p['losses']}敗)")
                    print(f"ERA: {p['era']:.2f} | FIP: {p['fip']:.2f} | WHIP: {p['whip']:.2f} | K-BB%: {p['k_bb_percent']:.1f}%")
                else:
                    print("**先発**: TBA")
                
                # 中継ぎ陣
                if stats_data.get('home_bullpen'):
                    b = stats_data['home_bullpen']
                    print(f"**中継ぎ陣** ({b['reliever_count']}名):")
                    print(f"ERA: {b['era']:.2f} | FIP: {b['fip']:.2f} | WHIP: {b['whip']:.2f}")
                    if b.get('closer_name'):
                        print(f"CL: {b['closer_name']}")
                
                # チーム打撃
                if stats_data.get('home_team_batting'):
                    t = stats_data['home_team_batting']
                    print("**チーム打撃**:")
                    print(f"AVG: .{t['batting_avg']} | OPS: .{t['ops']} | 得点: {t['runs']} | 本塁打: {t['home_runs']}")
                
                # 最近のOPS
                if stats_data.get('home_recent_ops'):
                    r = stats_data['home_recent_ops']
                    print(f"過去5試合OPS: {r['last_5_ops']:.3f} | 過去10試合OPS: {r['last_10_ops']:.3f}")
                
                print("=" * 50)
                
            except Exception as e:
                print(f"エラー: {e}")
                continue
        
        print(f"\n全{len(games_data)}試合の処理完了！")


async def main():
    """メイン実行関数"""
    reporter = TextOnlyReport()
    await reporter.send_all_games_text_only()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())