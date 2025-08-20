import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict
from scripts.enhanced_stats_collector import EnhancedStatsCollector
from scripts.calculate_gb_fb_stats import GBFBCalculator

class CompleteStatsFormatter:
    """完全な統計情報をフォーマット"""

    def __init__(self):
        self.enhanced_collector = EnhancedStatsCollector()
        self.gb_fb_calculator = GBFBCalculator()

    def format_game_stats(self, game_data: Dict) -> str:
        """1試合の統計を完全フォーマット"""
        away_team = game_data['away_team']
        home_team = game_data['home_team']
        game_time = game_data.get('game_time', '未定')

        # 試合情報ヘッダー
        output = f"{'='*60}\n"
        output += f"**{away_team['name']} @ {home_team['name']}**\n"
        output += f"開始時刻: {game_time} (日本時間)\n"
        output += f"{'='*50}\n\n"

        # Away Team
        output += f"【{away_team['name']}】\n"
        output += self._format_team_stats(away_team)
        output += "\n"

        # Home Team
        output += f"【{home_team['name']}】\n"
        output += self._format_team_stats(home_team)

        output += f"{'='*50}\n"

        return output

    def _format_team_stats(self, team_data: Dict) -> str:
        """チーム統計をフォーマット"""
        output = ""

        # 先発投手
        pitcher_id = team_data.get('pitcher_id')
        if pitcher_id:
            pitcher_stats = self.enhanced_collector.get_pitcher_enhanced_stats(pitcher_id)

            # GB%/FB%を取得（APIになければ計算）
            if pitcher_stats['gb_percent'] == 0.0 and pitcher_stats['fb_percent'] == 0.0:
                gb, fb = self.gb_fb_calculator.calculate_pitcher_gb_fb(pitcher_id, limit_games=3)
                pitcher_stats['gb_percent'] = gb
                pitcher_stats['fb_percent'] = fb

            output += f"**先発**: {pitcher_stats['name']} ({pitcher_stats['wins']}勝{pitcher_stats['losses']}敗)\n"
            output += f"ERA: {pitcher_stats['era']:.2f} | FIP: {pitcher_stats['fip']:.2f} | "
            output += f"xFIP: {pitcher_stats.get('xfip', 0.00):.2f} | "
            output += f"WHIP: {pitcher_stats['whip']:.2f} | K-BB%: {pitcher_stats['k_bb_percent']:.1f}% | "
            output += f"GB%: {pitcher_stats['gb_percent']:.1f}% | FB%: {pitcher_stats['fb_percent']:.1f}% | "
            output += f"QS率: {pitcher_stats['qs_rate']:.1f}%\n"
            
            # Phase1追加項目
            output += f"SwStr%: {pitcher_stats.get('swstr_percent', 10.0):.1f}% | "
            output += f"BABIP: {pitcher_stats.get('babip', .300):.3f}\n"
            
            output += f"対左: {pitcher_stats['vs_left']['avg']} (OPS {pitcher_stats['vs_left']['ops']}) | "
            output += f"対右: {pitcher_stats['vs_right']['avg']} (OPS {pitcher_stats['vs_right']['ops']})\n"
        else:
            output += "**先発**: 未定\n"

        output += "\n"

        # 中継ぎ陣
        bullpen = team_data.get('bullpen', {})
        output += f"**中継ぎ陣** ({bullpen.get('reliever_count', 0)}名):\n"
        output += f"ERA: {bullpen.get('era', 0.00):.2f} | FIP: {bullpen.get('fip', 0.00):.2f} | "
        output += f"WHIP: {bullpen.get('whip', 0.00):.2f}\n"
        if bullpen.get('closer_name'):
            output += f"CL: {bullpen['closer_name']}\n"

        output += "\n"

        # チーム打撃
        batting = team_data.get('batting', {})
        output += f"**チーム打撃**:\n"
        output += f"AVG: .{batting.get('avg', '000')} | OPS: .{batting.get('ops', '000')} | "
        output += f"得点: {batting.get('runs', 0)} | 本塁打: {batting.get('home_runs', 0)}\n"
        
        # Phase1追加項目 - wOBAとxwOBA
        team_id = team_data.get('team_id')
        if team_id:
            woba_stats = self.enhanced_collector.get_team_woba_and_xwoba(team_id)
            output += f"wOBA: {woba_stats.get('woba', .320):.3f} | "
            output += f"xwOBA: {woba_stats.get('xwoba', .320):.3f}\n"

        # 対左右投手成績
        if team_id:
            splits = self.enhanced_collector.get_team_batting_splits(team_id)
            output += f"対左投手: {splits['vs_left_pitching']['avg']} (OPS {splits['vs_left_pitching']['ops']}) | "
            output += f"対右投手: {splits['vs_right_pitching']['avg']} (OPS {splits['vs_right_pitching']['ops']})\n"

        # 最近の成績
        recent = team_data.get('recent_ops', {})
        output += f"過去5試合OPS: {recent.get('last_5', 0.000):.3f} | "
        output += f"過去10試合OPS: {recent.get('last_10', 0.000):.3f}\n"

        return output


# テスト実行
if __name__ == "__main__":
    formatter = CompleteStatsFormatter()

    # テストデータ
    test_game = {
        'game_time': '06/23 00:35',
        'away_team': {
            'name': 'Baltimore Orioles',
            'team_id': 110,
            'pitcher_id': 665152,  # Dean Kremer
            'bullpen': {
                'era': 3.23,
                'fip': 3.48,
                'whip': 1.18,
                'reliever_count': 6,
                'closer_name': 'Félix Bautista'
            },
            'batting': {
                'avg': '239',
                'ops': '698',
                'runs': 302,
                'home_runs': 88
            },
            'recent_ops': {
                'last_5': 0.647,
                'last_10': 0.696
            }
        },
        'home_team': {
            'name': 'New York Yankees',
            'team_id': 147,
            'pitcher_id': 701542,  # Will Warren
            'bullpen': {
                'era': 3.36,
                'fip': 3.56,
                'whip': 1.14,
                'reliever_count': 8,
                'closer_name': None
            },
            'batting': {
                'avg': '255',
                'ops': '791',
                'runs': 391,
                'home_runs': 118
            },
            'recent_ops': {
                'last_5': 0.812,
                'last_10': 0.637
            }
        }
    }

    print(formatter.format_game_stats(test_game))