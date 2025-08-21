#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB HTMLレポート生成システム
既存のMLBデータからA4サイズ1ページ/1試合のHTMLレポートを生成
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# MLBチーム情報（ロゴURL用）
TEAM_INFO = {
    # American League
    "Yankees": {"abbr": "nyy", "full": "New York Yankees"},
    "Red Sox": {"abbr": "bos", "full": "Boston Red Sox"},
    "Blue Jays": {"abbr": "tor", "full": "Toronto Blue Jays"},
    "Rays": {"abbr": "tb", "full": "Tampa Bay Rays"},
    "Orioles": {"abbr": "bal", "full": "Baltimore Orioles"},
    "White Sox": {"abbr": "cws", "full": "Chicago White Sox"},
    "Guardians": {"abbr": "cle", "full": "Cleveland Guardians"},
    "Tigers": {"abbr": "det", "full": "Detroit Tigers"},
    "Royals": {"abbr": "kc", "full": "Kansas City Royals"},
    "Twins": {"abbr": "min", "full": "Minnesota Twins"},
    "Astros": {"abbr": "hou", "full": "Houston Astros"},
    "Athletics": {"abbr": "oak", "full": "Oakland Athletics"},
    "Angels": {"abbr": "laa", "full": "Los Angeles Angels"},
    "Mariners": {"abbr": "sea", "full": "Seattle Mariners"},
    "Rangers": {"abbr": "tex", "full": "Texas Rangers"},
    
    # National League
    "Braves": {"abbr": "atl", "full": "Atlanta Braves"},
    "Marlins": {"abbr": "mia", "full": "Miami Marlins"},
    "Mets": {"abbr": "nym", "full": "New York Mets"},
    "Phillies": {"abbr": "phi", "full": "Philadelphia Phillies"},
    "Nationals": {"abbr": "wsh", "full": "Washington Nationals"},
    "Cubs": {"abbr": "chc", "full": "Chicago Cubs"},
    "Reds": {"abbr": "cin", "full": "Cincinnati Reds"},
    "Brewers": {"abbr": "mil", "full": "Milwaukee Brewers"},
    "Pirates": {"abbr": "pit", "full": "Pittsburgh Pirates"},
    "Cardinals": {"abbr": "stl", "full": "St. Louis Cardinals"},
    "Diamondbacks": {"abbr": "ari", "full": "Arizona Diamondbacks"},
    "Rockies": {"abbr": "col", "full": "Colorado Rockies"},
    "Dodgers": {"abbr": "lad", "full": "Los Angeles Dodgers"},
    "Padres": {"abbr": "sd", "full": "San Diego Padres"},
    "Giants": {"abbr": "sf", "full": "San Francisco Giants"}
}

