"""
MLB対戦データ可視化スクリプト
対戦分析結果をグラフで表示
"""
import json
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from scripts.matchup_analyzer import MatchupAnalyzer
import pandas as pd


class MatchupVisualizer:
    def __init__(self):
        self.analyzer = MatchupAnalyzer()
        self.setup_plot_style()
        
    def setup_plot_style(self):
        """グラフのスタイル設定"""
        plt.style.use('seaborn-v0_8-darkgrid')
        # 日本語フォント設定（Windows）
        plt.rcParams['font.family'] = 'MS Gothic'
        plt.rcParams['axes.unicode_minus'] = False
        
    def create_pitching_comparison(self, team1_data, team2_data):
        """投手陣比較グラフ"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # チーム名
        team1_name = team1_data['teamName']
        team2_name = team2_data['teamName']
        
        # 先発投手データ
        pitching1 = team1_data['pitching']
        pitching2 = team2_data['pitching']
        
        # 先発投手の平均成績
        def get_starters_avg(starters):
            if not starters:
                return {'era': 0, 'fip': 0, 'whip': 0}
            total = len(starters)
            return {
                'era': sum(float(s.get('era', 0)) for s in starters) / total,
                'fip': sum(s.get('fip', 0) for s in starters) / total,
                'whip': sum(float(s.get('whip', 0)) for s in starters) / total
            }
        
        starters1 = get_starters_avg(pitching1['starters'])
        starters2 = get_starters_avg(pitching2['starters'])
        
        # グラフ1: 先発投手比較
        categories = ['ERA', 'FIP', 'WHIP']
        team1_values = [starters1['era'], starters1['fip'], starters1['whip']]
        team2_values = [starters2['era'], starters2['fip'], starters2['whip']]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, team1_values, width, label=team1_name, color='#003087')
        bars2 = ax1.bar(x + width/2, team2_values, width, label=team2_name, color='#BD3039')
        
        ax1.set_xlabel('指標')
        ax1.set_ylabel('値（低い方が良い）')
        ax1.set_title('先発投手陣比較')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        
        # 値をバーの上に表示
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        # グラフ2: 中継ぎ比較
        bullpen1 = pitching1['bullpenAggregate']
        bullpen2 = pitching2['bullpenAggregate']
        
        categories2 = ['ERA', 'WHIP']
        team1_bullpen = [bullpen1.get('era', 0), bullpen1.get('whip', 0)]
        team2_bullpen = [bullpen2.get('era', 0), bullpen2.get('whip', 0)]
        
        x2 = np.arange(len(categories2))
        
        bars3 = ax2.bar(x2 - width/2, team1_bullpen, width, label=team1_name, color='#003087')
        bars4 = ax2.bar(x2 + width/2, team2_bullpen, width, label=team2_name, color='#BD3039')
        
        ax2.set_xlabel('指標')
        ax2.set_ylabel('値（低い方が良い）')
        ax2.set_title('中継ぎ陣比較')
        ax2.set_xticks(x2)
        ax2.set_xticklabels(categories2)
        ax2.legend()
        
        # 値をバーの上に表示
        for bars in [bars3, bars4]:
            for bar in bars:
                height = bar.get_height()
                ax2.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        plt.tight_layout()
        return fig
        
    def create_batting_comparison(self, team1_data, team2_data):
        """打撃陣比較グラフ"""
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # データ取得
        batting1 = team1_data['batting']
        batting2 = team2_data['batting']
        team1_name = team1_data['teamName']
        team2_name = team2_data['teamName']
        
        # レーダーチャート用データ
        categories = ['打率', 'OPS', '得点', '打点']
        
        # 正規化のための最大値
        max_values = {
            '打率': 0.300,
            'OPS': 0.900,
            '得点': 1000,
            '打点': 1000
        }
        
        # データの正規化（0-1の範囲に）
        team1_values = [
            float(batting1.get('avg', 0)) / max_values['打率'],
            float(batting1.get('ops', 0)) / max_values['OPS'],
            batting1.get('runs', 0) / max_values['得点'],
            batting1.get('rbi', 0) / max_values['打点']
        ]
        
        team2_values = [
            float(batting2.get('avg', 0)) / max_values['打率'],
            float(batting2.get('ops', 0)) / max_values['OPS'],
            batting2.get('runs', 0) / max_values['得点'],
            batting2.get('rbi', 0) / max_values['打点']
        ]
        
        # レーダーチャート作成
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
        
        # 閉じるために最初の値を最後に追加
        team1_values = team1_values + [team1_values[0]]
        team2_values = team2_values + [team2_values[0]]
        angles = np.concatenate([angles, [angles[0]]])
        
        ax = plt.subplot(111, projection='polar')
        
        # プロット
        ax.plot(angles, team1_values, 'o-', linewidth=2, label=team1_name, color='#003087')
        ax.fill(angles, team1_values, alpha=0.25, color='#003087')
        
        ax.plot(angles, team2_values, 'o-', linewidth=2, label=team2_name, color='#BD3039')
        ax.fill(angles, team2_values, alpha=0.25, color='#BD3039')
        
        # 軸の設定
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        
        # グリッド線
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'])
        
        plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
        plt.title('打撃陣比較（レーダーチャート）', pad=20)
        
        return fig
        
    def create_overall_comparison(self, matchup_result):
        """総合評価グラフ"""
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        
        teams = list(matchup_result['pitching'].columns[1:3])
        points = [matchup_result['team1_points'], matchup_result['team2_points']]
        
        colors = ['#003087', '#BD3039']
        bars = ax.bar(teams, points, color=colors, width=0.6)
        
        # 値をバーの上に表示
        for bar, point in zip(bars, points):
            height = bar.get_height()
            ax.annotate(f'{point}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=16, fontweight='bold')
        
        ax.set_ylabel('ポイント', fontsize=12)
        ax.set_title('総合評価ポイント', fontsize=16, fontweight='bold')
        ax.set_ylim(0, max(points) + 2)
        
        # 勝者を強調
        if points[0] > points[1]:
            ax.text(0.5, 0.95, f'予想: {teams[0]}優位', 
                   transform=ax.transAxes, ha='center', fontsize=14,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        elif points[1] > points[0]:
            ax.text(0.5, 0.95, f'予想: {teams[1]}優位', 
                   transform=ax.transAxes, ha='center', fontsize=14,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        else:
            ax.text(0.5, 0.95, '予想: 互角の戦い', 
                   transform=ax.transAxes, ha='center', fontsize=14,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        return fig
        
    def visualize_matchup(self, team1_id: int, team2_id: int, season: int = 2024):
        """対戦分析の可視化メイン関数"""
        print("\n📊 対戦データ可視化中...")
        
        # データ取得
        team1_data = self.analyzer.load_team_data(team1_id, season)
        team2_data = self.analyzer.load_team_data(team2_id, season)
        
        # 分析実行
        result = self.analyzer.generate_matchup_report(team1_id, team2_id, season)
        
        # グラフ作成
        print("\n🎨 グラフ生成中...")
        
        # 1. 投手陣比較
        fig1 = self.create_pitching_comparison(team1_data, team2_data)
        fig1.savefig(f'data/processed/pitching_comparison_{team1_id}_vs_{team2_id}.png', 
                     dpi=300, bbox_inches='tight')
        
        # 2. 打撃陣比較
        fig2 = self.create_batting_comparison(team1_data, team2_data)
        fig2.savefig(f'data/processed/batting_comparison_{team1_id}_vs_{team2_id}.png', 
                     dpi=300, bbox_inches='tight')
        
        # 3. 総合評価
        fig3 = self.create_overall_comparison(result)
        fig3.savefig(f'data/processed/overall_comparison_{team1_id}_vs_{team2_id}.png', 
                     dpi=300, bbox_inches='tight')
        
        # 表示
        plt.show()
        
        print(f"\n✅ グラフ保存完了:")
        print(f"  - 投手陣比較: data/processed/pitching_comparison_{team1_id}_vs_{team2_id}.png")
        print(f"  - 打撃陣比較: data/processed/batting_comparison_{team1_id}_vs_{team2_id}.png")
        print(f"  - 総合評価: data/processed/overall_comparison_{team1_id}_vs_{team2_id}.png")
        

def main():
    """メイン実行関数"""
    visualizer = MatchupVisualizer()
    
    print("\n🎨 MLB対戦データ可視化システム")
    print("=" * 60)
    
    # Yankees vs Red Sox を可視化
    visualizer.visualize_matchup(147, 111, 2024)
    
    print("\n💡 他のチームで可視化する場合:")
    print("visualizer.visualize_matchup(team1_id, team2_id, 2024)")
    

if __name__ == "__main__":
    main()