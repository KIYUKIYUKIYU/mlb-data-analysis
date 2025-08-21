#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB Report Visualizer
HTMLフォーマットの美しいレポートを生成
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from jinja2 import Template
import pandas as pd

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

class MLBReportVisualizer:
    def __init__(self, data_path=None):
        """
        初期化
        Args:
            data_path: レポートデータのパス
        """
        self.data_path = data_path
        self.report_data = {}
        self.charts = {}
        
    def load_report_data(self, json_path=None):
        """
        レポートデータを読み込む
        """
        if json_path and os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                self.report_data = json.load(f)
        else:
            # デモデータ（実際のデータ構造に合わせて調整）
            self.report_data = self._get_demo_data()
        return self.report_data
    
    def _get_demo_data(self):
        """デモデータ生成"""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "games": [
                {
                    "home_team": "Yankees",
                    "away_team": "Red Sox", 
                    "home_score": 5,
                    "away_score": 3,
                    "status": "Final",
                    "winning_pitcher": "Cole, G",
                    "losing_pitcher": "Pivetta, N",
                    "save_pitcher": "Chapman, A"
                }
            ],
            "team_stats": {
                "Yankees": {
                    "wins": 95,
                    "losses": 60,
                    "win_pct": .613,
                    "gb": "-",
                    "last_10": "7-3",
                    "streak": "W2"
                }
            },
            "player_stats": {
                "batters": [
                    {
                        "name": "Judge, A",
                        "team": "NYY",
                        "avg": .301,
                        "hr": 58,
                        "rbi": 144,
                        "ops": 1.011,
                        "war": 10.8
                    }
                ],
                "pitchers": [
                    {
                        "name": "Cole, G",
                        "team": "NYY",
                        "w": 15,
                        "l": 4,
                        "era": 2.81,
                        "so": 251,
                        "whip": 0.98
                    }
                ]
            }
        }
    
    def create_team_standings_chart(self, standings_data):
        """
        チーム順位表のチャート作成
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # データ準備（デモ用）
        teams = ['Yankees', 'Orioles', 'Blue Jays', 'Rays', 'Red Sox']
        wins = [95, 89, 85, 83, 78]
        
        # 横棒グラフ
        bars = ax.barh(teams, wins, color=['#003087', '#DF4601', '#134A8E', '#092C5C', '#BD3039'])
        ax.set_xlabel('Wins', fontsize=12)
        ax.set_title('AL East Standings', fontsize=14, fontweight='bold')
        ax.set_xlim(70, 100)
        
        # 勝利数をバーの端に表示
        for bar, win in zip(bars, wins):
            ax.text(win + 0.5, bar.get_y() + bar.get_height()/2, 
                   str(win), va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Base64エンコード
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{chart_base64}"
    
    def create_player_stats_chart(self, player_stats):
        """
        選手成績チャート作成
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 打者成績（ホームラン数）
        batters = ['Judge', 'Stanton', 'Torres', 'Rizzo', 'LeMahieu']
        hrs = [58, 31, 24, 22, 12]
        
        ax1.bar(batters, hrs, color='#003087', alpha=0.8)
        ax1.set_title('Home Run Leaders', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Home Runs', fontsize=12)
        ax1.set_ylim(0, max(hrs) * 1.1)
        
        for i, (batter, hr) in enumerate(zip(batters, hrs)):
            ax1.text(i, hr + 1, str(hr), ha='center', fontweight='bold')
        
        # 投手成績（ERA）
        pitchers = ['Cole', 'Cortes', 'Schmidt', 'Stroman', 'Gil']
        eras = [2.81, 3.77, 2.85, 3.95, 3.20]
        
        bars = ax2.bar(pitchers, eras, color='#C4CED4', alpha=0.8)
        ax2.set_title('ERA Leaders', fontsize=14, fontweight='bold')
        ax2.set_ylabel('ERA', fontsize=12)
        ax2.set_ylim(0, 5)
        
        # ERA値に応じて色を変更
        for bar, era in zip(bars, eras):
            if era < 3.00:
                bar.set_color('#4CAF50')  # 緑（優秀）
            elif era < 3.50:
                bar.set_color('#FFC107')  # 黄（良好）
            else:
                bar.set_color('#F44336')  # 赤（要改善）
        
        for i, (pitcher, era) in enumerate(zip(pitchers, eras)):
            ax2.text(i, era + 0.1, f'{era:.2f}', ha='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Base64エンコード
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{chart_base64}"
    
    def create_html_report(self, output_path=None):
        """
        HTMLレポート生成
        """
        # チャート生成
        self.charts['standings'] = self.create_team_standings_chart(self.report_data.get('team_stats', {}))
        self.charts['players'] = self.create_player_stats_chart(self.report_data.get('player_stats', {}))
        
        # HTMLテンプレート
        html_template = Template('''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB Daily Report - {{ date }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .date {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 40px;
            animation: fadeIn 0.8s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .section-title {
            font-size: 2em;
            color: #1e3c72;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .game-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .game-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        
        .game-teams {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .team-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #2a5298;
        }
        
        .score {
            font-size: 2em;
            font-weight: bold;
            color: #1e3c72;
        }
        
        .game-status {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .stats-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .stats-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .stats-table tr:hover {
            background-color: #f5f7fa;
        }
        
        .stats-table tr:last-child td {
            border-bottom: none;
        }
        
        .chart-container {
            margin: 30px 0;
            text-align: center;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .highlight {
            background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .footer {
            background: #2a5298;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .games-grid {
                grid-template-columns: 1fr;
            }
            
            .content {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚾ MLB Daily Report</h1>
            <div class="date">{{ date }}</div>
        </div>
        
        <div class="content">
            <!-- 試合結果セクション -->
            <div class="section">
                <h2 class="section-title">🏟️ Today's Games</h2>
                <div class="games-grid">
                    {% for game in games %}
                    <div class="game-card">
                        <div class="game-teams">
                            <div>
                                <div class="team-name">{{ game.away_team }}</div>
                                <div class="score">{{ game.away_score }}</div>
                            </div>
                            <div style="font-size: 1.5em; color: #999;">@</div>
                            <div>
                                <div class="team-name">{{ game.home_team }}</div>
                                <div class="score">{{ game.home_score }}</div>
                            </div>
                        </div>
                        <div class="game-status">
                            {{ game.status }}
                            {% if game.winning_pitcher %}
                            <br>W: {{ game.winning_pitcher }} | L: {{ game.losing_pitcher }}
                            {% if game.save_pitcher %}| S: {{ game.save_pitcher }}{% endif %}
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- 順位表チャート -->
            <div class="section">
                <h2 class="section-title">📊 Standings</h2>
                <div class="chart-container">
                    <img src="{{ charts.standings }}" alt="Team Standings">
                </div>
            </div>
            
            <!-- 選手成績チャート -->
            <div class="section">
                <h2 class="section-title">⭐ Player Statistics</h2>
                <div class="chart-container">
                    <img src="{{ charts.players }}" alt="Player Statistics">
                </div>
            </div>
            
            <!-- 打者成績テーブル -->
            <div class="section">
                <h2 class="section-title">🏏 Top Batters</h2>
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Player</th>
                            <th>Team</th>
                            <th>AVG</th>
                            <th>HR</th>
                            <th>RBI</th>
                            <th>OPS</th>
                            <th>WAR</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for batter in player_stats.batters[:10] %}
                        <tr>
                            <td><strong>{{ batter.name }}</strong></td>
                            <td>{{ batter.team }}</td>
                            <td>{{ "%.3f"|format(batter.avg) }}</td>
                            <td>{{ batter.hr }}</td>
                            <td>{{ batter.rbi }}</td>
                            <td>{{ "%.3f"|format(batter.ops) }}</td>
                            <td>{{ "%.1f"|format(batter.war) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- 投手成績テーブル -->
            <div class="section">
                <h2 class="section-title">🎯 Top Pitchers</h2>
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Player</th>
                            <th>Team</th>
                            <th>W-L</th>
                            <th>ERA</th>
                            <th>SO</th>
                            <th>WHIP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for pitcher in player_stats.pitchers[:10] %}
                        <tr>
                            <td><strong>{{ pitcher.name }}</strong></td>
                            <td>{{ pitcher.team }}</td>
                            <td>{{ pitcher.w }}-{{ pitcher.l }}</td>
                            <td>{{ "%.2f"|format(pitcher.era) }}</td>
                            <td>{{ pitcher.so }}</td>
                            <td>{{ "%.2f"|format(pitcher.whip) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated on {{ datetime.now().strftime("%Y-%m-%d %H:%M:%S") }} | MLB Report Automation System</p>
        </div>
    </div>
</body>
</html>
        ''')
        
        # HTMLレンダリング
        html_content = html_template.render(
            date=self.report_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            games=self.report_data.get('games', []),
            team_stats=self.report_data.get('team_stats', {}),
            player_stats=self.report_data.get('player_stats', {}),
            charts=self.charts,
            datetime=datetime
        )
        
        # ファイル保存
        if output_path is None:
            output_path = f"daily_reports/mlb_report_{datetime.now().strftime('%Y%m%d')}.html"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTMLレポートを生成しました: {output_path}")
        return output_path
    
    def create_pdf_report(self, html_path, pdf_path=None):
        """
        HTMLからPDFを生成（weasyprint使用）
        """
        try:
            import weasyprint
            
            if pdf_path is None:
                pdf_path = html_path.replace('.html', '.pdf')
            
            weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
            print(f"✅ PDFレポートを生成しました: {pdf_path}")
            return pdf_path
        except ImportError:
            print("⚠️ PDFエクスポートにはweasyprintが必要です: pip install weasyprint")
            return None


def main():
    """
    メイン実行関数
    """
    # レポート生成
    visualizer = MLBReportVisualizer()
    
    # データ読み込み（実際のJSONファイルパスを指定）
    # visualizer.load_report_data("daily_reports/mlb_data_20241225.json")
    visualizer.load_report_data()  # デモデータ使用
    
    # HTML生成
    html_path = visualizer.create_html_report()
    
    # PDF生成（オプション）
    # visualizer.create_pdf_report(html_path)
    
    print("\n📊 レポート生成完了！")
    print(f"📁 出力先: {html_path}")


if __name__ == "__main__":
    main()