from typing import Dict
from scripts.enhanced_stats_collector import EnhancedStatsCollector
from scripts.calculate_gb_fb_stats import GBFBCalculator

class CompleteStatsFormatter:
    """完全な統計情報をフォーマット"""
    
    def __init__(self):
        self.enhanced_collector = EnhancedStatsCollector()
        self.gb_fb_calculator = GBFBCalculator()
    
    def format_team_section(self, team_name: str, team_id: int, pitcher_id: int, 
                           pitcher_name: str, bullpen_data: Dict, 
                           team_batting: Dict, recent_ops: Dict) -> str:
        """チームセクションの完全フォーマット"""
        
        # 投手の拡張統計を取得
        pitcher_stats = self.enhanced_collector.get_pitcher_enhanced_stats(pitcher_id)
        pitcher_stats['name'] = pitcher_name  # 名前を設定
        
        # GB%/FB%を取得（APIになければ計算）
        if pitcher_stats['gb_percent'] == 0.0 and pitcher_stats['fb_percent'] == 0.0:
            gb, fb = self.gb_fb_calculator.calculate_pitcher_gb_fb(pitcher_id, limit_games=3)
            pitcher_stats['gb_percent'] = gb
            pitcher_stats['fb_percent'] = fb
        
        # チームの対左右投手成績を取得
        team_vs_stats = self.enhanced_collector.get_team_vs_pitching_stats(team_id)
        
        # 中継ぎ陣の拡張統計を取得（簡易版を使用）
        bullpen_enhanced = {
            'gb_percent': 0.0,  # 実装の複雑さのため省略
            'fb_percent': 0.0,
            'vs_left_avg': '.000',
            'vs_right_avg': '.000'
        }
        
        # フォーマット開始
        output = f"**【{team_name}】**\n"
        
        # 先発投手
        if pitcher_id:
            output += f"**先発**: {pitcher_stats['name']} ({pitcher_stats['wins']}勝{pitcher_stats['losses']}敗)\n"
            output += f"ERA: {pitcher_stats['era']:.2f} | FIP: {pitcher_stats['fip']:.2f} | "
            output += f"WHIP: {pitcher_stats['whip']:.2f} | K-BB%: {pitcher_stats['k_bb_percent']:.1f}% | "
            output += f"GB%: {pitcher_stats['gb_percent']:.1f}% | FB%: {pitcher_stats['fb_percent']:.1f}%\n"
            output += f"対左: {pitcher_stats['vs_left']['avg']} (OPS {pitcher_stats['vs_left']['ops']}) | "
            output += f"対右: {pitcher_stats['vs_right']['avg']} (OPS {pitcher_stats['vs_right']['ops']})\n"
        else:
            output += "**先発**: TBA\n"
        
        # 中継ぎ陣
        output += f"**中継ぎ陣** ({bullpen_data.get('reliever_count', 0)}名):\n"
        output += f"ERA: {bullpen_data.get('era', 0.00):.2f} | "
        output += f"FIP: {bullpen_data.get('fip', 0.00):.2f} | "
        output += f"WHIP: {bullpen_data.get('whip', 0.00):.2f}"
        
        # 中継ぎ陣のGB%/FB%（データがある場合のみ）
        if bullpen_enhanced['gb_percent'] > 0:
            output += f" | GB%: {bullpen_enhanced['gb_percent']:.1f}% | FB%: {bullpen_enhanced['fb_percent']:.1f}%"
        
        output += "\n"
        
        # 中継ぎ陣の対左右（データがある場合のみ）
        if bullpen_enhanced['vs_left_avg'] != '.000':
            output += f"対左: {bullpen_enhanced['vs_left_avg']} | 対右: {bullpen_enhanced['vs_right_avg']}\n"
        
        # クローザー
        if bullpen_data.get('closer_name'):
            output += f"CL: {bullpen_data['closer_name']}\n"
        
        # チーム打撃
        output += "**チーム打撃**:\n"
        output += f"AVG: .{team_batting.get('batting_avg', '000')} | "
        output += f"OPS: .{team_batting.get('ops', '000')} | "
        output += f"得点: {team_batting.get('runs', 0)} | "
        output += f"本塁打: {team_batting.get('home_runs', 0)}\n"
        
        # 対左右投手成績
        output += f"対左投手: {team_vs_stats['vs_lhp']['avg']} (OPS {team_vs_stats['vs_lhp']['ops']}) | "
        output += f"対右投手: {team_vs_stats['vs_rhp']['avg']} (OPS {team_vs_stats['vs_rhp']['ops']})\n"
        
        # 最近のOPS
        output += f"過去5試合OPS: {recent_ops.get('last_5_ops', 0.000):.3f} | "
        output += f"過去10試合OPS: {recent_ops.get('last_10_ops', 0.000):.3f}"
        
        return output
    
    def format_game_report(self, away_data: Dict, home_data: Dict, game_info: Dict) -> str:
        """試合レポート全体をフォーマット"""
        output = f"**{away_data['team_name']} @ {home_data['team_name']}**\n"
        output += f"開始時刻: {game_info['start_time']} (日本時間)\n"
        output += "=" * 50 + "\n"
        
        # Awayチーム
        output += self.format_team_section(
            away_data['team_name'],
            away_data['team_id'],
            away_data.get('pitcher_id'),
            away_data.get('pitcher_name', 'TBA'),
            away_data.get('bullpen', {}),
            away_data.get('batting', {}),
            away_data.get('recent_ops', {})
        )
        
        output += "\n"
        
        # Homeチーム
        output += self.format_team_section(
            home_data['team_name'],
            home_data['team_id'],
            home_data.get('pitcher_id'),
            home_data.get('pitcher_name', 'TBA'),
            home_data.get('bullpen', {}),
            home_data.get('batting', {}),
            home_data.get('recent_ops', {})
        )
        
        output += "\n" + "=" * 50
        
        return output


# テスト実行
if __name__ == "__main__":
    formatter = CompleteStatsFormatter()
    
    # テストデータ
    away_data = {
        'team_name': 'Baltimore Orioles',
        'team_id': 110,
        'pitcher_id': 665152,
        'pitcher_name': 'Dean Kremer',
        'bullpen': {
            'era': 3.23,
            'fip': 3.48,
            'whip': 1.18,
            'reliever_count': 6,
            'closer_name': 'Félix Bautista'
        },
        'batting': {
            'batting_avg': '239',
            'ops': '698',
            'runs': 302,
            'home_runs': 88
        },
        'recent_ops': {
            'last_5_ops': 0.647,
            'last_10_ops': 0.696
        }
    }
    
    home_data = {
        'team_name': 'New York Yankees',
        'team_id': 147,
        'pitcher_id': 701542,
        'pitcher_name': 'Will Warren',
        'bullpen': {
            'era': 3.36,
            'fip': 3.56,
            'whip': 1.14,
            'reliever_count': 8
        },
        'batting': {
            'batting_avg': '255',
            'ops': '791',
            'runs': 391,
            'home_runs': 118
        },
        'recent_ops': {
            'last_5_ops': 0.812,
            'last_10_ops': 0.637
        }
    }
    
    game_info = {
        'start_time': '06/23 00:35'
    }
    
    print("完全フォーマットのテスト:")
    print(formatter.format_game_report(away_data, home_data, game_info))