class MLBHTMLReportGenerator:
    def __init__(self):
        self.games_data = []
        self.report_date = datetime.now()
        
    def parse_text_report(self, text_content):
        """
        テキストレポートをパースして構造化データに変換
        """
        games = []
        
        # 試合ブロックを抽出
        game_pattern = r'\*\*([\w\s]+)\s*@\s*([\w\s]+)\*\*'
        game_blocks = re.split(r'={50,}', text_content)
        
        for block in game_blocks:
            if '**' not in block:
                continue
                
            match = re.search(game_pattern, block)
            if not match:
                continue
                
            game = {
                'away_team': match.group(1).strip(),
                'home_team': match.group(2).strip(),
                'game_time': self._extract_game_time(block),
                'away_pitcher': self._extract_pitcher_info(block, 'away'),
                'home_pitcher': self._extract_pitcher_info(block, 'home'),
                'away_bullpen': self._extract_bullpen_info(block, 'away'),
                'home_bullpen': self._extract_bullpen_info(block, 'home'),
                'away_batting': self._extract_batting_info(block, 'away'),
                'home_batting': self._extract_batting_info(block, 'home'),
                'summary': self._generate_summary(block)
            }
            games.append(game)
            
        return games
    
    def _extract_game_time(self, block):
        """試合時間を抽出"""
        time_match = re.search(r'(\d{2}/\d{2}\s+\d{2}:\d{2})', block)
        if time_match:
            return time_match.group(1)
        return "00:00"
    
    def _extract_pitcher_info(self, block, side):
        """投手情報を抽出"""
        pitcher_info = {
            'name': '未定',
            'record': '0勝0敗',
            'hand': 'R',  # デフォルト右
            'era': '0.00',
            'fip': '0.00',
            'xfip': '0.00',
            'whip': '0.00',
            'k_bb': '0.0%',
            'qs_rate': '0.0%',
            'gb_rate': '0.0%',
            'swstr': '0.0%',
            'babip': '0.000',
            'vs_left': '.000/.000',
            'vs_right': '.000/.000'
        }
        
        # 実際のデータから抽出するロジックをここに実装
        # 簡易版として、パターンマッチングで取得
        
        return pitcher_info
    
    def _extract_bullpen_info(self, block, side):
        """ブルペン情報を抽出"""
        return {
            'count': '8',
            'era': '3.50',
            'fip': '3.50',
            'xfip': '3.00',
            'whip': '1.20',
            'k_bb': '15.0%',
            'fatigue': '主力5名が連投中'
        }
    
    def _extract_batting_info(self, block, side):
        """打撃情報を抽出"""
        return {
            'avg': '.250',
            'ops': '.750',
            'woba': '.320',
            'xwoba': '.315',
            'ops_10games': '.780'
        }
    
    def _generate_summary(self, block):
        """総括を生成"""
        # 既存の総括を抽出するか、新規生成
        return "投手力と打線の調子を総合的に判断した予想をここに記載"
    
    def generate_html(self, games_data=None):
        """
        HTMLレポートを生成
        """
        if games_data:
            self.games_data = games_data
            
        html_content = self._get_html_header()
        
        for game in self.games_data:
            html_content += self._generate_game_page(game)
            
        html_content += self._get_html_footer()
        
        return html_content
    
    def _get_html_header(self):
        """HTMLヘッダー"""
        return """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB試合予想レポート - 日本時間 {date} の試合</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Roboto+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Noto Sans JP', sans-serif;
            background-color: #f3f4f6;
        }}
        .game-page {{
            width: 210mm;
            min-height: 297mm;
            padding: 15mm;
            margin: 10mm auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }}
        .data-font {{
            font-family: 'Roboto Mono', monospace;
        }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #1e3a8a;
            border-bottom: 2px solid #93c5fd;
            padding-bottom: 0.25rem;
            margin-bottom: 1rem;
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e5e7eb;
            font-size: 0.9rem;
        }}
        .stat-item .label {{
            color: #4b5563;
        }}
        .stat-item .value {{
            font-weight: 700;
            color: #111827;
        }}
        .handedness-rhp {{
            background-color: #ef4444;
            color: white;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
        }}
        .handedness-lhp {{
            background-color: #3b82f6;
            color: white;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
        }}
        @media print {{
            .game-page {{
                margin: 0;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body class="bg-gray-200">
""".format(date=self.report_date.strftime('%Y/%m/%d'))
    
    def _generate_game_page(self, game):
        """1試合分のページを生成"""
        away_team_abbr = TEAM_INFO.get(game['away_team'], {}).get('abbr', 'mlb')
        home_team_abbr = TEAM_INFO.get(game['home_team'], {}).get('abbr', 'mlb')
        
        # ESPNのロゴURLを使用（MLB公式APIに変更可能）
        away_logo = f"https://a.espncdn.com/i/teamlogos/mlb/500/{away_team_abbr}.png"
        home_logo = f"https://a.espncdn.com/i/teamlogos/mlb/500/{home_team_abbr}.png"
        
        return f"""
    <div class="game-page">
        <header class="flex justify-between items-center pb-4 border-b-2 border-gray-300">
            <div class="team-info text-center w-1/3">
                <img src="{away_logo}" alt="{game['away_team']} Logo" class="w-12 h-12 mx-auto mb-2">
                <h1 class="text-3xl font-black">{game['away_team']}</h1>
                <p class="text-lg font-bold">{game['away_pitcher']['name']} 
                    <span class="handedness-{'lhp' if game['away_pitcher']['hand'] == 'L' else 'rhp'}">
                        {'左' if game['away_pitcher']['hand'] == 'L' else '右'}
                    </span>
                </p>
                <p class="text-gray-600 data-font">{game['away_pitcher']['record']}</p>
            </div>
            <div class="game-time text-center w-1/3">
                <p class="text-sm text-gray-500">日本時間</p>
                <p class="text-4xl font-bold">{game['game_time']}</p>
                <p class="text-lg font-bold">試合開始</p>
            </div>
            <div class="team-info text-center w-1/3">
                <img src="{home_logo}" alt="{game['home_team']} Logo" class="w-12 h-12 mx-auto mb-2">
                <h1 class="text-3xl font-black">{game['home_team']}</h1>
                <p class="text-lg font-bold">{game['home_pitcher']['name']}
                    <span class="handedness-{'lhp' if game['home_pitcher']['hand'] == 'L' else 'rhp'}">
                        {'左' if game['home_pitcher']['hand'] == 'L' else '右'}
                    </span>
                </p>
                <p class="text-gray-600 data-font">{game['home_pitcher']['record']}</p>
            </div>
        </header>
        
        <main class="flex-grow mt-6 grid grid-cols-2 gap-8">
            <!-- Away Team Stats -->
            <div class="team-stats">
                <section class="mb-6">
                    <h2 class="section-title">先発投手: {game['away_pitcher']['name']}</h2>
                    <div class="stat-item">
                        <span class="label">ERA/FIP/xFIP</span>
                        <span class="value data-font">{game['away_pitcher']['era']}/{game['away_pitcher']['fip']}/{game['away_pitcher']['xfip']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">WHIP/K-BB%</span>
                        <span class="value data-font">{game['away_pitcher']['whip']}/{game['away_pitcher']['k_bb']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">QS率/GB%</span>
                        <span class="value data-font">{game['away_pitcher']['qs_rate']}/{game['away_pitcher']['gb_rate']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">SwStr%/BABIP</span>
                        <span class="value data-font">{game['away_pitcher']['swstr']}/{game['away_pitcher']['babip']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">対左/右 OPS</span>
                        <span class="value data-font">{game['away_pitcher']['vs_left']}/{game['away_pitcher']['vs_right']}</span>
                    </div>
                </section>
                
                <section class="mb-6">
                    <h2 class="section-title">中継ぎ陣 ({game['away_bullpen']['count']}名)</h2>
                    <div class="stat-item">
                        <span class="label">ERA/FIP/xFIP</span>
                        <span class="value data-font">{game['away_bullpen']['era']}/{game['away_bullpen']['fip']}/{game['away_bullpen']['xfip']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">WHIP/K-BB%</span>
                        <span class="value data-font">{game['away_bullpen']['whip']}/{game['away_bullpen']['k_bb']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">疲労度</span>
                        <span class="value">{game['away_bullpen']['fatigue']}</span>
                    </div>
                </section>
                
                <section>
                    <h2 class="section-title">攻撃 (vs {'RHP' if game['home_pitcher']['hand'] == 'R' else 'LHP'})</h2>
                    <div class="stat-item">
                        <span class="label">AVG/OPS</span>
                        <span class="value data-font">{game['away_batting']['avg']}/{game['away_batting']['ops']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">wOBA/xwOBA</span>
                        <span class="value data-font">{game['away_batting']['woba']}/{game['away_batting']['xwoba']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">過去10試合 OPS</span>
                        <span class="value data-font text-{'red' if float(game['away_batting']['ops_10games'][1:]) > .800 else 'blue'}-600 font-bold">
                            {game['away_batting']['ops_10games']}
                        </span>
                    </div>
                </section>
            </div>
            
            <!-- Home Team Stats -->
            <div class="team-stats">
                <section class="mb-6">
                    <h2 class="section-title">先発投手: {game['home_pitcher']['name']}</h2>
                    <div class="stat-item">
                        <span class="label">ERA/FIP/xFIP</span>
                        <span class="value data-font">{game['home_pitcher']['era']}/{game['home_pitcher']['fip']}/{game['home_pitcher']['xfip']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">WHIP/K-BB%</span>
                        <span class="value data-font">{game['home_pitcher']['whip']}/{game['home_pitcher']['k_bb']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">QS率/GB%</span>
                        <span class="value data-font">{game['home_pitcher']['qs_rate']}/{game['home_pitcher']['gb_rate']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">SwStr%/BABIP</span>
                        <span class="value data-font">{game['home_pitcher']['swstr']}/{game['home_pitcher']['babip']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">対左/右 OPS</span>
                        <span class="value data-font">{game['home_pitcher']['vs_left']}/{game['home_pitcher']['vs_right']}</span>
                    </div>
                </section>
                
                <section class="mb-6">
                    <h2 class="section-title">中継ぎ陣 ({game['home_bullpen']['count']}名)</h2>
                    <div class="stat-item">
                        <span class="label">ERA/FIP/xFIP</span>
                        <span class="value data-font">{game['home_bullpen']['era']}/{game['home_bullpen']['fip']}/{game['home_bullpen']['xfip']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">WHIP/K-BB%</span>
                        <span class="value data-font">{game['home_bullpen']['whip']}/{game['home_bullpen']['k_bb']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">疲労度</span>
                        <span class="value">{game['home_bullpen']['fatigue']}</span>
                    </div>
                </section>
                
                <section>
                    <h2 class="section-title">攻撃 (vs {'RHP' if game['away_pitcher']['hand'] == 'R' else 'LHP'})</h2>
                    <div class="stat-item">
                        <span class="label">AVG/OPS</span>
                        <span class="value data-font">{game['home_batting']['avg']}/{game['home_batting']['ops']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">wOBA/xwOBA</span>
                        <span class="value data-font">{game['home_batting']['woba']}/{game['home_batting']['xwoba']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="label">過去10試合 OPS</span>
                        <span class="value data-font text-{'red' if float(game['home_batting']['ops_10games'][1:]) > .800 else 'blue'}-600 font-bold">
                            {game['home_batting']['ops_10games']}
                        </span>
                    </div>
                </section>
            </div>
        </main>
        
        <footer class="mt-auto pt-4 border-t-4 border-black">
            <h3 class="text-xl font-bold mb-2">総括</h3>
            <p class="text-base leading-relaxed">{game['summary']}</p>
        </footer>
    </div>
"""
    
    def _get_html_footer(self):
        """HTMLフッター"""
        return """
</body>
</html>
"""
    
    def save_html(self, html_content, output_path):
        """HTMLファイルを保存"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ HTMLレポートを保存しました: {output_path}")


def main():
    """
    メイン実行関数
    """
    # 既存のテキストレポートを読み込む
    text_report_path = "daily_reports/mlb_report_20241225.txt"  # 実際のパスに変更
    
    generator = MLBHTMLReportGenerator()
    
    # テスト用のダミーデータ（実際はテキストレポートから抽出）
    test_games = [
        {
            'away_team': 'Yankees',
            'home_team': 'Red Sox',
            'game_time': '08/21 08:00',
            'away_pitcher': {
                'name': 'Gerrit Cole',
                'record': '12勝4敗',
                'hand': 'R',
                'era': '2.81',
                'fip': '2.95',
                'xfip': '3.12',
                'whip': '0.98',
                'k_bb': '24.5%',
                'qs_rate': '65.2%',
                'gb_rate': '45.3%',
                'swstr': '28.5%',
                'babip': '0.285',
                'vs_left': '.612',
                'vs_right': '.585'
            },
            'home_pitcher': {
                'name': 'Chris Sale',
                'record': '10勝6敗',
                'hand': 'L',
                'era': '3.42',
                'fip': '3.55',
                'xfip': '3.68',
                'whip': '1.12',
                'k_bb': '22.1%',
                'qs_rate': '58.3%',
                'gb_rate': '42.1%',
                'swstr': '26.2%',
                'babip': '0.298',
                'vs_left': '.542',
                'vs_right': '.698'
            },
            'away_bullpen': {
                'count': '8',
                'era': '3.45',
                'fip': '3.52',
                'xfip': '3.38',
                'whip': '1.18',
                'k_bb': '18.5%',
                'fatigue': '主力5名が連投中'
            },
            'home_bullpen': {
                'count': '7',
                'era': '3.89',
                'fip': '3.95',
                'xfip': '3.72',
                'whip': '1.25',
                'k_bb': '16.2%',
                'fatigue': '主力3名が連投中'
            },
            'away_batting': {
                'avg': '.268',
                'ops': '.812',
                'woba': '.345',
                'xwoba': '.338',
                'ops_10games': '.845'
            },
            'home_batting': {
                'avg': '.255',
                'ops': '.765',
                'woba': '.325',
                'xwoba': '.318',
                'ops_10games': '.712'
            },
            'summary': 'ヤンキースが投手力で優位。先発のColeはxFIP 3.12と安定しており、Sale（xFIP 3.68）を上回る。ブルペンも僅差でヤンキースが優位。打線は直近10試合でヤンキースがOPS .845と好調。総合的にヤンキースが有利と予想。'
        }
    ]
    
    # HTML生成
    html_content = generator.generate_html(test_games)
    
    # 保存
    output_path = f"daily_reports/html/mlb_report_{datetime.now().strftime('%Y%m%d')}.html"
    generator.save_html(html_content, output_path)
    
    print("\n📊 レポート生成完了！")
    print(f"ブラウザで確認: start {output_path}")


if __name__ == "__main__":
    main()